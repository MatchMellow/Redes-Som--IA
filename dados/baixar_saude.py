
import pandas as pd
from pathlib import Path


# Caminhos dos arquivos
PASTA = Path(__file__).parent

ARQUIVO_OBITOS = PASTA / "saude_obitos.csv"
ARQUIVO_INDICADORES = PASTA / "indicadores.csv"
ARQUIVO_SAIDA = PASTA / "saude.csv"


def baixar_saude():

    print("Carregando dados de saúde...")

    # Ler arquivo do DATASUS
    obitos = pd.read_csv(
        ARQUIVO_OBITOS,
        sep=";",
        encoding="utf-8-sig",
        dtype=str
    )

    # Limpar nomes das colunas
    obitos.columns = obitos.columns.str.strip()

    print("Colunas encontradas:", obitos.columns.tolist())

    # Identificar código municipal
    obitos["id_seis_digitos"] = (
        obitos["Município"]
        .str.extract(r"(\d{6})", expand=False)
    )

    # Converter quantidade de óbitos
    obitos["obitos_residencia"] = pd.to_numeric(
        obitos["Óbitos p/Residênc"],
        errors="coerce"
    )

    # Verificar dados inválidos
    obitos = obitos.dropna(
        subset=["id_seis_digitos", "obitos_residencia"]
    )

    # Verificar duplicações
    if obitos["id_seis_digitos"].duplicated().any():
        raise ValueError(
            "Existem municípios duplicados na tabela de saúde."
        )

    # Carregar nossa base municipal
    municipios = pd.read_csv(
        ARQUIVO_INDICADORES,
        dtype={"id_municipio": str}
    )

    # Criar chave de correspondência
    municipios["id_seis_digitos"] = (
        municipios["id_municipio"].str[:6]
    )

    # Relacionar os dados
    resultado = municipios[
        ["id_municipio", "id_seis_digitos"]
    ].merge(
        obitos[
            ["id_seis_digitos", "obitos_residencia"]
        ],
        on="id_seis_digitos",
        how="left",
        validate="one_to_one"
    )

    # Salvar resultado
    resultado = resultado[
        ["id_municipio", "obitos_residencia"]
    ]

    resultado.to_csv(
        ARQUIVO_SAIDA,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n===== RESULTADO DA SAÚDE =====")

    print("Municípios na base:", len(resultado))

    print(
        "Municípios com dados:",
        resultado["obitos_residencia"].notna().sum()
    )

    print(
        "Municípios sem correspondência:",
        resultado["obitos_residencia"].isna().sum()
    )

    print("\nPrimeiros registros:")
    print(resultado.head())

    print("\nArquivo gerado:", ARQUIVO_SAIDA)


if __name__ == "__main__":
    baixar_saude()
