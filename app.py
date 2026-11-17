
import streamlit as st
import pandas as pd

from pathlib import Path

from visualizacoes.mapas import criar_mapa_neural
from visualizacoes.graficos import (
    mapa_indicador,
    comparar_indicadores
)


PASTA = Path(__file__).parent
PASTA_DADOS = PASTA / "dados"

ARQUIVO_RESULTADO = (
    PASTA_DADOS / "resultados_som.csv"
)

st.set_page_config(
    page_title="SOM-BRASIL",
    page_icon="🧠",
    layout="wide"
)

# Identidade do projeto
st.title("🧠 SOM-BRASIL")

st.subheader(
    "Mapa socioeconômico dos municípios brasileiros"
)

st.write(
    "Sistema de inteligência artificial baseado "
    "em mapas auto-organizáveis (SOM)."
)

st.divider()

# Indicadores do projeto
# (nomes iguais às colunas de dados/indicadores_completos.csv)
INDICADORES = {
    "pib_per_capita": "PIB per capita (2022)",
    "renda_per_capita": "Renda per capita (2022)",
    "taxa_alfabetizacao": "Educação: alfabetização % (2022)",
    "idhm": "IDHM (2010)",
    "taxa_obitos": "Saúde: óbitos por mil hab.",
    "populacao": "População (2022)"
}

st.header("Indicadores socioeconômicos")

colunas = st.columns(3)

disponiveis = []

if ARQUIVO_RESULTADO.exists():

    df = pd.read_csv(
        ARQUIVO_RESULTADO,
        dtype={"id_municipio": str}
    )

    for coluna in INDICADORES:

        if coluna in df.columns:

            valores = pd.to_numeric(
                df[coluna],
                errors="coerce"
            )

            if valores.notna().any():
                disponiveis.append(coluna)

for indice, (coluna, nome) in enumerate(
    INDICADORES.items()
):

    posicao = indice % 3

    if coluna in disponiveis:

        valor = (
            df[coluna]
            .notna()
            .sum()
        )

        colunas[posicao].metric(
            nome,
            f"{valor:,}".replace(",", "."),
            "Municípios com dados"
        )

    else:

        colunas[posicao].metric(
            nome,
            "Pendente",
            "Aguardando coleta"
        )

st.divider()

# Verificar treinamento
if not ARQUIVO_RESULTADO.exists():

    st.warning(
        "Ainda não existe um treinamento concluído."
    )

    st.info(
        "Depois de preparar os indicadores, execute "
        "'python treinamento.py' no terminal."
    )

    st.stop()

# Verificar colunas necessárias
colunas_obrigatorias = [
    "neuronio_linha",
    "neuronio_coluna",
    "id_municipio"
]

faltantes = [
    coluna for coluna in colunas_obrigatorias
    if coluna not in df.columns
]

if faltantes:

    st.error(
        f"Colunas ausentes nos resultados: {faltantes}"
    )

    st.stop()

# Filtros
st.sidebar.header("Filtros")

df["id_municipio"] = (
    df["id_municipio"].astype(str).str.zfill(7)
)

if "uf" in df.columns:

    ufs = sorted(
        df["uf"].dropna().unique().tolist()
    )

    opcoes_uf = ["Todos"] + ufs

    uf_selecionada = st.sidebar.selectbox(
        "Estado",
        opcoes_uf
    )

    if uf_selecionada != "Todos":

        df = df[
            df["uf"] == uf_selecionada
        ]

else:

    st.sidebar.info(
        "Filtro por estado indisponível."
    )

# Seleção de indicador
indicadores_visiveis = [
    coluna for coluna in disponiveis
    if coluna in df.columns
]

if not indicadores_visiveis:

    st.warning(
        "Nenhum indicador numérico disponível."
    )

    st.stop()

indicador = st.sidebar.selectbox(
    "Indicador para visualizar",
    indicadores_visiveis,
    format_func=lambda x: INDICADORES.get(x, x)
)

# Resumo
st.header("Resumo do treinamento")

c1, c2, c3 = st.columns(3)

c1.metric(
    "Municípios analisados",
    len(df)
)

c2.metric(
    "Neurônios disponíveis",
    "100"
)

c3.metric(
    "Indicadores disponíveis",
    len(indicadores_visiveis)
)

st.divider()

# Mapa neural
st.header("Mapa de organização neural")

st.caption(
    "Quantos municípios cada neurônio representa. "
    "Este mapa não depende do indicador escolhido."
)

st.plotly_chart(
    criar_mapa_neural(df),
    width="stretch"
)

# Plano de componentes do indicador escolhido
nome_indicador = INDICADORES.get(indicador, indicador)

st.header(f"{nome_indicador} no mapa")

st.caption(
    "Cada casa é um neurônio, pintada com a média do indicador "
    "nos municípios que ele representa. Passe o mouse para ver detalhes."
)

st.plotly_chart(
    mapa_indicador(df, indicador, nome_indicador),
    width="stretch"
)

# Comparação entre indicadores
st.header("Comparação entre indicadores")

st.caption(
    "O mesmo mapa pintado por cada indicador. Desenhos parecidos "
    "indicam indicadores que andam juntos nos dados (por exemplo, "
    "renda, alfabetização e IDHM); desenhos diferentes indicam "
    "que o indicador traz informação própria."
)

st.plotly_chart(
    comparar_indicadores(df, indicadores_visiveis, INDICADORES),
    width="stretch"
)

# Tabela
st.header("Municípios analisados")

st.dataframe(
    df,
    width="stretch"
)
