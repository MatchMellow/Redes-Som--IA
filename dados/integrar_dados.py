import pandas as pd
import unicodedata
import re
from pathlib import Path


# Caminho da pasta 'dados' (a pasta deste próprio arquivo),
# para o script funcionar de qualquer diretório
PASTA = Path(__file__).parent


def ler_csv(nome, separador=None, **kwargs):
    caminho = PASTA / nome

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho}"
        )

    if separador:
        return pd.read_csv(
            caminho,
            sep=separador,
            encoding="utf-8-sig",
            **kwargs
        )

    return pd.read_csv(
        caminho,
        sep=None,
        engine="python",
        encoding="utf-8-sig",
        **kwargs
    )


def padronizar_id(coluna):
    return (
        coluna.astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.replace(r"\D", "", regex=True)
        .str.zfill(7)
    )


def normalizar_nome(nome):
    nome = str(nome).upper().strip()

    # Remover UF entre parênteses, quando existir
    nome = re.sub(r"\s*\([A-Z]{2}\)\s*$", "", nome)

    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(
        c for c in nome
        if not unicodedata.combining(c)
    )

    return re.sub(r"\s+", " ", nome).strip()


def chave_nome_idhm(nome):
    # Chave para cruzar nomes com o Atlas 2010: além de acentos,
    # ignora hífens, apóstrofos e as palavras de/do/da/dos/das/d.
    # Ex.: "Biritiba Mirim" e "Biritiba-Mirim" geram a mesma chave.
    nome = normalizar_nome(nome)
    nome = nome.replace("-", " ").replace("'", " ")
    nome = re.sub(r"\b(DE|DO|DA|DOS|DAS|D)\b", " ", nome)
    return re.sub(r"\s+", " ", nome).strip()


def converter_numero(coluna):
    return pd.to_numeric(
        coluna.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce"
    )


def conferir_duplicados(df, coluna, arquivo):
    duplicados = df[df[coluna].duplicated(keep=False)]

    if not duplicados.empty:
        raise ValueError(
            f"{arquivo} possui códigos municipais duplicados. "
            f"Exemplos:\n{duplicados.head()}"
        )


