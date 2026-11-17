import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _tamanho_grade(df):
    # Tamanho do quadro de neurônios, deduzido dos resultados
    linhas = int(df["neuronio_linha"].max()) + 1
    colunas = int(df["neuronio_coluna"].max()) + 1
    return max(linhas, 10), max(colunas, 10)


def _matriz_media(df, indicador):
    # Média do indicador em cada neurônio (plano de componentes).
    # Neurônios sem municípios (por exemplo, com filtro de UF) ficam vazios.
    linhas, colunas = _tamanho_grade(df)

    grupos = df.groupby(["neuronio_linha", "neuronio_coluna"])
    medias = grupos[indicador].mean()
    quantidades = grupos.size()
    exemplos = grupos["nome"].apply(
        lambda nomes: ", ".join(nomes.head(3))
    ) if "nome" in df.columns else None

    matriz = [[None] * colunas for _ in range(linhas)]
    textos = [[""] * colunas for _ in range(linhas)]

    for (linha, coluna), media in medias.items():
        linha, coluna = int(linha), int(coluna)
        matriz[linha][coluna] = media

        exemplo = (
            f"<br>Ex.: {exemplos[(linha, coluna)]}"
            if exemplos is not None else ""
        )
        textos[linha][coluna] = (
            f"Neurônio ({linha}, {coluna})"
            f"<br>Municípios: {quantidades[(linha, coluna)]}"
            f"{exemplo}"
        )

    return matriz, textos


def mapa_indicador(df, indicador, nome_indicador=None):
    # Quadro 10x10 pintado pela média do indicador em cada neurônio.
    # Mostra onde, no mapa aprendido, ficam os valores altos e baixos.
    nome = nome_indicador or indicador
    matriz, textos = _matriz_media(df, indicador)

    figura = go.Figure(
        data=go.Heatmap(
            z=matriz,
            text=textos,
            hovertemplate=(
                "%{text}<br>Média: %{z:,.3f}<extra></extra>"
            ),
            colorscale="Viridis",
            colorbar=dict(title="Média")
        )
    )

    figura.update_layout(
        title=f"Média de {nome} em cada neurônio",
        xaxis_title="Coluna do neurônio",
        yaxis_title="Linha do neurônio",
        yaxis=dict(autorange="reversed", scaleanchor="x", dtick=1),
        xaxis=dict(dtick=1),
        height=560
    )

    return figura


def comparar_indicadores(df, indicadores, nomes=None):
    # Os planos de componentes de todos os indicadores lado a lado.
    # Indicadores com desenhos parecidos andam juntos nos dados.
    nomes = nomes or {}
    total = len(indicadores)
    colunas_grade = 3
    linhas_grade = math.ceil(total / colunas_grade)

    figura = make_subplots(
        rows=linhas_grade,
        cols=colunas_grade,
        subplot_titles=[nomes.get(i, i) for i in indicadores],
        horizontal_spacing=0.04,
        vertical_spacing=0.1
    )

    for posicao, indicador in enumerate(indicadores):
        matriz, textos = _matriz_media(df, indicador)
        linha = posicao // colunas_grade + 1
        coluna = posicao % colunas_grade + 1

        figura.add_trace(
            go.Heatmap(
                z=matriz,
                text=textos,
                hovertemplate=(
                    f"<b>{nomes.get(indicador, indicador)}</b><br>"
                    "%{text}<br>Média: %{z:,.3f}<extra></extra>"
                ),
                colorscale="Viridis",
                showscale=False
            ),
            row=linha,
            col=coluna
        )

    figura.update_yaxes(autorange="reversed", showticklabels=False)
    figura.update_xaxes(showticklabels=False)

    figura.update_layout(
        title="Todos os indicadores no mesmo mapa (cada um na sua escala)",
        height=330 * linhas_grade + 60
    )

    return figura
