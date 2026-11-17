
import plotly.graph_objects as go


def criar_mapa_neural(df):

    ocupacao = (
        df.groupby(
            ["neuronio_linha", "neuronio_coluna"]
        )
        .size()
        .reset_index(name="quantidade")
    )

    matriz = [[0 for _ in range(10)] for _ in range(10)]

    for _, registro in ocupacao.iterrows():

        linha = int(registro["neuronio_linha"])
        coluna = int(registro["neuronio_coluna"])

        matriz[linha][coluna] = registro["quantidade"]

    figura = go.Figure(
        data=go.Heatmap(
            z=matriz,
            colorscale="Viridis",
            colorbar=dict(title="Municípios")
        )
    )

    figura.update_layout(
        title="Mapa de ocupação da rede SOM",
        xaxis_title="Coluna do neurônio",
        yaxis_title="Linha do neurônio",
        # Mesma orientação dos mapas por indicador: linha 0 em cima
        yaxis=dict(autorange="reversed", scaleanchor="x", dtick=1),
        xaxis=dict(dtick=1),
        height=560
    )

    return figura
