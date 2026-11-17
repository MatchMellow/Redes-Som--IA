
import pandas as pd
import unicodedata
import re
from pathlib import Path


PASTA = Path(__file__).parent

ARQUIVO_MUNICIPIOS = PASTA / "municipios.csv"
ARQUIVO_IDHM = PASTA / "idhm.csv"
ARQUIVO_SAIDA = PASTA / "idhm_integrado.csv"


def normalizar_nome(nome):

    nome = str(nome).strip().upper()

    nome = unicodedata.normalize(
        "NFKD", nome
    ).encode("ASCII", "ignore").decode("ASCII")

    nome = re.sub(r"\s+", " ", nome)

    return nome


def executar():

    print("Carregando municípios...")

    municipios = pd.read_csv(
        ARQUIVO_MUNICIPIOS,
        dtype=str
    )

    print("Carregando IDHM...")

    idhm = pd.read_csv(
        ARQUIVO_IDHM,
        sep=None,
        engine="python",
        dtype=str
    )

    # Limpar nomes das colunas
    municipios.columns = municipios.columns.str.strip()
    idhm.columns = idhm.columns.str.strip()

    # Preparar chaves de integração
    municipios["chave_nome"] = (
        municipios["nome"].apply(normalizar_nome)
    )

    municipios["chave_uf"] = (
        municipios["uf"].str.strip().str.upper()
    )

    idhm["chave_nome"] = (
        idhm["municipio"].apply(normalizar_nome)
    )

    idhm["chave_uf"] = (
        idhm["uf"].str.strip().str.upper()
    )

    # Converter IDHM para número
    idhm["idhm_2010"] = pd.to_numeric(
        idhm["IDHM 2010"]
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    # Verificar duplicidades
    if idhm.duplicated(
        subset=["chave_nome", "chave_uf"]
    ).any():

        raise ValueError(
            "Existem municípios duplicados no arquivo IDHM."
        )

    # Selecionar somente as informações necessárias
    idhm = idhm[
        ["chave_nome", "chave_uf", "idhm_2010"]
    ]

    # Integrar com os códigos oficiais
    resultado = municipios.merge(
        idhm,
        on=["chave_nome", "chave_uf"],
        how="left",
        validate="one_to_one"
    )

    # Conferir cobertura
    encontrados = resultado["idhm_2010"].notna().sum()
    ausentes = resultado["idhm_2010"].isna().sum()

    print("\n===== RESULTADO DA INTEGRAÇÃO =====")

    print("Municípios na base:", len(resultado))
    print("IDHM encontrado:", encontrados)
    print("IDHM ausente:", ausentes)

    if ausentes > 0:

        print("\nMunicípios sem correspondência:")

        print(
            resultado.loc[
                resultado["idhm_2010"].isna(),
                ["id_municipio", "nome", "uf"]
            ].head(20)
        )

    # Gerar arquivo final
    resultado = resultado[
        ["id_municipio", "nome", "uf", "idhm_2010"]
    ]

    resultado.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nArquivo gerado:", ARQUIVO_SAIDA)


if __name__ == "__main__":
    executar()
