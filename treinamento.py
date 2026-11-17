
import numpy as np
import pandas as pd
from pathlib import Path

from modelos.rede_som import RedeSOM
from processamento.normalizacao import normalizar_dados


PASTA = Path(__file__).parent
PASTA_DADOS = PASTA / "dados"

# Base gerada por dados/integrar_dados.py
ARQUIVO_INDICADORES = PASTA_DADOS / "indicadores_completos.csv"
ARQUIVO_MUNICIPIOS = PASTA_DADOS / "municipios.csv"
ARQUIVO_RESULTADO = PASTA_DADOS / "resultados_som.csv"

# Indicadores usados no treinamento (nomes reais das colunas).
# Todos são obrigatórios: se algum faltar, o treinamento para com erro,
# em vez de seguir em silêncio sem ele.
INDICADORES = [
    "pib_per_capita",      # Economia: PIB por habitante (2022)
    "renda_per_capita",    # Renda: rendimento domiciliar per capita (Censo 2022)
    "taxa_alfabetizacao",  # Educação: % de alfabetizados (Censo 2022)
    "idhm",                # Desenvolvimento humano: IDHM (Atlas 2010)
    "taxa_obitos",         # Saúde: óbitos por 1.000 habitantes (DATASUS)
    "populacao"            # Tamanho: população (Censo 2022)
]

# Indicadores com valores muito extremos, que passam por logaritmo antes
# da normalização. Sem isso, a escala de 0 a 1 é dominada por poucas
# cidades enormes e quase todos os municípios ficam espremidos perto de 0
# (população: 95% abaixo de 0,01; PIB per capita: 95% abaixo de 0,1).
# O logaritmo preserva a ordem e passa a comparar ordens de grandeza.
# Os valores originais continuam no arquivo de resultados.
INDICADORES_LOG = [
    "pib_per_capita",
    "populacao"
]

# Configuração da rede
LINHAS = 10
COLUNAS = 10
EPOCAS = 20
TAXA_APRENDIZADO = 0.5
SEMENTE = 42


def carregar_dados():

    print("Carregando indicadores...")

    if not ARQUIVO_INDICADORES.exists():
        raise FileNotFoundError(
            "Arquivo indicadores.csv não encontrado."
        )

    df = pd.read_csv(
        ARQUIVO_INDICADORES,
        dtype={"id_municipio": str}
    )

    df["id_municipio"] = (
        df["id_municipio"].str.zfill(7)
    )

    # Recuperar nome e UF da base de municípios
    if ARQUIVO_MUNICIPIOS.exists():

        municipios = pd.read_csv(
            ARQUIVO_MUNICIPIOS,
            dtype={"id_municipio": str}
        )

        municipios["id_municipio"] = (
            municipios["id_municipio"].str.zfill(7)
        )

        colunas_metadata = [
            coluna for coluna in ["nome", "uf"]
            if coluna not in df.columns
            and coluna in municipios.columns
        ]

        if colunas_metadata:

            df = df.merge(
                municipios[
                    ["id_municipio"] + colunas_metadata
                ],
                on="id_municipio",
                how="left",
                validate="one_to_one"
            )

    return df


def executar_treinamento():

    df = carregar_dados()

    indicadores = list(INDICADORES)

    faltantes = [
        coluna for coluna in indicadores
        if coluna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Indicadores ausentes em {ARQUIVO_INDICADORES.name}: "
            f"{faltantes}. Rode dados/integrar_dados.py."
        )

    print("\nIndicadores usados:")

    for indicador in indicadores:
        print("-", indicador)

    # Converter os indicadores para números
    for coluna in indicadores:

        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce"
        )

    # Remover registros sem dados completos
    df = df.dropna(
        subset=indicadores
    ).copy()

    if len(df) == 0:
        raise ValueError(
            "Nenhum município possui todos os indicadores selecionados."
        )

    print("\nMunicípios disponíveis:", len(df))

    # Logaritmo nos indicadores extremos (só na cópia usada no treino)
    df_treino = df.copy()

    for coluna in INDICADORES_LOG:
        df_treino[coluna] = np.log10(df_treino[coluna])
        print(f"Logaritmo aplicado em: {coluna}")

    # Normalização (escala de 0 a 1)
    df_normalizado, parametros = normalizar_dados(
        df_treino,
        indicadores
    )

    dados = df_normalizado[
        indicadores
    ].values.tolist()

    # Criar rede SOM
    print("\nInicializando rede neural SOM...")

    rede = RedeSOM(
        linhas=LINHAS,
        colunas=COLUNAS,
        dimensoes=len(indicadores),
        taxa_aprendizado=TAXA_APRENDIZADO,
        epocas=EPOCAS,
        semente=SEMENTE
    )

    # Treinamento próprio
    print("\nIniciando treinamento...")

    rede.treinar(dados)

    # Identificar neurônio vencedor
    coordenadas = rede.mapear(dados)

    df["neuronio_linha"] = [
        posicao[0] for posicao in coordenadas
    ]

    df["neuronio_coluna"] = [
        posicao[1] for posicao in coordenadas
    ]

    # Registrar os indicadores utilizados
    df["indicadores_treinamento"] = ", ".join(
        indicadores
    )

    # Salvar resultados
    df.to_csv(
        ARQUIVO_RESULTADO,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n===== RESULTADO DO TREINAMENTO =====")

    print("Municípios treinados:", len(df))

    print("Indicadores utilizados:", len(indicadores))

    print("Neurônios:", LINHAS * COLUNAS)

    ocupados = df.groupby(
        ["neuronio_linha", "neuronio_coluna"]
    ).size()

    print(
        f"Neurônios com municípios: {len(ocupados)} | "
        f"municípios por neurônio: mín {ocupados.min()}, "
        f"mediana {int(ocupados.median())}, máx {ocupados.max()}"
    )

    print(
        "Erro médio: primeira época "
        f"{rede.historico_erros[0]:.6f} -> última época "
        f"{rede.historico_erros[-1]:.6f}"
    )

    print("\nIndicadores:", indicadores)

    print("\nArquivo salvo em:")
    print(ARQUIVO_RESULTADO)

    print("\nTreinamento concluído!")


if __name__ == "__main__":
    executar_treinamento()
