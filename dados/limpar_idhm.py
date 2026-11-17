import pandas as pd

# 1. Lê apenas as duas primeiras colunas úteis
df = pd.read_csv('dados/data-_2_.csv', usecols=['Territorialidades', 'IDHM 2010'])

# 2. Remove espaços extras, a linha 'Brasil' e os rodapés do final
df['Territorialidades'] = df['Territorialidades'].astype(str).str.strip()
df = df[df['Territorialidades'] != 'Brasil']
df['IDHM 2010'] = pd.to_numeric(df['IDHM 2010'], errors='coerce')
df = df.dropna(subset=['IDHM 2010']).copy()

# 3. Separa Nome do Município e UF para facilitar o cruzamento depois
df['municipio'] = df['Territorialidades'].str.extract(r'^(.*)\s+\([A-Z]{2}\)$')[0]
df['uf'] = df['Territorialidades'].str.extract(r'\(([A-Z]{2})\)$')[0]

# 4. Reorganiza e salva como idhm_2010.csv
df_final = df[['municipio', 'uf', 'Territorialidades', 'IDHM 2010']]
df_final.to_csv('dados/idhm_2010.csv', index=False, encoding='utf-8')

print(f"Arquivo dados/idhm_2010.csv salvo com sucesso! Total de municípios: {len(df_final)}")