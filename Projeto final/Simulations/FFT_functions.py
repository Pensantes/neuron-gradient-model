import matplotlib

matplotlib.use("TkAgg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pickle  # noqa: E402
from pathlib import Path  # noqa: E402
from sklearn.linear_model import OrthogonalMatchingPursuit  # noqa: E402
from scipy.fft import rfft, rfftfreq, irfft  # noqa: E402

"""
   Para didatica: 
   rfft é uma função que calcula o FFT para sinais reais
   rfftfreq retorna a lista de frequencia de cada coeficiente
   irfft aplica o rfft inverso (O i significa inverse :3 )
"""

bib_path = Path(r"Projeto final\Data\bib_eeg.pkl")


def Decompouser_FFT(sinal: np.ndarray, fs: float):
    """Usando FFT, decompõe o sinal em varias componentes, util para guardar e fazer
    operações futuras"""

    # Garante que ta no formato certo, em teoria não muda nada além do formato
    sinal = np.asarray(sinal, dtype=float)

    # remove componente Média, para o fft só ver as oscilações sem
    # deslocamento vertical
    media = np.mean(sinal)
    x = sinal - media

    # FFT
    coef = rfft(x)
    freqs = rfftfreq(len(x), d=1 / fs)

    return freqs, coef, media


def reconstrutor_FFT(coef: np.ndarray, media: float, n: int):
    """Reconstroi o sinal original a partir dos coeficientes"""
    x_rec = irfft(coef, n=n)
    return x_rec + media


def salvar_assinatura(nome: str, sinal: list, tempo: list):
    """Salva a assinatura do sinal em um array"""
    # Converte no jeito de gente, uso o copy para nao modificar a lista original
    signal = np.asarray(sinal.copy())
    time = np.asarray(tempo.copy())

    # Acha a frequencia do sinal, o diff calcula a diferença entre
    # Amostras consecutivas
    dt_ms = np.mean(np.diff(time))
    fs = 1000 / dt_ms

    freqs, coef, media = Decompouser_FFT(signal, fs)

    biblioteca = carrega_bib()

    biblioteca[nome] = {
        "fs": fs,
        "n": len(signal),
        "media": media,
        "freqs": freqs,
        "coef_real": coef.real,
        "coef_imag": coef.imag,
    }

    salva_bib(biblioteca)


def load_assinatura(nome: str):
    """Carrega a assinatura do sinal"""
    biblioteca = carrega_bib()

    data = biblioteca[nome]

    fs = float(data["fs"])
    n = int(data["n"])
    media = float(data["media"])

    coef = data["coef_real"] + data["coef_imag"] * 1j

    sinal = reconstrutor_FFT(coef, media, n)

    return sinal, fs


def carrega_bib():
    """Garante que eu receba algo ao tentar carregar a minha biblioteca"""
    if not bib_path.exists() or bib_path.stat().st_size == 0:
        return {}

    with open(bib_path, "rb") as f:
        return pickle.load(f)


def salva_bib(biblioteca: dict):
    """Garante que eu salve a minha biblioteca no arquivo bib_eeg"""
    bib_path.parent.mkdir(parents=True, exist_ok=True)

    with open(bib_path, "wb") as f:
        pickle.dump(biblioteca, f)


def carrega_espaco():
    """Retorna um dicionario dos sinais salvos"""
    biblioteca = carrega_bib()

    sinais = {}
    for i in biblioteca:
        sinal, fs = load_assinatura(i)
        sinais[i] = sinal

    # Igualar o tamanho de todos os sinais, imaginando que eles começam ao mesmo tempo
    limite = menor_sinal(sinais)

    for i in sinais:
        sinais[i] = sinais[i][0:limite]

    return sinais


def criar_frag_teste(sinais: dict, nomes: list, pesos: list, inicio: int, tamanho: int):
    """
    Essa função cria um fragmento de tamanho fixo e com uma composição específica.

    sinais: lista com todos os sinais disponiveis
    nomes: quais sinais compões esse fragmento
    pesos: os pesos de cada sinal em nomes
    inicio: a partir de que trecho dos sinais a gente vai pegar
    tamanho: tamanho do sinal
    """

    # Veja se o tamanho ta coerente, caso contrario restrinja o tamanho
    try:
        sinais[nomes[0]][inicio + tamanho]
    except IndexError:
        tamanho = len(sinais[nomes[0]]) - inicio

    # A principio, o frag é um array cheio de zeros
    frag = np.zeros(tamanho)

    for nome, peso in zip(nomes, pesos):
        trecho = sinais[nome][inicio : inicio + tamanho]

        frag += peso * trecho

    return frag


def normaliza_sinal(x: np.ndarray):
    """Normalizando o sinal para compararmos somente as oscilações"""
    x = np.asarray(x, dtype=float)
    x = x - np.mean(x)

    norma = np.linalg.norm(x)

    if norma < 1e-12:
        return x

    return x / norma


def montar_dicionario_janelas(sinais: dict, tamanho: int, candidatos: list):
    """
    Me fornece, em uma matriz coluna, as varias combinaçoes dos sinais possiveis.
    Os sinais vão estar codificados na lista metadados, na qual indices iguais
    representam colunas condizentes
    """
    colunas = []
    metadados = []

    vistos = set()

    # Vamos rodar os melhores candidatos na nossa matriz
    for i in candidatos:
        chave = (i["nome"], i["inicio"])

        if chave in vistos:
            continue

        vistos.add(chave)

        sinal = sinais[i["nome"]]
        trecho = normaliza_sinal(sinal[i["inicio"] : i["fim"]])

        colunas.append(trecho)
        metadados.append(i)

    D = np.column_stack(colunas)

    return D, metadados


def menor_sinal(sinais: dict):
    """Retorna o menor tamanho dos sinais, assim podemos igualar todos em tamanho"""
    menor = float("inf")
    for i in sinais.values():
        if len(i) < menor:
            menor = len(i)

    return menor


def score_combination(a: np.ndarray, b: np.ndarray):
    """Me retorna os scores da operação D.T @ fragmento"""
    return float(np.dot(a, b))


def janela_valida(sinal, inicio, tamanho):
    return 0 <= inicio and inicio + tamanho <= len(sinal)


def top_candidatos_finder(
    fragmento_norm: np.ndarray,
    sinais: list,
    tamanho: int,
    passo: int,
    top_k: int,
    regioes=None,
):
    """Função que me diz quais são os top_k candidatos ao rodar no passo definido"""

    candidatos = []

    for nome, sinal in sinais.items():
        sinal = np.asarray(sinal, dtype=float)

        if regioes is None:
            inicios = range(0, len(sinal) - tamanho + 1, passo)
        else:
            inicios_set = set()

            for reg in regioes:
                if reg["nome"] != nome:
                    continue

                centro = reg["inicio"]
                raio = reg["raio"]

                a = max(0, centro - raio)
                b = min(len(sinal) - tamanho, centro + raio)

                for inicio in range(a, b + 1, passo):
                    inicios_set.add(inicio)

            inicios = sorted(inicios_set)

        for inicio in inicios:
            # Primeiro valida se a janela que foi pega é valida
            if not 0 <= inicio and inicio + tamanho <= len(sinal):
                continue

            # Pega o score do trecho testado
            trecho = normaliza_sinal(sinal[inicio : inicio + tamanho])
            score = abs(float(np.dot(fragmento_norm, trecho)))

            candidatos.append(
                {
                    "nome": nome,
                    "inicio": inicio,
                    "fim": inicio + tamanho,
                    "score": score,
                }
            )

    candidatos.sort(key=lambda x: x["score"], reverse=True)

    return candidatos[:top_k]


def best_decomposicao_FFT(
    fragmento,
    sinais,
    passos=(100, 25, 5, 1),
    top_k=80,
    max_componentes=None,
    erro_alvo=0.01,
    score_alvo=0.999,
):
    """
    Cospe a melhor combinação de sinais dentro de uma biblioteca
    de sinais possíveis para compor o meu fragmento de EEG.
    """

    fragmento = np.asarray(fragmento, dtype=float)
    tamanho = len(fragmento)
    y = normaliza_sinal(fragmento)

    if max_componentes is None:
        max_componentes = min(10, len(sinais))

    candidatos = None

    # busca no modelo coarse-to-fire
    for passo in passos:
        if candidatos is None:
            regioes = None
        else:
            regioes = [
                {
                    "nome": c["nome"],
                    "inicio": c["inicio"],
                    "raio": 3 * passo_anterior,  # noqa: F821
                }
                for c in candidatos
            ]

        candidatos = top_candidatos_finder(
            fragmento_norm=y,
            sinais=sinais,
            tamanho=tamanho,
            passo=passo,
            top_k=top_k,
            regioes=regioes,
        )

        # O noqa é para tirar o aviso chato, eu uso o passo_anterior antes
        passo_anterior = passo  # noqa: F841

    # monta o dicionario final para score
    D, metadados = montar_dicionario_janelas(sinais, tamanho, candidatos)

    melhor = None

    # vamos tentar decompor no numero de componentes alvo
    for n_comp in range(1, max_componentes + 1):
        modelo = OrthogonalMatchingPursuit(n_nonzero_coefs=n_comp, fit_intercept=False)

        modelo.fit(D, y)

        coef = modelo.coef_
        # Reconstrução do sinal original
        recon = D @ coef

        erro = np.linalg.norm(y - recon) / (np.linalg.norm(y) + 1e-12)
        score = float(np.dot(y, normaliza_sinal(recon)))

        idx = np.flatnonzero(np.abs(coef) > 1e-12)

        componentes = []

        for i in idx:
            componentes.append(
                {
                    "nome": metadados[i]["nome"],
                    "inicio": metadados[i]["inicio"],
                    "fim": metadados[i]["fim"],
                    "peso": float(coef[i]),
                    "score_janela": metadados[i]["score"],
                }
            )

        resultado = {
            "componentes": componentes,
            "reconstrução": recon,
            "erro": erro,
            "score": score,
            "n_componentes": n_comp,
            "candidatos": candidatos,
        }

        melhor = resultado

        if erro <= erro_alvo or score >= score_alvo:
            break

    return melhor


def componentes_teste(resultado: dict):
    """
    Vai normalizar cada uma das componentes, fornecendo um valor aproximado
    da composição do sinal
    """

    total = 0
    for componente in resultado["componentes"]:
        total += abs(componente["peso"])

    for i, j in enumerate(resultado["componentes"]):
        print(
            f"Componente {i} ({j['nome']}, atraso de {j['inicio']}): {abs(j['peso']) / total}"
        )


def main(comp_reais: list, inicio: int):
    sinais = carrega_espaco()

    print(sinais)

    sinais_reais = ["Dedão", "Indicador", "Dedo médio", "Anelar", "Mindinho"]

    frag = criar_frag_teste(sinais, sinais_reais, comp_reais, inicio, 300)

    resultado = best_decomposicao_FFT(
        frag,
        sinais,
    )

    return resultado, normaliza_sinal(frag)


if __name__ == "__main__":
    main([1, 1, 0, 0, 0], 0)
