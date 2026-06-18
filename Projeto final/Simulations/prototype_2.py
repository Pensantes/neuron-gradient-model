# Se usarmos o Agg do Python, o Jupyter não consegue rodar. Por isso vamos
# usar o Agg do Tkinter para o .bat conseguir abrir
import matplotlib

matplotlib.use("TkAgg")

import os  # noqa: E402

# Faz o pygame aparecer na esquerda
os.environ["SDL_VIDEO_WINDOW_POS"] = "0,300"

# O keybord até poderia ficar em cima, mas o plt é melhor não
import matplotlib.pyplot as plt  # noqa: E402
import keyboard as kb  # noqa: E402
import numpy as np  # noqa: E402
import random  # noqa: E402
import pygame  # noqa: E402
# os comentarios são so para nao aparecer um erro chato do ruff


def esta_dentro_x(
    np_x: float, lista: list, esp_canal: float, larg_canal: float
) -> bool:
    """Essa função serve para verificar se a minha posição x esta colidindo com
    alguma parte da membrana. Entao retorna True se eu nao estiver em nenhum canal"""
    for i in lista.values():
        if 0 < np_x - i - esp_canal < larg_canal:
            return False
    return True


class Ion:
    """Classe de objeto para os íons da animação"""

    def __init__(
        self, x: complex, v: complex, imagem: pygame.image, tipo: str, fator: float
    ):
        """Como variáveis internas, temos

        x: posição atual do íon em complexo

        v: velocidade atual do íon em complexo

        imagem: qual o sprite desse objeto

        tipo: qual categoria de animação ela vai pertencer

        fator: uma variável auxiliar para ajustar a velocidade de evolução
        """
        self.pos = np.array([x, v], dtype=complex)
        self.imagem = imagem
        # define qual animaçao ela vai cumprir
        self.tipo = tipo
        # Só para definir onde a imagem vai ser desenhada
        self.rect = self.imagem.get_rect(
            center=(np.real(self.pos[0]), np.imag(self.pos[0]))
        )
        self.fator = fator

    # Movimento
    def update(self, dt: float, ions: list, b_membrana: pygame.image, canais: list):
        """Função que atualiza a posição da partícula, recebe:

        dt: passo de evolução

        ions: lista de ions ativos

        b_membrana: imagem da do bloco de membrana

        canais: lista com as posições dos canais"""
        if self.tipo == "Fluxo Superior":
            if np.real(self.pos[0]) > width:
                ions.remove(self)
            periodo = np.real(self.pos[0]) // 40
            self.pos[0] += (
                np.real(self.pos[1]) * dt
                + self.fator * np.sin(periodo + 5 * self.fator) * 1j
            )

        if self.tipo == "Fluxo Inferior":
            if np.real(self.pos[0]) < 0:
                ions.remove(self)
            periodo = np.real(self.pos[0]) // 40
            self.pos[0] += (
                np.real(self.pos[1]) * dt
                + self.fator * np.sin(periodo + 5 * self.fator) * 1j
            )

        if (
            self.tipo == "Na"
            or self.tipo == "K"
            or self.tipo == "L"
            or self.tipo == "Ca"
        ):
            if np.imag(self.pos[0]) < 0 or np.imag(self.pos[0]) > height:
                ions.remove(self)
            self.pos[0] += (
                self.pos[1] * dt
                + np.sin(np.imag(self.pos[0]) + np.real(self.pos[0])) / 5
            )

        if self.tipo == "Visual":
            self.pos[0] += self.pos[1] * dt
            self.rect.center = (np.real(self.pos[0]), np.imag(self.pos[0]))

            sprite_y = b_membrana.get_height()
            sprite_x = b_membrana.get_width()
            membr_y = height // 2

            y, vy = np.imag(self.pos)
            x, vx = np.real(self.pos)

            np_x = float(x + vx * dt)
            np_y = float(y + vy * dt)

            # Na membrana
            if abs(np_y - membr_y - sprite_y * (5 / 8)) <= sprite_y / 4:
                larg_canal = (9 / 25) * sprite_x
                esp_canal = (8 / 25) * sprite_x
                if esta_dentro_x(np_x, canais, larg_canal, esp_canal):
                    if abs(y - membr_y - sprite_y * (5 / 8)) <= sprite_y / 4:
                        self.pos[1] = -np.conj(self.pos[1])
                    else:
                        self.pos[1] = np.conj(self.pos[1])

            # Condições que invertem o movimento nas fronteiras
            if np_y <= 0 or np_y >= height:
                self.pos[1] = np.conj(self.pos[1])

            if np_x <= 0 or np_x >= width:
                self.pos[1] = -np.conj(self.pos[1])

        self.rect.center = (np.real(self.pos[0]), np.imag(self.pos[0]))

    def draw(self, surface: pygame.surface):
        """Essa função atualiza o desenho do ion, recebe:

        a tela a ser atualizado o desenho"""
        surface.blit(self.imagem, self.rect)


