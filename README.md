<img src="Imagens cabeçalho/Cabecalho.png"/>

# Simulação de Gradiente de um neurônio (SiGraNe)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue">
  <img src="https://img.shields.io/badge/Área-Neurology%20Simulation-purple">
</p>

Projeto que visa simular neurônios para avaliar o fluxo de íons, comportamento em redes maiores e qualidade de reconstrução de sinal. Esse projeto é um trabalho de final do primeiro semestre da ILUM do aluno Vinícius Marianno De Marque Cutolo.

## Como executar:

Aqui vai o passo a passo de como executar esse programa:

1. Baixe o arquivo zip e extraia ele em uma pasta

2. Com o seu programa para executar o projeto (preferencialmente o VScode), vá em *file*, *Open folder* e selecione a pasta *Projeto final*.

3. Execute esse comando no terminal
``` sh
pip install -r requirements.txt
```

4. Execute o script *screen.py*

## Conteúdo:

<ul>
  <li> :file_folder: <b>Projeto final</b>: contém os scripts, arquivos e dados extras para rodar as simulações.</li>
    <ul>
      <li> :file_folder: <b>Data</b>: Armazena dados para as simulações.</li>
        <ul>
          <li> :card_file_box: <b>bib_eeg.pkl</b>: biblioteca dos sinais da simulação <b>FFT_functions</b></li>
        </ul>
      <li> :file_folder: <b>Simulation</b>: Guarda os scripts de cada simulação e as imagens usadas dentro dos projetos</li>
        <ul>
          <li> :file_folder: <b>Images</b>: Contém todos os sprites para o projeto</li>
          <li>:page_facing_up:<b>FFT_functions.py</b>: script de decomposição e reconstrução de sinais</li>
          <li>:page_facing_up:<b>plot_frag.py</b>: script que gera os gráficos da decomposição anterior</li>
          <li>:page_facing_up:<b>prototype_2.py</b>: script que simula um neurônio isolado, evidenciando os seus canais iônicos</li>
          <li>:page_facing_up:<b>simulation_8.py</b>: script de simulação de um eletroencefalograma sintético</li>
        </ul>
      <li> :page_facing_up: <b>screen.py</b>: Script principal, executa o menu das simulações.</li>
      <li> :spiral_notepad: <b>requirements.txt</b>: txt com todas as bibliotecas necessárias para rodar o projeto.</li>
    </ul>
  </ul>
</ul>

## XKCD relevante:

  ![img](https://imgs.xkcd.com/comics/curve_fitting.png)

## Professores avaliadores:

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/drcassar">
        <img src="https://avatars.githubusercontent.com/u/9871905?v=4" width="100px;" alt="Foto do Cassar no Github"/><br>
        <b>Prof. Dr. Daniel R. Cassar</b>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/jamesmalmeida">
        <img src="https://avatars.githubusercontent.com/u/108157661?v=4" width="100px;" alt="Foto do James no Github"/><br>
        <b>Prof. James Moraes de Almeida</b>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/llemos">
        <img src="https://avatars.githubusercontent.com/u/1894434?v=4" width="100px;" alt="Foto do Leandro no Github"/><br>
        <b>Prof. Leandro Nascimento Lemos</b>
      </a>
    </td>
  </tr>
</table>

## Aluno:

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/ViniCutolo">
        <img src="https://avatars.githubusercontent.com/u/271505502?s=80&v=4" width="100px;" alt="Foto do Vinícius no Github"/><br>
        <b>Vinícius Marianno de Marque Cutolo</b>
      </a>
    </td>
  </tr>
</table>

<img src="Imagens cabeçalho/Rodape.png"/>
