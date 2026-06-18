# Se usarmos o Agg do Python, o Jupyter não consegue rodar. Por isso vamos
# usar o Agg do Tkinter para o .bat conseguir abrir
import matplotlib

matplotlib.use("TkAgg")

import numpy as np  # noqa: E402
import keyboard as kb  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def exp_seguro(x: float):
    """Função que impede que um valor saia de um certo intervalo, ela recebe:

    x: o expoente de uma conta"""
    # vamos capar os expoentes para não ter erro computacional
    return np.exp(np.clip(x, -50, 50))


def noise_P(n: float, sigma: float):
    """Essa função serve para adicionar um noise no calculo do P, para ficar
    mais realista.

    Entrada:

    n: tamanho do vetor de estado

    sigma: desvio padrão da distribuição aleatória"""
    # Gera um noise aleatório
    eta = np.random.normal(0, sigma, size=n)
    eta -= np.mean(eta)  # Força o np.sum(eta) a ser 0. Não alterando o P

    return eta


def normaliza_prob(P: np.array):
    """Função que normaliza um array unidimencional

    Entradas:

    P: vetor probabilidade a ser normalizado

    Saída:

    O vetor P normalizado
    """
    P = np.asarray(P, dtype=float)
    P = np.clip(P, 0, 1)
    s = np.sum(P)
    if s <= 1e-12:
        return np.ones_like(P) / len(P)
    return P / s


def k_Na(V: float):
    """Função que atualiza as constantes de equilibrio do canal de Na

    Recebe o potencial atual"""
    return [
        0.04 * exp_seguro(0.075 * (V + 65)),  # k1(ativação)
        2.5 * exp_seguro(-0.035 * (V + 65)),  # k-1(desativação)
        0.25 * exp_seguro(0.07 * (V + 65)),  # alfa(abertura)
        5 * exp_seguro(-0.03 * (V + 65)),  # beta(fechamento)
        1.8 * exp_seguro(0.03 * (V + 65)),  # k2(inativação)
        0.12 * exp_seguro(-0.025 * (V + 65)),  # k-2(recuperação)
        k_Na,
    ]


def k_K(V: float):
    """Função que atualiza as constantes de equilibrio do canal de K

    Recebe o potencial atual"""
    return [
        0.025 * exp_seguro(0.03 * (V + 65)),  # k1(ativação)
        0.25 * exp_seguro(-0.025 * (V + 65)),  # k-1(desativação)
        0.08 * exp_seguro(0.028 * (V + 65)),  # alfa(abertura)
        0.1 * exp_seguro(-0.02 * (V + 65)),  # beta(fechamento)
        k_K,
    ]


def k_Ca(V: float):
    """Função que atualiza as constantes de equilibrio do canal de Ca

    Recebe o potencial atual"""
    return [
        0.02 * exp_seguro(0.05 * (V + 65)),  # k1(ativação)
        0.2 * exp_seguro(-0.03 * (V + 65)),  # k-1(desativação)
        0.08 * exp_seguro(0.04 * (V + 65)),  # alfa(abertura)
        0.1 * exp_seguro(-0.02 * (V + 65)),  # beta(fechamento)
        k_Ca,
    ]


def k_L(V: float):
    """Função que atualiza as constantes de equilibrio do canal de L

    Recebe o potencial atual"""
    return [
        0.1,  # k1  (ativação)
        0.1,  # k-1 (desativação)
        1,  # beta  (abertura)
        1,  # alfa (fechamento)
        k_L,
        # O canal L é fixo (perdas naturais). Então não precisa mudar ele com V
        # To ligado que k_L é inutil >:(, mas eu preciso de um algoridmo genérico, não?
    ]


def dSyn_dt(s: float, tau: float):
    """Diferencial da conexão sináptica, modela o decaimento do estímulo

    Entrada:

    s: intensidade atual do estímulo

    tau: constante de decaimento
    """
    return -s / tau


def KCa_open(Ca_i: float):
    """Equação diferencial para achar a porcentagem de corrente de acumulo de cálcio

    Entrada:

    Ca_i: potencial acumulado do íon cálcio
    """
    Kd = 0.0005  # mM
    n = 4

    return (Ca_i**n) / (Ca_i**n + Kd**n)


