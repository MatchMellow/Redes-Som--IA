import pandas as pd
from pathlib import Path

PASTA = Path(__file__).parent

ARQUIVO_MUNICIPIOS = PASTA / "municipios.csv"
ARQUIVO_OBITOS = PASTA / "saude_obitos.csv"
ARQUIVO_SAIDA = PASTA / "saude.csv"


def executar():
    print("Carregando municípios...")

    municipios = pd.read_csv(
        ARQUIVO_MUNICIPIOS,
        dtype={"id_municipio": str}
    )

    # Manter o código IBGE completo
    municipios["codigo_6"] = (
        municipios["id_municipio"].str[:6]
    )

    print("Carregando óbitos do DATASUS...")

    obitos = pd.read_csv(
        ARQUIVO_OBITOS,
        sep=";",
        dtype=str,
        encoding="utf-8-sig"
    )

    # Extrair os seis primeiros dígitos
    obitos["codigo_6"] = (
        obitos["Município"]
        .str.extract(r"^(\d{6})")[0]
    )

    obitos["obitos_residencia"] = pd.to_numeric(
        obitos["Óbitos p/Residênc"],
        errors="coerce"
    )

    # Filtrar apenas linhas que possuem código municipal válido (remove nulos, ignorados e totais)
    obitos = obitos.dropna(subset=["codigo_6"]).copy()

    # Conferir códigos duplicados apenas nos códigos válidos
    if obitos["codigo_6"].duplicated().any():
        raise ValueError(
            "Existem códigos municipais duplicados nos óbitos."
        )

    # Integrar pelos códigos municipais
    resultado = municipios.merge(
        obitos[["codigo_6", "obitos_residencia"]],
        on="codigo_6",
        how="left",
        validate="one_to_one"
    )

    # Remover coluna auxiliar
    resultado = resultado.drop(
        columns=["codigo_6"]
    )

    # Relatório
    print("\n===== RESULTADO =====")

    print("Municípios:", len(resultado))

    print(
        "Com registros de óbitos:",
        resultado["obitos_residencia"].notna().sum()
    )

    print(
        "Sem registros:",
        resultado["obitos_residencia"].isna().sum()
    )

    print("\nPrimeiros registros:")

    print(resultado.head(10))

    resultado.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nArquivo gerado:", ARQUIVO_SAIDA)


if __name__ == "__main__":
    executar()