def executar():
    print("\n===== SOM-BRASIL: INTEGRAÇÃO COMPLETA =====")

    # 1. Municípios Base
    print("\n1. Carregando municípios...")
    municipios = ler_csv("municipios.csv")

    municipios.columns = (
        municipios.columns.str.replace("\ufeff", "")
        .str.strip().str.lower()
    )

    municipios["id_municipio"] = padronizar_id(
        municipios["id_municipio"]
    )

    municipios["nome"] = municipios["nome"].astype(str).str.strip()
    municipios["uf"] = municipios["uf"].astype(str).str.strip()

    conferir_duplicados(
        municipios, "id_municipio", "municipios.csv"
    )

    base = municipios[
        ["id_municipio", "nome", "uf"]
    ].copy()

    # 2 e 3. População (Censo 2022) e PIB per capita (2022)
    # Os dois vêm do mesmo arquivo, gerado por baixar_pib.py:
    #   pib_mil_reais  = PIB TOTAL do município (não usar no SOM)
    #   populacao_2022 = população do Censo 2022
    #   pib_per_capita = PIB total / população (já calculado)
    # Usamos a população do Censo 2022 (e não a estimativa de 2026 de
    # populacao.csv) para todos os indicadores serem do mesmo ano.
    # Os números já estão com ponto decimal, então basta pd.to_numeric
    # (converter_numero apagaria o ponto e estragaria o valor).
    print("2. Integrando população (Censo 2022)...")
    print("3. Integrando PIB per capita (2022)...")
    pib = ler_csv("pib_per_capita.csv", separador=",")
    pib.columns = pib.columns.str.replace("\ufeff", "").str.strip().str.lower()
    pib["id_municipio"] = padronizar_id(pib["id_municipio"])

    pib["populacao"] = pd.to_numeric(
        pib["populacao_2022"], errors="coerce"
    )
    pib["pib_per_capita"] = pd.to_numeric(
        pib["pib_per_capita"], errors="coerce"
    )
    pib = pib[["id_municipio", "populacao", "pib_per_capita"]].copy()
    conferir_duplicados(pib, "id_municipio", "pib_per_capita.csv")

    base = base.merge(
        pib, on="id_municipio", how="left", validate="one_to_one"
    )


    # 4. Renda per capita
    print("4. Integrando renda per capita...")
    renda = ler_csv("renda_per_capita.csv", separador=",")

    renda.columns = (
        renda.columns.str.replace("\ufeff", "")
        .str.strip().str.lower()
    )

    renda["id_municipio"] = padronizar_id(
        renda["id_municipio"]
    )

    # O arquivo usa ponto como separador decimal (ex.: 1210.6).
    # converter_numero apagaria esse ponto (1210.6 -> 12106),
    # por isso a convers\u00e3o \u00e9 direta.
    renda["renda_per_capita"] = pd.to_numeric(
        renda["renda_per_capita"], errors="coerce"
    )

    renda = renda[
        ["id_municipio", "renda_per_capita"]
    ].copy()

    conferir_duplicados(
        renda, "id_municipio", "renda_per_capita.csv"
    )

    base = base.merge(
        renda, on="id_municipio", how="left",
        validate="one_to_one"
    )

    # 5. Educação: tabela SIDRA (com filtro de segurança para rodapés vazios/zeros)
    print("5. Lendo educação do IBGE...")
    caminho_educacao = PASTA / "educacao_ibge.csv"

    if not caminho_educacao.exists():
        raise FileNotFoundError(caminho_educacao)

    educacao = pd.read_csv(
        caminho_educacao,
        sep=";",
        encoding="utf-8-sig",
        # Não pulamos um número fixo de linhas: o cabeçalho do SIDRA tem
        # 4 linhas, e o antigo skiprows=6 descartava os 2 primeiros
        # municípios. As linhas que não são de município são removidas
        # abaixo, pelo código de 7 dígitos.
        header=None,
        names=[
            "id_municipio",
            "nome_municipio",
            "idade",
            "taxa_alfabetizacao"
        ],
        dtype=str
    )

    # Manter só linhas de município (código IBGE com 7 dígitos);
    # descarta cabeçalhos ("Cód.") e rodapés da tabela
    educacao = educacao[
        educacao["id_municipio"].astype(str).str.fullmatch(r"\d{7}")
    ].copy()

    educacao["id_municipio"] = padronizar_id(
        educacao["id_municipio"]
    )

    # Esta tabela usa vírgula decimal (ex.: "91,59"), então aqui
    # converter_numero é a função certa
    educacao["taxa_alfabetizacao"] = converter_numero(
        educacao["taxa_alfabetizacao"]
    )

    educacao = educacao[
        (educacao["id_municipio"].notna()) & 
        (educacao["id_municipio"] != "0000000")
    ].copy()

    educacao = educacao[
        ["id_municipio", "taxa_alfabetizacao"]
    ]

    conferir_duplicados(
        educacao, "id_municipio", "educacao_ibge.csv"
    )

    base = base.merge(
        educacao, on="id_municipio", how="left",
        validate="one_to_one"
    )

    # 6. IDHM 2010 (Atlas Brasil)
    # O arquivo do Atlas não tem o código do IBGE, então o cruzamento
    # é feito pelo nome + UF. Para isso:
    #   a) comparamos nomes ignorando acentos, hífens, apóstrofos e
    #      as palavras de/do/da/dos/das (resolve diferenças de escrita);
    #   b) os casos restantes (municípios com grafia oficial diferente,
    #      renomeados ou criados depois de 2010) ficam escritos em
    #      correcoes_idhm.csv, que qualquer pessoa pode conferir;
    #   c) se algum município ficar sem IDHM, o script PARA com erro,
    #      em vez de seguir em silêncio.
    # O arquivo não tem IDHM Renda, por isso essa coluna foi removida.
    print("6. Integrando IDHM 2010...")
    idhm = ler_csv("idhm.csv", separador=",")

    idhm.columns = (
        idhm.columns.str.replace("﻿", "")
        .str.strip().str.lower()
    )

    idhm["idhm"] = pd.to_numeric(idhm["idhm 2010"], errors="coerce")
    idhm["chave_nome"] = idhm["municipio"].apply(chave_nome_idhm)
    idhm["chave_uf"] = idhm["uf"].str.upper().str.strip()

    if idhm.duplicated(["chave_nome", "chave_uf"]).any():
        raise ValueError(
            "Dois municípios do arquivo IDHM ficaram com a mesma chave "
            "de nome na mesma UF; a comparação de nomes não é segura."
        )

    # Nome usado na busca: o nome atual ou, se houver correção,
    # o nome com que o município aparece no Atlas 2010
    correcoes = ler_csv(
        "correcoes_idhm.csv", separador=",", dtype={"id_municipio": str}
    )
    correcoes["id_municipio"] = padronizar_id(correcoes["id_municipio"])
    conferir_duplicados(correcoes, "id_municipio", "correcoes_idhm.csv")

    mapa_correcoes = dict(
        zip(correcoes["id_municipio"], correcoes["nome_idhm_2010"])
    )
    nome_busca = base["id_municipio"].map(mapa_correcoes).fillna(base["nome"])

    base["chave_nome"] = nome_busca.apply(chave_nome_idhm)
    base["chave_uf"] = base["uf"].str.upper().str.strip()

    # Mais de um município atual pode usar o mesmo IDHM de origem
    # (ex.: município criado a partir de outro), por isso many_to_one
    base = base.merge(
        idhm[["chave_nome", "chave_uf", "idhm"]],
        on=["chave_nome", "chave_uf"],
        how="left",
        validate="many_to_one"
    )

    base = base.drop(columns=["chave_nome", "chave_uf"])

    sem_idhm = base[base["idhm"].isna()]
    if not sem_idhm.empty:
        raise ValueError(
            f"{len(sem_idhm)} município(s) sem IDHM. Adicione-os em "
            f"correcoes_idhm.csv:\n"
            f"{sem_idhm[['id_municipio', 'nome', 'uf']].to_string(index=False)}"
        )

    print(
        f"   IDHM encontrado para todos os {len(base)} municípios "
        f"({len(correcoes)} via correcoes_idhm.csv)"
    )

    # 7. Saúde: óbitos do DATASUS convertidos em taxa
    # O DATASUS só lista municípios com pelo menos 1 óbito no recorte
    # consultado (o arquivo não tem nenhuma linha com 0). Por isso,
    # município ausente = 0 óbitos.
    # A contagem bruta acompanha o tamanho da cidade (correlação 0,98
    # com a população), então usamos a taxa por 1.000 habitantes.
    # ATENÇÃO: o recorte exato do arquivo do DATASUS (tipo de óbito e
    # período) ainda precisa ser confirmado.
    print("7. Integrando óbitos (taxa por 1.000 habitantes)...")
    saude = ler_csv("saude.csv", separador=",")

    saude.columns = (
        saude.columns.str.replace("﻿", "")
        .str.strip().str.lower()
    )

    saude["id_municipio"] = padronizar_id(
        saude["id_municipio"]
    )

    saude["obitos_residencia"] = pd.to_numeric(
        saude["obitos_residencia"], errors="coerce"
    )

    saude = saude.dropna(subset=["id_municipio"]).copy()
    saude = saude[["id_municipio", "obitos_residencia"]]

    conferir_duplicados(
        saude, "id_municipio", "saude.csv"
    )

    base = base.merge(
        saude, on="id_municipio", how="left",
        validate="one_to_one"
    )

    ausentes_obitos = base["obitos_residencia"].isna().sum()
    base["obitos_residencia"] = base["obitos_residencia"].fillna(0)

    base["taxa_obitos"] = (
        base["obitos_residencia"] / base["populacao"] * 1000
    )

    print(
        f"   {ausentes_obitos} municípios sem registro no DATASUS "
        f"considerados com 0 óbitos"
    )

    # 8. Organizar colunas finais
    colunas = [
        "id_municipio",
        "nome",
        "uf",
        "populacao",
        "pib_per_capita",
        "renda_per_capita",
        "taxa_alfabetizacao",
        "idhm",
        "obitos_residencia",
        "taxa_obitos"
    ]

    base = base[colunas]

    # 9. Relatório de cobertura
    print("\n===== COBERTURA DOS DADOS =====")
    print("Municípios na base:", len(base))

    for coluna in base.columns[3:]:
        quantidade = base[coluna].notna().sum()
        print(
            f"{coluna}: {quantidade} preenchidos; "
            f"{base[coluna].isna().sum()} ausentes"
        )

    # 10. Salvar arquivo integrado final
    saida = PASTA / "indicadores_completos.csv"

    base.to_csv(
        saida,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nIntegração concluída com sucesso!")
    print("Arquivo gerado:", saida)

    print("\nPrimeiros registros:")
    print(base.head(10).to_string(index=False))


if __name__ == "__main__":
    executar()