def dV_dt(t: float, V: float, estados: dict, g: dict, C: float, Ir: float):
    """Calcula todas as correntes para achar a diferencial do potencial

    Entradas:

    t: tempo atual

    V: potencial atual

    estados: todos os vetores probabilidade de estado dos canais (dicionario)

    g: a condutância dos canais (dicionario)

    C: a capacitância da membrana

    Ir: corrente de estímulo"""
    # Como ela é grande, vamos separar em componentes
    comp1 = Ir / C  # Corrente de estímulo
    comp2 = -(g["L"][0] / C) * (V - g["L"][1])  # *estados["PL"][2] #Corrente de vazão
    comp3 = (
        -(g["Na"][0] / C) * (V - g["Na"][1]) * estados["PNa"][2]
    )  # Corrente de sódio
    comp4 = (
        -(g["K"][0] / C) * (V - g["K"][1]) * estados["PK"][2]
    )  # Corrente de potássio
    comp5 = (
        -(g["Ca"][0] / C) * (V - g["Ca"][1]) * estados["PCa"][2]
    )  # Corrente de cálcio
    comp6 = -(g["KCa"][0] / C) * (V - g["KCa"][1]) * KCa_open(estados["Ca_i"])
    # Corrente de acúmulo de cálcio (não coube na linha de cima T_T))
    # Corrente da sinapse Excitatoria
    comp7 = -(g["SynE"][0] / C) * (V - g["SynE"][1]) * estados["SynE"]
    # Corrente da sinapse Inibitória
    comp8 = -(g["SynI"][0] / C) * (V - g["SynI"][1]) * estados["SynI"]

    return comp1 + comp2 + comp3 + comp4 + comp5 + comp6 + comp7 + comp8, comp5


def dCa_dt(ICa: float, Ca_i: float):
    """Diferencial do acumulo de cálcio no neurônio

    Entrada:

    ICa: corrente no canal de cálcio

    Ca_i: potencial acumulado dos íons cálcio"""
    Ca_rest = 0.0001
    alpha = 5e-7
    beta = 0.05
    return -alpha * ICa - beta * (Ca_i - Ca_rest)


class Neuronio:
    """Objeto do neurônio para mexer nele"""

    def __init__(
        self,
        estado: dict,
        k: dict,
        lista_V: list,
        line: plt.figure,
        ax: plt.axes,
        lista_t: list,
        number: float,
        V0=-65,
    ):
        """O objeto de neurônio recebe as seguintes variaveis como padrão:

        estado: dicionario que guarda todos os vetores de probabilidade e o potencial

        k: dicionario de equilíbrio

        lista_V: lista dos potenciais para plotar os gráficos

        line: guarda qual a própria linha dentro dos vários gráficos

        number: qual o seu número (os neurônios são ordenados)
        """

        self.k = {"Na": k_Na, "K": k_K, "Ca": k_Ca, "L": k_L}
        self.estado = {
            "PNa": steady_state(Matriz_de_transicao("Na", self.k, V0)),
            "PK": steady_state(Matriz_de_transicao("K", self.k, V0)),
            "PCa": steady_state(Matriz_de_transicao("Ca", self.k, V0)),
            "PL": np.array([1, 0, 0], dtype=float),
            "V": V0,
            "Ca_i": 0.0001,
            "SynE": 0.0,
            "SynI": 0.0,
            "V_anterior": V0,
            "V_ant_anterior": 0,
            "spike": False,
            "V_pico": V0,
        }
        self.lista_V = atualização([], self.estado["V"])
        (self.line,) = ax.plot(lista_t, self.lista_V, label=f"V{number + 1}(t)")
        self.number = number


def steady_state(Q: np.array):
    """Cria um vetor estável para o equilíbrio

    Q: Matriz de transição característica desse vetor"""
    # Vamos definir o equilíbrio inicial
    A = Q.copy()
    A[-1, :] = 1
    b = np.zeros(Q.shape[0])
    b[-1] = 1
    return np.linalg.solve(A, b)


