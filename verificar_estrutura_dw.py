import pymysql

# Conexão
connection = pymysql.connect(
    host='localhost',
    user='user',
    password='user123',
    database='filmes',
    charset='utf8mb4',
    port=33016
)

cursor = connection.cursor()

print("=" * 80)
print("ESTRUTURA DO DATA WAREHOUSE - ESQUEMA ESTRELA")
print("=" * 80)

# Listar todas as tabelas
cursor.execute("SHOW TABLES")
tabelas = cursor.fetchall()

print("\n📊 TABELAS NO BANCO:")
print("-" * 80)

dimensoes = []
fato = []
bridge = []

for tabela in tabelas:
    nome = tabela[0]
    if nome.startswith('Dim_'):
        dimensoes.append(nome)
    elif nome.startswith('Fato_Filme') and '_' in nome[10:]:
        bridge.append(nome)
    else:
        fato.append(nome)

print("\n🔷 TABELAS DE DIMENSÃO (Dim_*):")
for dim in sorted(dimensoes):
    cursor.execute(f"SELECT COUNT(*) FROM {dim}")
    count = cursor.fetchone()[0]
    print(f"  • {dim:30s} ({count:6d} registros)")

print("\n⭐ TABELA FATO:")
for f in sorted(fato):
    cursor.execute(f"SELECT COUNT(*) FROM {f}")
    count = cursor.fetchone()[0]
    print(f"  • {f:30s} ({count:6d} registros)")

print("\n🔗 TABELAS BRIDGE (Relacionamentos N:N):")
for b in sorted(bridge):
    cursor.execute(f"SELECT COUNT(*) FROM {b}")
    count = cursor.fetchone()[0]
    print(f"  • {b:30s} ({count:6d} registros)")

# Visualizar relacionamentos da Fato_Filme
print("\n" + "=" * 80)
print("RELACIONAMENTOS DA TABELA FATO")
print("=" * 80)

cursor.execute("""
    SELECT 
        TABLE_NAME,
        COLUMN_NAME,
        REFERENCED_TABLE_NAME,
        REFERENCED_COLUMN_NAME
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = 'filmes'
    AND TABLE_NAME = 'Fato_Filme'
    AND REFERENCED_TABLE_NAME IS NOT NULL
""")

print("\nFato_Filme está conectada às seguintes dimensões:")
for rel in cursor.fetchall():
    print(f"  • {rel[1]:20s} -> {rel[2]}.{rel[3]}")

# Exemplo de consulta analítica
print("\n" + "=" * 80)
print("EXEMPLO DE CONSULTA ANALÍTICA - Top 10 Filmes por Bilheteria")
print("=" * 80)

cursor.execute("""
    SELECT 
        df.titulo,
        dt.ano_lancamento,
        ff.bilheteria_mundial,
        ff.nota_imdb
    FROM Fato_Filme ff
    INNER JOIN Dim_Filme df ON ff.id_filme = df.id_filme
    INNER JOIN Dim_Tempo dt ON ff.id_tempo = dt.id_tempo
    WHERE ff.bilheteria_mundial IS NOT NULL
    ORDER BY ff.bilheteria_mundial DESC
    LIMIT 10
""")

print("\n{:<50} {:>8} {:>15} {:>8}".format("Título", "Ano", "Bilheteria", "Nota"))
print("-" * 80)
for row in cursor.fetchall():
    titulo = row[0][:47] + "..." if len(row[0]) > 50 else row[0]
    ano = row[1] if row[1] else "N/A"
    bilheteria = f"${row[2]:,.0f}" if row[2] else "N/A"
    nota = f"{row[3]:.1f}" if row[3] else "N/A"
    print(f"{titulo:<50} {ano:>8} {bilheteria:>15} {nota:>8}")

connection.close()
print("\n" + "=" * 80)
print("✅ Data Warehouse configurado com sucesso no padrão Star Schema!")
print("=" * 80)
