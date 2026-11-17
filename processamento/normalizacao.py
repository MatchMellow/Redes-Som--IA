
import pandas as pd


def normalizar_dados(df, colunas):

    resultado = df.copy()
    parametros = {}

    for coluna in colunas:

        minimo = resultado[coluna].min()
        maximo = resultado[coluna].max()

        parametros[coluna] = {
            "minimo": float(minimo),
            "maximo": float(maximo)
        }

        if maximo == minimo:
            resultado[coluna] = 0.0

        else:
            resultado[coluna] = (
                resultado[coluna] - minimo
            ) / (maximo - minimo)

    return resultado, parametros