def Matriz_de_transicao(nome: str, k: dict, V: float):
    """Calcula a matriz de transição para realizar a cadeia de Markov

    Entrada:

    nome: qual o nome do íon que será gerada a matriz

    k: dicionário de constantes de equilíbrio

    V: potencial de membrana

    Saída:

    A matriz de transição do canal"""
    if nome != "Na":
        K = k[nome](V)
        # Cria a matriz de transição
        Q = np.array(
            [[-K[0], K[1], 0], [K[0], -(K[1] + K[2]), K[3]], [0, K[2], -K[3]]],
            dtype=float,
        )
    else:
        K = k[nome](V)
        # Cria a matriz de transição
        Q = np.array(
            [
                [-K[0], K[1], 0, K[5]],
                [K[0], -(K[1] + K[2]), K[3], 0],
                [0, K[2], -(K[3] + K[4]), 0],
                [0, 0, K[4], -K[5]],
            ],
            dtype=float,
        )

    return Q


def f(t: float, y: np.array, k: dict, g: dict, C: float, Ir: float, Noise: bool):
    """Calcula as diferenciais de cada parametro

    Entradas:

    t: tempo atual da iteração

    y: vetor que concatena todas as variáveis

    k: dicionário das constantes de equilíbrio

    g: dicionário das condutâncias de cada canal

    C: capacitância da membrana

    Ir: estímulo externo

    Saída:

    Um vetor de mesmo tamanho que o y, mas as entradas são as variações em cada uma das componentes"""
    # Tau das sinapses
    tau_E = 1.2
    tau_I = 10.0

    # Sigma dos noises dos canais
    sigma_Na = 0.01 * 5
    sigma_K = 0.006 * 5
    sigma_Ca = 0.004 * 5

    # Vetores estados de cada um
    PNa = y[0:4]
    PK = y[4:7]
    PCa = y[7:10]
    PL = y[10:13]
    V = y[13]
    Ca_i = y[14]
    SynE = y[-2]
    SynI = y[-1]

    # Calculando as diferenciais no tempo
    dPNa = Matriz_de_transicao("Na", k, V) @ PNa
    dPK = Matriz_de_transicao("K", k, V) @ PK
    dPCa = Matriz_de_transicao("Ca", k, V) @ PCa
    dPL = Matriz_de_transicao("L", k, V) @ PL
    dsE = dSyn_dt(SynE, tau_E)
    dsI = dSyn_dt(SynI, tau_I)

    if Noise:
        dPNa += noise_P(4, sigma_Na)
        dPK += noise_P(3, sigma_K)
        dPCa += noise_P(3, sigma_Ca)

    dV, ICa = dV_dt(
        t,
        V,
        {
            "PNa": PNa,
            "PK": PK,
            "PCa": PCa,
            "PL": PL,
            "Ca_i": Ca_i,
            "SynE": SynE,
            "SynI": SynI,
        },
        g,
        C,
        Ir,
    )

    dCa = dCa_dt(-ICa, Ca_i)

    # Produto de matriz
    return np.concatenate([dPNa, dPK, dPCa, dPL, [dV], [dCa], [dsE], [dsI]])


def RK4(t: float, y: list, dt: float, k: dict, g: dict, C: float, Ir: float):
    """Função que aplica o método de evolução RK4 em uma função

    Entradas:

    t: tempo atual da iteração

    y: vetor que junta todas as variáveis para evoluir

    dt: passo de evolução

    k: dicionário das constantes de equilíbrio

    g: dicionário das condutâncias de cada canal

    C: capacitância da membrana

    Ir: estímulo externo

    Saída:

    Novo estado evoluído de cada variável"""
    k1 = f(t, y, k, g, C, Ir, False)
    k2 = f(t + dt / 2, y + dt * k1 / 2, k, g, C, Ir, False)
    k3 = f(t + dt / 2, y + dt * k2 / 2, k, g, C, Ir, False)
    k4 = f(t + dt, y + dt * k3, k, g, C, Ir, True)

    return y + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)


