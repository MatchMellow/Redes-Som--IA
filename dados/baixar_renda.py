
import csv
import re
from pathlib import Path

PASTA = Path(__file__).parent

ARQUIVO_ENTRADA = PASTA / "renda_sidra.csv"
ARQUIVO_SAIDA = PASTA / "renda_per_capita.csv"


def baixar_renda():

    print("Lendo tabela do IBGE...")

    registros = []

    with open(
        ARQUIVO_ENTRADA,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        leitor = csv.reader(arquivo, delimiter=";")

        for linha in leitor:

            if len(linha) < 4:
                continue

            codigo = linha[0].strip().strip('"')
            municipio = linha[1].strip().strip('"')
            valor = linha[3].strip().strip('"')

            # Aceitar somente códigos municipais de 7 dígitos
            if not re.fullmatch(r"\d{7}", codigo):
                continue

            try:
                renda = float(
                    valor.replace(".", "").replace(",", ".")
                )
            except ValueError:
                continue

            registros.append({
                "id_municipio": codigo,
                "nome_municipio": municipio,
                "renda_per_capita": renda
            })

    if not registros:
        raise ValueError(
            "Nenhum município foi encontrado no arquivo."
        )

    resultado = {}

    for registro in registros:

        codigo = registro["id_municipio"]

        if codigo in resultado:
            raise ValueError(
                f"Código municipal duplicado: {codigo}"
            )

        resultado[codigo] = registro

    registros = list(resultado.values())

    with open(
        ARQUIVO_SAIDA,
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        campos = [
            "id_municipio",
            "nome_municipio",
            "renda_per_capita"
        ]

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos
        )

        escritor.writeheader()
        escritor.writerows(registros)

    print("\n===== RENDA MUNICIPAL =====")

    print("Municípios encontrados:", len(registros))

    print("Arquivo gerado:", ARQUIVO_SAIDA)

    print("\nPrimeiros municípios:")

    for registro in registros[:5]:
        print(registro)


if __name__ == "__main__":
    baixar_renda()