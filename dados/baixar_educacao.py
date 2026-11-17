
import pandas as pd
from pathlib import Path


# Localização dos arquivos
PASTA = Path(__file__).parent

ARQUIVO_ORIGINAL = PASTA / "educacao_ibge.csv"

ARQUIVO_FINAL = PASTA / "educacao.csv"


def baixar_educacao():

    print("Processando dados de educação do IBGE...")

    # O arquivo possui linhas de identificação antes do cabeçalho.
    df = pd.read_csv(
        ARQUIVO_ORIGINAL,
        sep=";",
        skiprows=5,
        dtype={"Cód.": str},
        encoding="utf-8-sig"
    )

    # Limpar nomes das colunas
    df.columns = df.columns.str.strip()

    print("Colunas encontradas:", df.columns.tolist())

    # Conferir colunas necessárias
    necessarias = [
        "Cód.",
        "Município",
        "Idade",
        "Total"
    ]

    for coluna in necessarias:
        if coluna not in df.columns:
            raise ValueError(
                f"Coluna não encontrada: {coluna}"
            )

    # Selecionar pessoas de 15 anos ou mais:
    # Total de idade e Total de sexo/cor ou raça
    df = df[
        df["Idade"].astype(str).str.strip() == "Total"
    ].copy()

    # Organizar os dados
    resultado = pd.DataFrame()

    resultado["id_municipio"] = (
        df["Cód."]
        .astype(str)
        .str.strip()
    )

    resultado["nome_municipio"] = (
        df["Município"].astype(str).str.strip()
    )

    # Converter porcentagem para número
    resultado["educacao"] = pd.to_numeric(
        df["Total"]
        .astype(str)
        .str.replace(",", ".", regex=False),
        errors="coerce"
    )

    # Remover dados inválidos
    resultado = resultado.dropna(
        subset=["educacao"]
    )

    # Conferir códigos duplicados
    if resultado["id_municipio"].duplicated().any():
        raise ValueError(
            "Existem municípios duplicados. "
            "Confira os filtros da tabela do IBGE."
        )

    # Salvar CSV final
    resultado.to_csv(
        ARQUIVO_FINAL,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n===== EDUCAÇÃO CONCLUÍDA =====")

    print("Municípios encontrados:", len(resultado))

    print("Arquivo gerado:", ARQUIVO_FINAL)

    print("\nPrimeiros municípios:")

    print(resultado.head(5).to_string(index=False))


if __name__ == "__main__":
    baixar_educacao()
