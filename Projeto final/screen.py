def main():
    from PIL import Image
    import keyboard as kb
    import subprocess
    import pygame
    import json
    import math
    import sys
    import os

    caminho = os.path.join(os.path.dirname(__file__), "Simulations")
    sys.path.append(caminho)

    # Eu estou ignorando porque esse erro é resolvido pela parte de cima
    import FFT_functions as fft  # type: ignore

    # Faz o pygame aparecer na esquerda
    os.environ["SDL_VIDEO_WINDOW_POS"] = "240,100"

    class StopAll(Exception):
        """Exceção de uma forma de erro"""

        pass

    def is_in(mx: float, my: float, rect: pygame.Rect):
        """
        Vamos verificar e o mouse está em cima do botão. \n
        Entradas: \n
        mx: posição horizontal do mouse \n
        my: posição vertical do mouse \n
        rect: superfície do botão \n
        Saída: \n
        retorna um boolean
        """
        return rect.collidepoint(mx, my)

    def carregar_gif(caminho: str):
        """
        Decompõe um gif em frames e guarda eles em uma lista \n
        Entradas:\n
        caminho: a string do diretório do gif\n
        Saídas:\n
        lista com os frames do gif\n
        """
        gif = Image.open(caminho)

        frames = []
        try:
            # Colocando cada frame dentro de frames
            while True:
                frame = gif.convert("RGBA")
                frame = pygame.image.fromstring(frame.tobytes(), frame.size, "RGBA")
                frames.append(frame)
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass

        return frames

    def justificar_texto(texto: str, largura: int):
        """Da as quebras de linha quando o texto atinge um certo tamanho\n
        Entradas:\n
        text: string com o texto completo\n
        largura: tamanho da linha\n
        saída:\n
        texto justificado"""
        linha = ""
        palavras = texto.split()

        tamanho = 0
        for palavra in palavras:
            if tamanho + len(palavra) + 1 > largura:
                linha += "\n"
                tamanho = 0

            linha += palavra + " "
            tamanho += len(palavra) + 1

        return linha

    def componentes_reais(resultados: dict, modo: str):
        """Essa função extrai o resultado e coloca como uma string, há dois modos:\n
        Estimada: imagina que resultados é um dicionario da biblioteca FFT_functions\n
        Reais: imagina que resultados é uma lista de números puros\n
        \n
        Entradas: \n
        Resultados: Pode variar entre um dicionario ou uma lista, mas basicamente é um dos dois e contém o resultado da FFT_functions em string\n
        modo: ja foi explicado acima\n
        Saída:\n
        Retorna uma string formatada para ser escrita"""

        if modo == "Estimada":
            total = 0
            texto = ""
            for componente in resultados["componentes"]:
                total += abs(componente["peso"])

            areas = ["Ombro", "Fossa cubital", "Pulso"]
            for i, j in enumerate(resultado["componentes"]):
                ind_area = j["inicio"] // 300
                texto += (
                    f"Componente {i + 1} ({j['nome']}, região: {areas[ind_area]}): {abs(j['peso']) / total}"
                    + "\n"
                )
        if modo == "Reais":
            texto = ""
            nomes = ["Dedão", "Indicador", "Dedo médio", "Anelar", "Mindinho"]
            for i, j in enumerate(resultados):
                texto += (
                    f"Componente {i + 1} ({nomes[i]}): {resultados[i] / sum(resultados)}"
                    + "\n"
                )

        return texto

    # Iniciando o pygame
    pygame.init()

    # Para de matar o meu jogo subprosses T_T
    pygame.display.init()

    # dimensoes
    larg = 800
    altura = 600

    # tempo
    t = 0
    clock = pygame.time.Clock()

    # Fazendo a tela e o nome dela
    tela = pygame.display.set_mode((larg, altura))
    pygame.display.set_caption("Menu")

    # Para poder mudar de tela sem nenhum problema
    screen = "Menu"

    # Isso vai para o solver mais tarde
    lista_dedos = [0, 0, 0, 0, 0]
    area = None

    # Imagens
    solo_botao = pygame.image.load(
        r"Simulations\Images\Solo Neuron.png"
    ).convert_alpha()
    multi_botao = pygame.image.load(
        r"Simulations\Images\Multi Neuron.png"
    ).convert_alpha()
    solver_botao = pygame.image.load(
        r"Simulations\Images\Solver Neuron.png"
    ).convert_alpha()
    finger_botao = pygame.image.load(
        r"Simulations\Images\Finger Neuron.png"
    ).convert_alpha()
    amarelo_botao = pygame.image.load(r"Simulations\Images\amarelo.png").convert_alpha()

    arrow_botaoR = pygame.image.load(
        r"Simulations\Images\Arrow_button -R.png"
    ).convert_alpha()
    arrow_botaoL = pygame.image.load(
        r"Simulations\Images\Arrow_button -L.png"
    ).convert_alpha()

    Arm_png = pygame.image.load(r"Simulations\Images\Arm image.png").convert_alpha()

    fundo_text = pygame.image.load(
        r"Simulations\Images\Fundo\Fundo Text.png"
    ).convert_alpha()
    frames_fundo = carregar_gif(r"Simulations\Images\Fundo\Fundo inicial.gif")
    frame_i = 0

    # dando resize
    solo_botao = pygame.transform.scale(solo_botao, (288, 88))

    multi_botao = pygame.transform.scale(multi_botao, (288, 88))

    solver_botao = pygame.transform.scale(solver_botao, (288, 88))

    finger_botao = pygame.transform.scale(finger_botao, (72, 22))

    amarelo_botao = pygame.transform.scale(amarelo_botao, (144, 144))

    arrow_botaoR = pygame.transform.scale(arrow_botaoR, (213, 88))

    arrow_botaoL = pygame.transform.scale(arrow_botaoL, (213, 88))

    Arm_png = pygame.transform.scale(Arm_png, (675, 450))

    fundo_text = pygame.transform.scale(fundo_text, (936, 324))

    frames_fundo = [pygame.transform.scale(f, (larg, altura)) for f in frames_fundo]

    sprites = [solo_botao, multi_botao, solver_botao]

    pygame.font.init()
    # Fonte do mine :3
    fonte = pygame.font.Font(r"Simulations\Images\Font\Minecraftia-Regular.ttf", 40)
    fonte_pequena = pygame.font.Font(
        r"Simulations\Images\Font\Minecraftia-Regular.ttf", 20
    )
    fonte_bem_pequena = pygame.font.Font(
        r"Simulations\Images\Font\Minecraftia-Regular.ttf", 12
    )

    # Textos para renderizarmos depois
    # Texto solo
    str_texto_solo = "Essa simulação visa analisar como que os canais de um neurônio isolado se comportam a um determinado estimulo ou situação (pensando nas sinapses). Para avaliar isso, temos os seguintes comandos: 'Enter' para dar o estímulo, 'UpArrow' e 'DownArrow' para aumentar ou diminuir a intensidade do estimulo, 'Space' para receber uma corrente sináptica estimulante, 'B' para receber uma corrente sináptica inibitória, 'RightArrow' e 'LeftArrow' para controlar o intervalo de tempo estimulante do modo pulso_cronometrado, 'T' para iniciar o modo pulso_cronometrado (que dura 10 ms) e, por fim, 'Escape' sai da simulação. Para fins didáticos, os círculos amarelos são íons de K, vermelho são íons Na e os verdes são íons Ca, com Na<K<Ca"

    str_texto_solo = justificar_texto(str_texto_solo, 70)
    texto_solo = fonte_bem_pequena.render(str_texto_solo, True, (0, 0, 0))

    # Textos para EEG
    str_texto_multi = "Esse simulação tenta analisar como que vários neurônios se comportam caso estejam ligados por um grafo. Nessa simulação só existe alguns comando: o 'Enter' para estimular o neurônio inicial e o 'UpArrow' e o 'DownArrow' para aumentar ou diminuir a intensidade do estímulo. Nessa simulação, a esquerda teremos todos os potenciais de membrana dos neurônios sobrepostos e a direita há um Eletroencefalograma (EEG) sintético que avalia o somatório das correntes sinápticas. Para sair, pressione 'Escape'"

    str_texto_multi = justificar_texto(str_texto_multi, 75)
    texto_multi = fonte_bem_pequena.render(str_texto_multi, True, (0, 0, 0))

    # Textos para solver
    str_texto_solver = "Essa parte é uma tentativa de construir um algoritmo capaz de ler exames de EEG. Imagine que tenhamos uma leitura de um exame, ele não consiguirá contar a história de quem o formou. Contudo, esse algoritmo recebe uma biblioteca de sinais purificados e, com ajuda de um algoritmo baseado em Série de Fourier, tenta prever qual a composição do sinal baseado em sua forma. Na próxima tela há um braço com 8 botões apertáveis, você pode escolher uma composição de dedos (5 botões escrito 'Finger') e a região de medição (3 quadrados amarelos, só um é selecionável por vez e você não pode prosseguir se não escolher nenhum)"

    str_texto_solver = justificar_texto(str_texto_solver, 75)
    texto_solver = fonte_bem_pequena.render(str_texto_solver, True, (0, 0, 0))

    """Quando eu aperto um botão, ele precisa sair de dois loops ao mesmo tempo.
    Para isso, vou usar try e dar raise em um StopIteration quando um botão for
    apertado."""

    try:
        while True:
            # Fundinho
            tela.fill("cyan")

            # desenha o GIF
            tela.blit(frames_fundo[frame_i], (0, 0))

            # troca frame
            frame_i = (frame_i + 1) % len(frames_fundo)

            mx, my = pygame.mouse.get_pos()

            # tempo
            t += 0.05
            if t > 2 * math.pi:
                t = 0

            if screen == "Menu":
                # oscilação vertical
                y_offset = math.sin(t) * 5  # 10 = intensidade

                texto = fonte.render("SiGraNe", True, (255, 128, 128))
                rect = texto.get_rect(center=(larg // 2, altura // 4 + y_offset))
                tela.blit(texto, rect)

                texto = fonte_pequena.render(
                    "(Simulação de um Gradiente de Neurônio)", True, (255, 128, 128)
                )
                rect = texto.get_rect(center=(larg // 2, altura // 4 + 50 + y_offset))
                tela.blit(texto, rect)

                for i in range(0, 3):
                    rect_imagem = solo_botao.get_rect(
                        center=(
                            larg // 2 + 175 * (2 * i - 1 - 3 * (i // 2)),
                            altura // 2 + 120 * (i // 2),
                        )
                    )

                    # Interagindo com o mouse
                    if is_in(mx, my, rect_imagem):
                        sprites[i].set_alpha(128)
                    else:
                        sprites[i].set_alpha(255)

                    tela.blit(sprites[i], rect_imagem)

                    # Veja se ele apertou o mouse
                    click = pygame.mouse.get_just_pressed()[0]
                    if is_in(mx, my, rect_imagem) and click:
                        if i == 0:
                            screen = "Exp_mono_neuron"

                        elif i == 1:
                            screen = "Exp_multi_neuron"

                        elif i == 2:
                            screen = "Exp_solver_neuron"

                texto = fonte_pequena.render(
                    "Pressione 'Escape' para sair", True, (255, 128, 128)
                )
                rect = texto.get_rect(
                    center=(
                        larg - texto.get_width() // 2 - 25,
                        altura - 50 + y_offset,
                    )
                )
                tela.blit(texto, rect)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        break

                if kb.is_pressed("escape"):
                    raise StopAll

            elif screen == "Exp_mono_neuron":
                # Sprite do fundo
                rect_imagem = fundo_text.get_rect(center=(larg // 2, altura // 2))
                tela.blit(fundo_text, rect_imagem)

                # Desenhando texto
                rect = texto_solo.get_rect(center=(larg // 2, altura // 2))
                tela.blit(texto_solo, rect)

                # Interagindo com o mouse (seta direita)
                rect_imagem = arrow_botaoR.get_rect(
                    center=(3 * (larg // 3) - 150, 6 * (altura // 7))
                )

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoR.set_alpha(128)
                    if click:
                        pygame.quit()

                        # Abre a simulação do neuronio sozinho como subprocesso
                        base = os.path.dirname(__file__)

                        arquivo = os.path.join(base, r"Simulations\prototype_2.py")

                        subprocess.run(["python", arquivo])

                        raise StopIteration
                else:
                    arrow_botaoR.set_alpha(255)

                tela.blit(arrow_botaoR, rect_imagem)

                # Interagindo com o mouse (seta esquerda)
                rect_imagem = arrow_botaoL.get_rect(center=(150, 6 * (altura // 7)))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoL.set_alpha(128)
                    if click:
                        screen = "Menu"
                else:
                    arrow_botaoL.set_alpha(255)

                tela.blit(arrow_botaoL, rect_imagem)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        break

                if kb.is_pressed("escape"):
                    raise StopAll

            elif screen == "Exp_multi_neuron":
                # Sprite do fundo
                rect_imagem = fundo_text.get_rect(center=(larg // 2, altura // 2))
                tela.blit(fundo_text, rect_imagem)

                # Desenhando texto
                rect = texto_multi.get_rect(center=(larg // 2, altura // 2))
                tela.blit(texto_multi, rect)

                # Interagindo com o mouse (seta direita)
                rect_imagem = arrow_botaoR.get_rect(
                    center=(3 * (larg // 3) - 150, 6 * (altura // 7))
                )

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoR.set_alpha(128)
                    if click:
                        pygame.quit()
                        # Abre o EEG como um subprocesso

                        base = os.path.dirname(__file__)

                        arquivo = os.path.join(base, r"Simulations\simulation_8.py")

                        subprocess.run(["python", arquivo])

                        raise StopIteration
                else:
                    arrow_botaoR.set_alpha(255)

                tela.blit(arrow_botaoR, rect_imagem)

                # Interagindo com o mouse (seta esquerda)
                rect_imagem = arrow_botaoL.get_rect(center=(150, 6 * (altura // 7)))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoL.set_alpha(128)
                    if click:
                        screen = "Menu"
                else:
                    arrow_botaoL.set_alpha(255)

                tela.blit(arrow_botaoL, rect_imagem)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        break

                if kb.is_pressed("escape"):
                    raise StopAll

            elif screen == "Exp_solver_neuron":
                # Sprite do fundo
                rect_imagem = fundo_text.get_rect(center=(larg // 2, altura // 2))
                tela.blit(fundo_text, rect_imagem)

                # Desenhando texto
                rect = texto_solver.get_rect(center=(larg // 2, altura // 2))
                tela.blit(texto_solver, rect)

                # Interagindo com o mouse (seta direita)
                rect_imagem = arrow_botaoR.get_rect(
                    center=(3 * (larg // 3) - 150, 6 * (altura // 7))
                )

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoR.set_alpha(128)
                    if click:
                        # Lista para o solver
                        lista_dedos = [0, 0, 0, 0, 0]
                        area = None
                        screen = "Select_solver_neuron"
                else:
                    arrow_botaoR.set_alpha(255)

                tela.blit(arrow_botaoR, rect_imagem)

                # Interagindo com o mouse (seta esquerda)
                rect_imagem = arrow_botaoL.get_rect(center=(150, 6 * (altura // 7)))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoL.set_alpha(128)
                    if click:
                        screen = "Menu"
                else:
                    arrow_botaoL.set_alpha(255)

                tela.blit(arrow_botaoL, rect_imagem)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        break

                if kb.is_pressed("escape"):
                    raise StopAll

            elif screen == "Select_solver_neuron":
                # Interagindo com o braço
                rect_imagem = Arm_png.get_rect(
                    center=(Arm_png.get_width() / 2 - 85, altura // 2 - 100)
                )
                tela.blit(Arm_png, rect_imagem)

                # Dedao
                rect_imagem = finger_botao.get_rect(center=(467 + 30, 236))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    finger_botao.set_alpha(128)
                    if click:
                        lista_dedos[0] = 1 - lista_dedos[0]
                else:
                    finger_botao.set_alpha(255)

                if lista_dedos[0] == 1:
                    finger_botao.set_alpha(128)

                tela.blit(finger_botao, rect_imagem)

                # indicador
                rect_imagem = finger_botao.get_rect(center=(525 + 30, 311))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    finger_botao.set_alpha(128)
                    if click:
                        lista_dedos[1] = 1 - lista_dedos[1]
                else:
                    finger_botao.set_alpha(255)

                if lista_dedos[1] == 1:
                    finger_botao.set_alpha(128)

                tela.blit(finger_botao, rect_imagem)

                # Dedo médio
                rect_imagem = finger_botao.get_rect(center=(513 + 30, 345))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    finger_botao.set_alpha(128)
                    if click:
                        lista_dedos[2] = 1 - lista_dedos[2]
                else:
                    finger_botao.set_alpha(255)

                if lista_dedos[2] == 1:
                    finger_botao.set_alpha(128)

                tela.blit(finger_botao, rect_imagem)

                # anelar
                rect_imagem = finger_botao.get_rect(center=(489 + 30, 373))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    finger_botao.set_alpha(128)
                    if click:
                        lista_dedos[3] = 1 - lista_dedos[3]
                else:
                    finger_botao.set_alpha(255)

                if lista_dedos[3] == 1:
                    finger_botao.set_alpha(128)

                tela.blit(finger_botao, rect_imagem)

                # mindinho
                rect_imagem = finger_botao.get_rect(center=(430 + 30, 396))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    finger_botao.set_alpha(128)
                    if click:
                        lista_dedos[4] = 1 - lista_dedos[4]
                else:
                    finger_botao.set_alpha(255)

                if lista_dedos[4] == 1:
                    finger_botao.set_alpha(128)

                tela.blit(finger_botao, rect_imagem)

                # Interagindo com o mouse (seta direita)
                rect_imagem = arrow_botaoR.get_rect(
                    center=(3 * (larg // 3) - 150, 6 * (altura // 7))
                )

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoR.set_alpha(128)
                    if click and area is not None:
                        # Calculando o fragmento e a composição
                        resultado, fragmento = fft.main(lista_dedos, area)

                        # Criando um arquivo para o subprocesso poder ler
                        dados = {
                            "resultado": resultado["reconstrução"].tolist(),
                            "fragmento": fragmento.tolist(),
                        }

                        with open("dados.json", "w") as f:
                            json.dump(dados, f)

                        # Plotando resultado para se bonitinho :3 (se eu plotar dentro do pygame, o tamanho da janela zoa)
                        base = os.path.dirname(__file__)

                        arquivo = os.path.join(base, r"Simulations\plot_frag.py")

                        subprocess.run(["python", arquivo])

                        screen = "Result_solver_neuron"
                    elif click and area is None:
                        print("selecione uma das áreas em amarelo")
                else:
                    arrow_botaoR.set_alpha(255)

                tela.blit(arrow_botaoR, rect_imagem)

                # Interagindo com o mouse (seta esquerda)
                rect_imagem = arrow_botaoL.get_rect(center=(150, 6 * (altura // 7)))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoL.set_alpha(128)
                    if click:
                        screen = "Exp_solver_neuron"
                else:
                    arrow_botaoL.set_alpha(255)

                tela.blit(arrow_botaoL, rect_imagem)

                # Interagindo com area 1
                rect_imagem = amarelo_botao.get_rect(center=(51, 72 + 20))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    amarelo_botao.set_alpha(128)
                    if click:
                        area = 0
                else:
                    amarelo_botao.set_alpha(64)

                if area == 0:
                    amarelo_botao.set_alpha(128)

                tela.blit(amarelo_botao, rect_imagem)

                # Interagindo com area 2
                rect_imagem = amarelo_botao.get_rect(center=(193, 198))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    amarelo_botao.set_alpha(128)
                    if click:
                        area = 300
                else:
                    amarelo_botao.set_alpha(64)

                if area == 300:
                    amarelo_botao.set_alpha(128)

                tela.blit(amarelo_botao, rect_imagem)

                # Interagindo com area 3
                rect_imagem = amarelo_botao.get_rect(center=(365, 283))

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    amarelo_botao.set_alpha(128)
                    if click:
                        area = 600
                else:
                    amarelo_botao.set_alpha(64)

                if area == 600:
                    amarelo_botao.set_alpha(128)

                tela.blit(amarelo_botao, rect_imagem)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        break

                if kb.is_pressed("escape"):
                    raise StopAll

            elif screen == "Result_solver_neuron":
                texto = ""

                texto += "Score: " + str(resultado["score"]) + "\n"
                texto += "Erro: " + str(resultado["erro"]) + "\n"
                texto += "=====================================================" + "\n"
                texto += "Componentes estimadas" + "\n"
                texto += componentes_reais(resultado, "Estimada")
                texto += "=====================================================" + "\n"
                texto += "Componentes reais" + "\n"
                texto += componentes_reais(lista_dedos, "Reais")

                texto_resultado = fonte_bem_pequena.render(texto, True, (0, 0, 0))

                # Desenhando fundo do texto
                rect = fundo_text.get_rect(center=(larg // 2, altura // 2))
                tela.blit(fundo_text, rect)

                # Desenhando texto
                rect = texto_resultado.get_rect(center=(larg // 2 + 10, altura // 2))
                tela.blit(texto_resultado, rect)

                # Interagindo com o mouse (seta direita)
                rect_imagem = arrow_botaoR.get_rect(
                    center=(3 * (larg // 3) - 150, 6 * (altura // 7))
                )

                if is_in(mx, my, rect_imagem):
                    click = pygame.mouse.get_just_pressed()[0]
                    arrow_botaoR.set_alpha(128)
                    if click:
                        screen = "Menu"
                else:
                    arrow_botaoR.set_alpha(255)

                tela.blit(arrow_botaoR, rect_imagem)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        break

                if kb.is_pressed("escape"):
                    raise StopAll

            pygame.display.flip()
            clock.tick(60)
    except StopIteration:
        base = os.path.dirname(__file__)

        arquivo = os.path.join(base, "screen.py")

        subprocess.run(["python", arquivo])
    except StopAll:
        pygame.quit()


if __name__ == "__main__":
    main()
