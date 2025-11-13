import pandas as pd

# Caminho do arquivo original
input_file = 'filmes_ingles_apos_2000.csv'
output_file = 'filmes_processado.csv'

# Lê o CSV original (mantendo todas as colunas)
df = pd.read_csv(input_file)

# Função para pegar apenas o primeiro valor antes da vírgula
def pegar_primeiro(valor):
    if pd.isna(valor):
        return valor
    return str(valor).split(',')[0].strip()

# Identificar colunas corretas pelos índices
col_director = df.columns[12]   # coluna 13
col_language = df.columns[19]   # coluna 20

# Aplicar a função nas colunas específicas
df[col_director] = df[col_director].apply(pegar_primeiro)
df[col_language] = df[col_language].apply(pegar_primeiro)

# Exportar o resultado completo para um novo arquivo CSV
df.to_csv(output_file, index=False, encoding='utf-8')

print(f"✅ Novo arquivo gerado com sucesso: {output_file}")