def step_neuronio(estado: dict, Ir: float, dt: float, k: dict, g: dict, Cm: float):
    """Atualiza um neurônio individual

    Entradas:

    estado: dicionario com todas as variáveis para evoluírem

    Ir: estímulo externo

    dt: passo de evolução

    k: dicionário das constantes de equilíbrio

    g: dicionário das condutâncias de cada canal

    C: capacitância da membrana"""
    y = np.concatenate(
        [
            estado["PNa"],
            estado["PK"],
            estado["PCa"],
            estado["PL"],
            [estado["V"]],
            [estado["Ca_i"]],
            [estado["SynE"]],
            [estado["SynI"]],
        ]
    )

    y = RK4(0, y, dt, k, g, Cm, Ir)

    estado["PNa"] = normaliza_prob(y[0:4])
    estado["PK"] = normaliza_prob(y[4:7])
    estado["PCa"] = normaliza_prob(y[7:10])
    estado["PL"] = normaliza_prob(y[10:13])
    estado["V"] = y[13]
    estado["Ca_i"] = max(y[14], 0)
    estado["SynE"] = max(y[-2], 0)
    estado["SynI"] = max(y[-1], 0)

    estado["spike"] = (
        estado["V_ant_anterior"] < estado["V_anterior"] > estado["V"]
        and estado["V"] > 0
    )
    if estado["spike"]:
        estado["V_pico"] = max(estado.get("V_pico", -65), estado["V"])
    estado["V_ant_anterior"] = estado["V_anterior"]
    estado["V_anterior"] = estado["V"]


def atualização(lista: list, var: float, tipo: str = "Parcial"):
    """Atualiza a lista de valores para poupar memória, ele tem um modo total que não limita a lista

    Entrada:

    lista: lista a ser atualizada

    var: variável a ser inserida

    tipo: string que diz se o programa vai salvar a lista parcialmente ou totalmente

    Saída:

    Uma lista que pode estar limitada ou não a depender do tipo"""
    if tipo != "Total":
        if len(lista) == 500:
            lista.pop(0)
        lista.append(var)

        return lista
    else:
        lista.append(var)

        return lista


def get_extremo(neuronios: list, tipo: str):
    """Retorna um valor extremo de todas as listas de potencias

    Entrada:

    neuronios: a lista de neurônios a serem iterados

    tipo: string que diz se é desejado o minimo ou o máximo

    Saída:

    O maior ou menor valor de potencial entre os neurônios, a depender do tipo"""
    if tipo == "min":
        minimo = min(neuronios[0].lista_V)
        for n in neuronios:
            if min(n.lista_V) < minimo:
                minimo = min(n.lista_V)
        return minimo
    else:
        maximo = max(neuronios[0].lista_V)
        for n in neuronios:
            if max(n.lista_V) > maximo:
                maximo = max(n.lista_V)
        return maximo