def steady_state(Q: np.array):
    """Cria o vetor estacionário para um dada matriz de transição

    Q: Matriz de transição característica desse vetor"""

    # Vamos definir o equilíbrio inicial
    A = Q.copy()
    # Substitui a última linha por 1
    A[-1, :] = 1
    # Cria um vetor [0,0,0,...]
    b = np.zeros(Q.shape[0])
    # Troca o último elemento por 1
    b[-1] = 1
    # Resolve o sistema linear e acha o vetor
    return np.linalg.solve(A, b)


def exp_seguro(x: float):
    """Função que impede que um valor saia de um certo intervalo, ela recebe:

    x: o expoente de uma conta"""
    # vamos capar os expoentes para não ter erro computacional
    return np.exp(np.clip(x, -50, 50))


def noise_P(n: int, sigma: float):
    """Essa função serve para adicionar um noise no calculo do P, para ficar
    mais realista.

    Entrada:

    n: tamanho do vetor de estado

    sigma: desvio padrão da distribuição aleatória"""
    # Gera um noise aleatório
    eta = np.random.normal(0, sigma, size=n)
    eta = np.mean(eta)  # Força o np.sum(eta) a ser 0. Não alterando o P

    return eta


def k_Na(V: float):
    """Função que atualiza as constantes de equilibrio do canal de Na

    Recebe o potencial atual"""
    return [
        0.04 * exp_seguro(0.075 * (V + 65)),  # k1(ativação)
        2.5 * exp_seguro(-0.035 * (V + 65)),  # k-1(desativação)
        0.25 * exp_seguro(0.07 * (V + 65)),  # alfa(abertura)
        5 * exp_seguro(-0.03 * (V + 65)),  # beta(fechamento)
        1.8 * exp_seguro(0.03 * (V + 65)),  # k2(inativação)
        0.06 * exp_seguro(-0.025 * (V + 65)),  # k-2(recuperação)
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
    """Função que atualiza as constantes de equilibrio do canal de vazão

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


def k_syn(V):
    """Função que atualiza as constantes de equilibrio do canal de Sinapse

    Recebe o potencial atual"""
    return []


def dV_dt(t: float, V: float, estados: dict, g: dict, C: float, Ir: float):
    """Diferencial do potencial para atualiza-lo.

    Entradas:

    t: tempo atual

    V: potencial atual

    estados: todos os vetores probabilidade de estado dos canais (dicionario)

    g: a condutância dos canais (dicionario)

    C: a capacitância da membrana

    Ir: corrente de estímulo
    """
    # Simplesmente aplica a equação diferencial do potencial
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
    # Corrente de acúmulo de cálcio (não coube na linha de cima T_T)
    # Corrente da sinapse Excitatoria
    comp7 = -(g["SynE"][0] / C) * (V - g["SynE"][1]) * estados["SynE"]
    # Corrente da sinapse Inibitória
    comp8 = -(g["SynI"][0] / C) * (V - g["SynI"][1]) * estados["SynI"]

    return (
        comp1 + comp2 + comp3 + comp4 + comp5 + comp6 + comp7 + comp8,
        comp2,
        comp3,
        comp4,
        comp5,
    )


def dCa_dt(ICa: float, Ca_i: float):
    """Diferencial do canal não linear de cálcio

    Entrada:

    ICa: corrente no canal de cálcio

    Ca_i: potencial acumulado dos íons cálcio
    """
    Ca_rest = 0.0001
    alpha = 5e-7
    beta = 0.02
    return -alpha * ICa - beta * (Ca_i - Ca_rest)


def dSyn_dt(s: float, tau: float):
    """Diferencial da conexão sináptica, modela o decaimento do estímulo

    Entrada:

    s: intensidade atual do estímulo

    tau: constante de decaimento
    """
    return -s / tau


def KCa_open(Ca_i: float):
    """
    Define o 'Vetor probabilidade' do canal não linear de cálcio

    Entrada:

    Ca_i: potencial acumulado do íon cálcio
    """
    Kd = 0.0005  # mM
    n = 4

    return (Ca_i**n) / (Ca_i**n + Kd**n)


def Matriz_de_transicao(nome: str, k: dict, V: float):
    """
    Cria a matriz de transição relacionada ao vetor probabilidade específico

    Entrada:

    nome: qual o nome do íon que será gerada a matriz

    k: dicionário de constantes de equilíbrio

    V: potencial de membrana

    Saída:

    A matriz de transição do canal
    """

    if nome != "Na":
        K = k[nome][4](V)
        # Cria a matriz de transição
        Q = np.array(
            [[-K[0], K[1], 0], [K[0], -(K[1] + K[2]), K[3]], [0, K[2], -K[3]]],
            dtype=float,
        )
    else:
        K = k[nome][6](V)
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


def f(t: float, y: np.array, k: dict, g: dict, C: float, Ir: float):
    """
    Função diferencial dos estados, ela que calcula o fator de evolução de cada uma das variáveis.

    Entradas:

    t: tempo atual da iteração

    y: vetor que concatena todas as variáveis

    k: dicionário das constantes de equilíbrio

    g: dicionário das condutâncias de cada canal

    C: capacitância da membrana

    Ir: estímulo externo

    Saída:

    Um vetor de mesmo tamanho que o y, mas as entradas são as variações em cada uma das componentes

    """

    # Tau das sinapses
    tau_E = 5.0
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
    dPNa = Matriz_de_transicao("Na", k, V) @ PNa + noise_P(4, sigma_Na)
    dPK = Matriz_de_transicao("K", k, V) @ PK + noise_P(3, sigma_K)
    dPCa = Matriz_de_transicao("Ca", k, V0) @ PCa + noise_P(3, sigma_Ca)
    dPL = Matriz_de_transicao("L", k, V) @ PL
    dsE = dSyn_dt(SynE, tau_E)
    dsI = dSyn_dt(SynI, tau_I)

    # Eu vou colher as correntes tambem para o pygame
    dV, IL, INa, IK, ICa = dV_dt(
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
    return (
        np.concatenate([dPNa, dPK, dPCa, dPL, [dV], [dCa], [dsE], [dsI]]),
        IL,
        INa,
        IK,
        ICa,
    )


def RK4(t: float, y: list, dt: float, k: dict, g: dict, C: float, Ir: float):
    """
    Função que aplica o método de evolução RK4 em uma função

    Entradas:

    t: tempo atual da iteração

    y: vetor que junta todas as variáveis para evoluir

    dt: passo de evolução

    k: dicionário das constantes de equilíbrio

    g: dicionário das condutâncias de cada canal

    C: capacitância da membrana

    Ir: estímulo externo

    Saída:

    Novo estado evoluído de cada variável
    """

    # f retorna as correntes tmb, vamos so colher elas
    k1 = f(t, y, k, g, C, Ir)[0]
    k2 = f(t + dt / 2, y + dt * k1 / 2, k, g, C, Ir)[0]
    k3 = f(t + dt / 2, y + dt * k2 / 2, k, g, C, Ir)[0]
    k4, IL, INa, IK, ICa = f(t + dt, y + dt * k3, k, g, C, Ir)

    return y + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4), IL, INa, IK, ICa


def atualização(lista: list, var: float):
    """
    Função auxiliar que limita o tamanho de uma lista para poupar memória

    Entrada:

    lista: lista para atualizar

    var: valor a ser adicionado nessa lista

    Saída:

    lista com var adicionado, mas limitada em um certo tamanho

    """

    # Limita a minha lista para poupar memoria
    if len(lista) == 500:
        lista.pop(0)
    lista.append(var)

    return lista


def main():
    pygame.init()

    # Definindo as variáveis

    # Pare de ser chato Python ToT, ta aq sua variavel global
    global V0

    V0 = -65  # Pot de repouso
    # Agora, as constantes de equilibrio
    k = {
        # Temos 3 estados, então 4 constantes: k+1, k-1, beta e alfa, respectivamente
        # com k+1 R--->AR // k-1 AR--->R // beta AR--->AR* // alfa AR*--->AR.
        # Para o Na, temos um estado adicional k2 AR*--->I // k-2 I--->R
        # Em que R é o canal fechado, AR é o canal ativado mas fechado e AR* é ele aberto
        "Na": [5.0, 2.0, 20.0, 5.0, 0.0, 0.0, k_Na],
        "K": [2.0, 1.0, 10.0, 2.0, k_K],
        "Ca": [2.0, 1.0, 10.0, 2.0, k_Ca],
        "L": [0.1, 0.1, 1.0, 1.0, k_L],
        "SynE": [0.1, 0.1, 1.0, 1.0, k_syn],
        "SynI": [0.1, 0.1, 1.0, 1.0, k_syn],
    }
    # Esse é o dicionario de estados
    estados = {
        # Para os vetores P, temos que P[0] é a porcentagem de canais fechados
        # P[1] é a porcentagem de canais ativados fechados e P[2] a porcentagem
        # de canais ativados e abertos
        # Eu uso o steady_state para saber qual o vetor P que esta em equilibrio
        # em V0
        "PNa": steady_state(Matriz_de_transicao("Na", k, V0)),
        "PK": steady_state(Matriz_de_transicao("K", k, V0)),
        # Canal clássico de cálcio
        "PCa": steady_state(Matriz_de_transicao("Ca", k, V0)),
        "PL": np.array([1, 0, 0], dtype=float),
        # Para V, V como pot atual e temos V0 como pot de repouso, respectivamente
        "V": V0,
        # Canal não linear de cálcio
        "Ca_i": 0.0001,  # mM
        # excitatória tipo AMPA
        "SynE": 0.0,
        # Inibitória tipo GABA-A
        "SynI": 0.0,
    }
    # Condutância máxima dos canais e potencial padrão
    g = {
        "Na": [120, 50],  # mS/cm², mV
        "K": [36, -77],
        "Ca": [1, 120],
        "L": [0.3, -54.4],
        "KCa": [5.0, -77],
        "SynE": [0.5, 0.0],
        "SynI": [0.8, -75],
    }

    Cm = 1  # Capacitancia da membrana (microF/cm²)
    t = 0  # tempo
    delta = 0.005  # variação do tempo
    Ir = 0  # estimulo
    Imax = 15  # qual deve ser a corrente do estimulo

    modo_teste = False  # Aqui eu defino uma bateria de testes repetitivos
    t0 = t  # Variavel de marcação do delta total
    intervalo_medio = 1  # O periodo do pulso

    n_sub = 5  # Numero de sub passos para o RK4

    lista_pot = [V0, estados["V"]]
    lista_t = [0, t]

    plt.ion()  # permite interação com o grafico

    fig, ax = plt.subplots()  # so me interessa o ax, ele é o meu objeto de grafico

    ax.set_xlabel("tempo(ms)")
    ax.set_ylabel("potenciais(mV)")
    ax.set_title("Gráfico do potencial da membrana")
    ax.grid(True)

    (line,) = ax.plot(lista_t, lista_pot, label="V(t)")
    ax.legend()

    plt.show(block=False)

    # Forçando a janela do Matplotlib aparecer na direita
    manager = plt.get_current_fig_manager()
    manager.window.wm_geometry("+960+200")

    # Variáveis de corrente para o Pygame
    INa = 0
    IK = 0
    IL = 0
    ICa = 0

    # Para as outras funções não chorarem, vou declarar como global aq
    global width, height

    # Estrutura do espaço
    width, height = 960, 600

    tela = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Membrana do neurônio")

    clock = pygame.time.Clock()

    b_membrana = pygame.image.load(r"Simulations\Images\Membrana.png").convert_alpha()
    b_canal = pygame.image.load(r"Simulations\Images\Canal Iônico.png").convert_alpha()
    i_sodio = pygame.image.load(r"Simulations\Images\Sódio.png").convert_alpha()
    i_potassio = pygame.image.load(r"Simulations\Images\Potássio.png").convert_alpha()
    i_calcio = pygame.image.load(r"Simulations\Images\Cálcio.png").convert_alpha()

    b_membrana = pygame.transform.scale(b_membrana, (80, 80))

    b_canal = pygame.transform.scale(b_canal, (80, 80))

    i_sodio = pygame.transform.scale(i_sodio, (16, 16))

    i_potassio = pygame.transform.scale(i_potassio, (20, 20))

    i_calcio = pygame.transform.scale(i_calcio, (24, 24))

    # algumas informaçoes para o canal existir
    sprite_x = b_canal.get_width()
    esp_canal = sprite_x * (8 / 25)
    larg_canal = sprite_x * (9 / 25)

    # quais todos os espaços que eu vou desenhar a membrana?
    locais_canal = random.sample(range(0, width, b_membrana.get_width()), 4)

    # Posição espacial dos canais iônicos
    pos_canais = {"Na": 0, "K": 0, "L": 0, "Ca": 0}

    for i in pos_canais:
        pos_canais[i] = random.choice(locais_canal)
        locais_canal.remove(pos_canais[i])

    # lista de particulas
    ions = []

    sprite = [i_sodio, i_potassio, i_calcio]
    membr_y = height // 2

    # gerando particulas visuais em cima
    for i in range(50):
        ion = Ion(
            x=random.randrange(0, width)
            + (random.randrange(0, membr_y // 2 - 20) + 1) * 1j,
            v=random.randrange(-80, 80) + random.randrange(-80, 80) * 1j,
            imagem=sprite[random.randint(0, 2)],
            tipo="Visual",
            fator=np.random.normal(1, 1, size=1).item(),
        )
        ions.append(ion)
    # gerando particulas visuais em baixo
    for i in range(50):
        ion = Ion(
            x=random.randrange(0, width)
            + (random.randrange(height - membr_y // 2, height) - 1) * 1j,
            v=random.randrange(-80, 80) + random.randrange(-80, 80) * 1j,
            imagem=sprite[random.randint(0, 2)],
            tipo="Visual",
            fator=np.random.normal(1, 1, size=1).item(),
        )
        ions.append(ion)

    # Vou usar uma trava de teclado posteriormente, entao vou criar isso agr
    space_agr = False
    space_ant = False

    b_agr = False
    b_ant = False

    render_a_cada = 2

    while True:
        # definindo o mode teste
        if kb.is_pressed("T"):
            modo_teste = True
            t0 = t

        space_agr = kb.is_pressed("space")

        if space_agr and not space_ant:
            estados["SynE"] += 0.2

        space_ant = space_agr

        b_agr = kb.is_pressed("B")

        if b_agr and not b_ant:
            estados["SynI"] += 0.2

        b_ant = b_agr

        if not modo_teste:
            if kb.is_pressed("enter"):
                # estimulo manual
                Ir = Imax
            else:
                Ir = 0
            if kb.is_pressed("right"):
                # controlando o intervalo de estimulo
                intervalo_medio += 0.1
                intervalo_medio = round(intervalo_medio, 2)
            elif kb.is_pressed("left"):
                intervalo_medio -= 0.1
                intervalo_medio = round(intervalo_medio, 2)
        else:
            if ((t - t0) // (intervalo_medio)) % 2 == 0:
                Ir = Imax
            else:
                Ir = 0

            if (t - t0) >= 10:
                modo_teste = False

        if kb.is_pressed("esc"):
            pygame.quit()
            break

        if kb.is_pressed("up"):
            Imax += 1
        elif kb.is_pressed("down"):
            Imax -= 1

        # Só para explicar, concatenate pega varios arrays e funde em 1
        y = np.concatenate(
            [
                estados["PNa"],
                estados["PK"],
                estados["PCa"],
                estados["PL"],
                [estados["V"]],
                [estados["Ca_i"]],
                [estados["SynE"]],
                [estados["SynI"]],
            ]
        )

        # Não quero depender da converção automatica
        y = np.array(y, dtype=float)

        for _ in range(n_sub):
            y, IL, INa, IK, ICa = RK4(t, y, delta / n_sub, k, g, Cm, Ir)
            t += delta / n_sub

        estados["PNa"] = y[0:4] / (np.sum(y[0:4]) if np.sum(y[0:4]) != 0 else 1)
        estados["PK"] = y[4:7] / (np.sum(y[4:7]) if np.sum(y[4:7]) != 0 else 1)
        estados["PK"] = y[7:10] / (np.sum(y[7:10]) if np.sum(y[7:10]) != 0 else 1)
        estados["PL"] = y[10:13] / (np.sum(y[10:13]) if np.sum(y[10:13]) != 0 else 1)
        estados["V"] = y[13]
        estados["Ca_i"] = max(y[14], 0)
        estados["SynE"] = max(y[-2], 0)
        estados["SynI"] = max(y[-1], 0)

        lista_pot = atualização(lista_pot, estados["V"])
        lista_t = atualização(lista_t, t)

        line.set_data(lista_t, lista_pot)
        line.set_label(
            f"V(t), Imáximo = {Imax} \n"
            + f"Estímulo ={False if Ir == 0 else True} (pressione Enter)\n"
            + f"Intervalo de experimento: {intervalo_medio} ms (<- ou -> e T para ativar)\n"
            + f"Estimulo sinapse E: {round(estados['SynE'], 2)} (pressione Espaço)\n"
            + f"Estimulo sinapse I: {round(estados['SynI'], 2)} (pressione B)"
        )

        ax.set_xlim(min(lista_t), max(lista_t))

        if (min(lista_pot) - 1) > -20:
            minimo = -20
            # minimo=min(lista_pot)-1
        else:
            minimo = min(lista_pot) - 1

        if (max(lista_pot) + 1) < 20:
            maximo = 20
            # maximo=max(lista_pot)+1
        else:
            maximo = max(lista_pot) + 1

        ax.set_ylim(minimo, maximo)

        # Definindo os potenciais externos e internos
        pot_ex = int(120 + Ir * 5)
        pot_int = 120 + int(estados["V"])

        # algumas informaçoes para o canal existir
        sprite_x = b_canal.get_width()
        esp_canal = sprite_x * (8 / 25)
        larg_canal = sprite_x * (9 / 25)

        dt = clock.tick(60) / 1000

        tela.fill("dark blue")

        # desenhando a membrana
        for i in range(0, width, b_membrana.get_width()):
            if i not in pos_canais.values():
                tela.blit(b_membrana, (i, membr_y))
            else:
                tela.blit(b_canal, (i, membr_y))

        # gerando particulas que fluem no canal de Na
        for i in range(abs(int(INa)) // 10 if abs(INa) // 10 > 1 or INa == 0 else 1):
            if INa > 0:
                x_ = 0j + 1j
            else:
                x_ = height * 1j - 1j
            ion = Ion(
                x=pos_canais["Na"]
                + esp_canal
                + random.randrange(1, int(larg_canal) - 1)
                + x_,
                v=120 * (1 if INa > 0 else -1) * 1j,
                imagem=sprite[0],
                tipo="Na",
                fator=np.random.normal(1, 1, size=1).item(),
            )
            ions.append(ion)

        # gerando particulas que fluem no canal de K
        for i in range(abs(int(IK)) // 10 if abs(IK) // 10 > 1 or IK == 0 else 1):
            if IK > 0:
                x_ = 0j + 1j
            else:
                x_ = height * 1j - 1j
            ion = Ion(
                x=pos_canais["K"]
                + esp_canal
                + random.randrange(1, int(larg_canal) - 1)
                + x_,
                v=120 * (1 if IK > 0 else -1) * 1j,
                imagem=sprite[1],
                tipo="K",
                fator=np.random.normal(1, 1, size=1).item(),
            )
            ions.append(ion)

        # gerando particulas que fluem no canal de vazamento
        for i in range(abs(int(IL)) // 10 if abs(IL) // 10 > 1 or IL == 0 else 1):
            if IL > 0:
                x_ = 0j + 1j
            else:
                x_ = height * 1j - 1j
            ion = Ion(
                x=pos_canais["L"]
                + esp_canal
                + random.randrange(1, int(larg_canal) - 1)
                + x_,
                v=120 * (1 if IL > 0 else -1) * 1j,
                imagem=sprite[random.randint(0, 2)],
                tipo="L",
                fator=np.random.normal(1, 1, size=1).item(),
            )
            ions.append(ion)

        # gerando particulas que fluem no canal de cálcio
        for i in range(abs(int(ICa)) // 10 if abs(ICa) // 10 > 1 or ICa == 0 else 1):
            if ICa > 0:
                x_ = 0j + 1j
            else:
                x_ = height * 1j - 1j
            ion = Ion(
                x=pos_canais["Ca"]
                + esp_canal
                + random.randrange(1, int(larg_canal) - 1)
                + x_,
                v=120 * (1 if ICa > 0 else -1) * 1j,
                imagem=sprite[2],
                tipo="Ca",
                fator=np.random.normal(1, 1, size=1).item(),
            )
            ions.append(ion)

        # gerando particulas que fluem em cima
        for i in range(pot_ex // 50):
            ion = Ion(
                x=0 - 20 + (random.randrange(0, membr_y // 2) - 50) * 1j,
                v=160,
                imagem=sprite[random.randint(0, 2)],
                tipo="Fluxo Superior",
                fator=np.random.normal(1, 1, size=1).item(),
            )
            ions.append(ion)

        # gerando particulas que fluem em baixo
        for i in range(pot_int // 50):
            ion = Ion(
                x=width
                + 20
                + (random.randrange(height - membr_y // 2, height) + 50) * 1j,
                v=-160,
                imagem=sprite[random.randint(0, 2)],
                tipo="Fluxo Inferior",
                fator=np.random.normal(1, 1, size=1).item(),
            )
            ions.append(ion)

        for ion in ions:
            ion.update(dt, ions, b_membrana, pos_canais)

        ax.legend()

        if ((t * 1000) // 5) % render_a_cada == 0:
            # Arualizando as particulas
            for ion in ions:
                ion.draw(tela)

            pygame.display.flip()
            if delta < 0.01:
                fig.canvas.draw_idle()
                fig.canvas.flush_events()

            else:
                fig.canvas.draw_idle()
                fig.canvas.flush_events()

    pygame.quit()
    plt.close()


if __name__ == "__main__":
    main()
