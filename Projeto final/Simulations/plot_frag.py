import matplotlib

matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import numpy as np
import json


with open("dados.json") as f:
    dados = json.load(f)


fragmento = np.array(dados["fragmento"])
resultado = np.array(dados["resultado"])

# Plotando resultado para se bonitinho :3
plt.plot(fragmento, label="Sinal original")
plt.plot(
    resultado,
    linestyle="--",
    label="Reconstrução",
)
plt.title("fragmento artificial (feche essa janela para voltar ao menu)")
plt.legend()
plt.grid()
plt.show()