def main():
    # Vou definir isso antes, porque os neuronios precisam
    lista_t = [0]
    fig, ax = plt.subplots()  # so me interessa o ax, ele é o meu objeto de grafico

    # Criando os neurônios
    neuronios = [Neuronio({}, {}, [], 0, ax, lista_t, i) for i in range(20)]

    # Definindo as conexões entre eles

    conexoes = [
        # Anel excitatório principal
        {"pre": 0, "pos": 1, "tipo": "E", "peso": 0.65},
        {"pre": 1, "pos": 2, "tipo": "E", "peso": 0.60},
        {"pre": 2, "pos": 3, "tipo": "E", "peso": 0.65},
        {"pre": 3, "pos": 4, "tipo": "E", "peso": 0.60},
        {"pre": 4, "pos": 5, "tipo": "E", "peso": 0.65},
        {"pre": 5, "pos": 6, "tipo": "E", "peso": 0.60},
        {"pre": 6, "pos": 7, "tipo": "E", "peso": 0.65},
        {"pre": 7, "pos": 8, "tipo": "E", "peso": 0.60},
        {"pre": 8, "pos": 9, "tipo": "E", "peso": 0.65},
        {"pre": 9, "pos": 10, "tipo": "E", "peso": 0.60},
        {"pre": 10, "pos": 11, "tipo": "E", "peso": 0.65},
        {"pre": 11, "pos": 12, "tipo": "E", "peso": 0.60},
        {"pre": 12, "pos": 13, "tipo": "E", "peso": 0.65},
        {"pre": 13, "pos": 14, "tipo": "E", "peso": 0.60},
        {"pre": 14, "pos": 15, "tipo": "E", "peso": 0.65},
        {"pre": 15, "pos": 16, "tipo": "E", "peso": 0.60},
        {"pre": 16, "pos": 17, "tipo": "E", "peso": 0.65},
        {"pre": 17, "pos": 18, "tipo": "E", "peso": 0.60},
        {"pre": 18, "pos": 19, "tipo": "E", "peso": 0.65},
        # Inibitórias
        {"pre": 5, "pos": 10, "tipo": "I", "peso": 0.35},
        {"pre": 10, "pos": 15, "tipo": "I", "peso": 0.35},
        {"pre": 15, "pos": 5, "tipo": "I", "peso": 0.35},
        {"pre": 3, "pos": 12, "tipo": "I", "peso": 0.3},
        {"pre": 8, "pos": 17, "tipo": "I", "peso": 0.3},
        # Conexões excitatórias aleatórias fracas
        {"pre": 0, "pos": 10, "tipo": "E", "peso": 0.15},
        {"pre": 2, "pos": 14, "tipo": "E", "peso": 0.12},
        {"pre": 4, "pos": 11, "tipo": "E", "peso": 0.10},
        {"pre": 7, "pos": 16, "tipo": "E", "peso": 0.18},
        {"pre": 9, "pos": 3, "tipo": "E", "peso": 0.12},
        {"pre": 12, "pos": 6, "tipo": "E", "peso": 0.14},
        {"pre": 14, "pos": 1, "tipo": "E", "peso": 0.13},
        {"pre": 18, "pos": 8, "tipo": "E", "peso": 0.11},
    ]

    # Variaveis globais
    t = 0
    dt = 0.005
    dt_render = 0.05
    n_sub = int(dt_render / dt)

    Imax = 20

    g = {
        "Na": [120, 50],  # mS/cm², mV
        "K": [36, -77],
        "Ca": [1, 120],
        "L": [0.3, -54.4],
        "KCa": [2.0, -77],
        "SynE": [1.5, 0.0],
        "SynI": [0.8, -75],
    }
    Cm = 1  # Capacitancia da membrana (microF/cm²)

    # V_rest=-65 #mV

    plt.ion()  # modo interativo

    ax.set_xlabel("tempo(ms)")
    ax.set_ylabel("potenciais(mV)")
    ax.set_title("Gráfico do potencial da membrana")
    ax.grid(True)

    # Criando o gráfico do neurônio total
    fig_total, ax_total = plt.subplots()

    ax_total.set_xlabel("tempo(ms)")
    ax_total.set_ylabel("Corrente(μA)")
    ax_total.set_title("EEG sintético")
    ax_total.grid(True)

    lista_tT = [0]
    gain = 0.2  # so uma variavel para dar contraste no gráfico
    EEG = 0  # Variavel de resposta do EEG
    # Um EEG não mede V total, mede a corrente sinaptica entre os neuronios
    for n in neuronios:
        V = n.estado["V"]
        EEG += g["SynE"][0] * n.estado["SynE"] * (V - g["SynE"][1]) + g["SynI"][
            0
        ] * n.estado["SynI"] * (V - g["SynI"][1])

    V_soma = gain * EEG

    lista_VT = atualização([], V_soma)
    (lineT,) = ax_total.plot(lista_tT, lista_VT, label="Corrente de Sinapse(t)")

    ax.legend()
    ax_total.legend()

    plt.show(block=False)

    manager1 = fig.canvas.manager
    manager2 = fig_total.canvas.manager
    manager1.window.wm_geometry("+0+200")
    manager2.window.wm_geometry("+950+200")

    # Variaveis de performace
    rende_todo = 10
    frame = 0

    pode_pausar = True

    # Para a decomposição, isso gravará o sinal
    gravar = False
    sinal = []

    while True:
        # Pausa a simulação
        if kb.is_pressed("space") and pode_pausar:
            pode_pausar = False
            print("Pausou")
            # Impede e ir para o loop e dar break automaticamente
            while kb.is_pressed("space"):
                if kb.is_pressed("escape"):
                    break

            # Loop de analise, os canvas sao para eu poder mexer no grafico
            while True:
                if kb.is_pressed("space"):
                    break
                if kb.is_pressed("escape"):
                    break
                fig.canvas.draw()
                fig.canvas.flush_events()
                fig_total.canvas.draw()
                fig_total.canvas.flush_events()
                plt.pause(dt)
            print("Voltou")

        if not kb.is_pressed("space"):
            pode_pausar = True

        if kb.is_pressed("escape"):
            break

        if kb.is_pressed("up"):
            Imax += 5
        elif kb.is_pressed("down"):
            Imax -= 5

        for _ in range(n_sub):
            for i, n in enumerate(neuronios):
                Ir = 0
                # Só o primeiro neuronio é estimulado
                if i == 0 and (kb.is_pressed("enter")):
                    Ir = Imax

                step_neuronio(n.estado, Ir, dt, n.k, g, Cm)

                # atualizando a sinapse
                for c in conexoes:
                    pre = neuronios[c["pre"]]
                    pos = neuronios[c["pos"]]

                    if pre.estado["spike"]:
                        # O peso depende do tamanho do spike
                        fator = np.clip((n.estado["V_pico"]) / 40, 0, 1.5)
                        peso_real = c["peso"] * fator

                        if c["tipo"] == "E":
                            pos.estado["SynE"] = min(
                                pos.estado["SynE"] + peso_real, 4.0
                            )
                        else:
                            pos.estado["SynI"] = min(
                                pos.estado["SynI"] + peso_real, 4.0
                            )

                        # Aqui ele define o começo e o fim do sinal
                        if pre.number == 0:
                            gravar = True
                        if pre.number == 18 and pre.estado["spike"]:
                            if gravar:
                                print(sinal)
                                lista = lista_tT[len(sinal) - len(lista_tT) :]
                                print(list(map(lambda x: round(x, 2), lista)))
                            gravar = False

                        # pre.estado["V_pico"]=-65

        if frame % rende_todo:
            ax.set_xlim(min(lista_t), max(lista_t))

        # Atualizando o tempo
        t += dt_render
        lista_t = atualização(lista_t, t)
        lista_tT = atualização(lista_tT, t, "Total")

        frame += 1
        for n in neuronios:
            # Atualizando a lista dentro dos neuronios
            n.lista_V = atualização(n.lista_V, n.estado["V"])
            n.estado["V_pico"] = -65
            V = n.estado["V"]
            EEG += g["SynE"][0] * n.estado["SynE"] * (V - g["SynE"][1]) + g["SynI"][
                0
            ] * n.estado["SynI"] * (V - g["SynI"][1])

        V_soma = gain * EEG

        # Perda com o tempo
        EEG *= 0.1

        lista_VT = atualização(lista_VT, V_soma, "Total")
        if gravar:
            sinal = atualização(sinal, float(V_soma), "Total")

        if frame % rende_todo == 0:
            for n in neuronios:
                # Atualizando a lista dentro dos neuronios
                n.line.set_data(lista_t, n.lista_V)

            # Para o grafico total
            lineT.set_data(lista_tT, lista_VT)
            minimo = lista_tT[-500] if len(lista_tT) > 500 else min(lista_tT)
            ax_total.set_xlim(minimo, lista_tT[-1])

        # Gráfico individual
        if (get_extremo(neuronios, "min") - 1) > -20:
            minimo = -20
        else:
            minimo = get_extremo(neuronios, "min") - 1

        if (get_extremo(neuronios, "max") + 1) < 20:
            maximo = 20
        else:
            maximo = get_extremo(neuronios, "max") + 1

        ax.set_ylim(minimo, maximo)

        # Limitando a taxa de atualização do EEG
        if frame % rende_todo == 0:
            # Gráfico total
            if (min(lista_VT) - 1) > -20:
                minimo = -20
            else:
                minimo = min(lista_VT) - 1

            if (max(lista_VT) + 1) < 20:
                maximo = 20
            else:
                maximo = max(lista_VT) + 1

            ax_total.set_ylim(minimo, maximo)

        neuronios[0].line.set_label(f"V1(t) \n Corrente máxima: {Imax}")

        ax.legend()

        if frame % rende_todo == 0:
            if dt_render < 0.01:
                fig.canvas.draw()
                fig.canvas.flush_events()

                if (int(t / dt)) % 20 == 0:
                    fig_total.canvas.draw()
                    fig_total.canvas.flush_events()
                plt.pause(dt)
            else:
                fig.canvas.draw()
                fig.canvas.flush_events()

                if (int(t / dt)) % 20 == 0:
                    fig_total.canvas.draw()
                    fig_total.canvas.flush_events()
                plt.pause(0.01)

    plt.close(fig)
    plt.close(fig_total)

    # Tentando resolver um problema de alteração da resolução do menu
    plt.close("all")


if __name__ == "__main__":
    main()
