import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# ================================
# 1. Carregar e filtrar o CSV
# ================================

df = pd.read_csv(r"base de dados nao normalizada\world_imdb_movies_top_movies_per_year.csv[1]", encoding='utf-8')

# Filtrar filmes após 2000 e em inglês
df = df[
    (df['year'] >= 2000) &
    (df['language'].str.contains('English', case=False, na=False))
]

print(f"{len(df)} filmes filtrados.")

# ================================
# 2. Normalização
# ================================

# Tabela principal: Filmes
filmes = df.drop(columns=['director','writer','star','genre','language']).copy()

# Diretores
movie_director = (
    df[['id','director']]
    .assign(director=df['director'].str.split(',\s*'))
    .explode('director')
    .dropna()
)

# Roteiristas
movie_writer = (
    df[['id','writer']]
    .assign(writer=df['writer'].str.split(',\s*'))
    .explode('writer')
    .dropna()
)

# Estrelas / Atores
movie_star = (
    df[['id','star']]
    .assign(star=df['star'].str.split(',\s*'))
    .explode('star')
    .dropna()
)

# Gêneros
movie_genre = (
    df[['id','genre']]
    .assign(genre=df['genre'].str.split(',\s*'))
    .explode('genre')
    .dropna()
)

# Idiomas
movie_language = (
    df[['id','language']]
    .assign(language=df['language'].str.split(',\s*'))
    .explode('language')
    .dropna()
)

# ================================
# 3. Tabelas de Dimensão
# ================================

# --- Pessoas (diretores, roteiristas, atores)
pessoas = pd.concat([
    movie_director[['director']].rename(columns={'director':'nome_pessoa'}),
    movie_writer[['writer']].rename(columns={'writer':'nome_pessoa'}),
    movie_star[['star']].rename(columns={'star':'nome_pessoa'})
]).drop_duplicates().reset_index(drop=True)
pessoas['id_pessoa'] = pessoas.index + 1

# --- Gêneros
generos = movie_genre[['genre']].drop_duplicates().reset_index(drop=True)
generos = generos.rename(columns={'genre':'nome_genero'})
generos['id_genero'] = generos.index + 1

# --- Idiomas
idiomas = movie_language[['language']].drop_duplicates().reset_index(drop=True)
idiomas = idiomas.rename(columns={'language':'nome_idioma'})
idiomas['id_idioma'] = idiomas.index + 1

# --- Países
paises = filmes[['country_origin']].drop_duplicates().reset_index(drop=True)
paises = paises.rename(columns={'country_origin':'nome_pais'})
paises['id_pais'] = paises.index + 1

# --- Empresas
empresas = filmes[['production_company']].drop_duplicates().reset_index(drop=True)
empresas = empresas.rename(columns={'production_company':'nome_empresa'})
empresas['id_empresa'] = empresas.index + 1

# ================================
# 4. Tabelas Associativas
# ================================

# Filme ↔ Diretor
filme_diretor = movie_director.merge(pessoas, left_on='director', right_on='nome_pessoa')[['id','id_pessoa']]
filme_diretor = filme_diretor.rename(columns={'id':'id_filme'})

# Filme ↔ Roteirista
filme_roteirista = movie_writer.merge(pessoas, left_on='writer', right_on='nome_pessoa')[['id','id_pessoa']]
filme_roteirista = filme_roteirista.rename(columns={'id':'id_filme'})

# Filme ↔ Estrela / Ator
filme_estrela = movie_star.merge(pessoas, left_on='star', right_on='nome_pessoa')[['id','id_pessoa']]
filme_estrela = filme_estrela.rename(columns={'id':'id_filme'})
filme_estrela['ordem_credito'] = None  # coluna adicional conforme o SQL

# Filme ↔ Gênero
filme_genero = movie_genre.merge(generos, left_on='genre', right_on='nome_genero')[['id','id_genero']]
filme_genero = filme_genero.rename(columns={'id':'id_filme'})

# Filme ↔ Idioma
filme_idioma = movie_language.merge(idiomas, left_on='language', right_on='nome_idioma')[['id','id_idioma']]
filme_idioma = filme_idioma.rename(columns={'id':'id_filme'})

# Filme ↔ País
filme_pais = filmes.merge(paises, left_on='country_origin', right_on='nome_pais')[['id','id_pais']]
filme_pais = filme_pais.rename(columns={'id':'id_filme'})

# Filme ↔ Empresa
filme_empresa = filmes.merge(empresas, left_on='production_company', right_on='nome_empresa')[['id','id_empresa']]
filme_empresa = filme_empresa.rename(columns={'id':'id_filme'})

# ================================
# 5. Conexão MySQL
# ================================

user = "root"
password = "root123"
password_enc = quote_plus(password)
host = "localhost"
port = 33016
database = "filmes"

engine =  create_engine(f"mysql+pymysql://{user}:{password_enc}@{host}:{port}/")

# ================================
# 6. Criação das Tabelas no MySQL
# ================================

engine_root = create_engine(f"mysql+pymysql://{user}:{password_enc}@{host}:{port}/")

with engine_root.begin() as conn:
    conn.execute(text(f"DROP DATABASE IF EXISTS {database};"))
    conn.execute(text(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))

with engine.begin() as conn:
    
    conn.execute(text("DROP DATABASE IF EXISTS filmes;"))
    conn.execute(text("CREATE DATABASE filmes;"))
    conn.execute(text("USE filmes;"))
    
    # 1. Filmes
    conn.execute(text("""
        CREATE TABLE Filmes (
            id_filme INT AUTO_INCREMENT PRIMARY KEY,
            titulo VARCHAR(255) NOT NULL,
            link_imdb VARCHAR(500),
            ano_lancamento INT,
            duracao_minutos INT,
            classificacao_mpa VARCHAR(20),
            nota_imdb DECIMAL(3,1),
            votos_imdb INT,
            orcamento DECIMAL(15,2),
            bilheteria_mundial DECIMAL(15,2),
            bilheteria_eua_canada DECIMAL(15,2),
            bilheteria_abertura DECIMAL(15,2),
            vitorias_premios INT,
            nominacoes_premios INT,
            vitorias_oscar INT
        ) ENGINE=InnoDB;
    """))

    # 2. Dimensões
    conn.execute(text("""
        CREATE TABLE Pessoas (
            id_pessoa INT AUTO_INCREMENT PRIMARY KEY,
            nome_pessoa VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Generos (
            id_genero INT AUTO_INCREMENT PRIMARY KEY,
            nome_genero VARCHAR(100) NOT NULL
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Paises (
            id_pais INT AUTO_INCREMENT PRIMARY KEY,
            nome_pais VARCHAR(150) NOT NULL
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Empresas (
            id_empresa INT AUTO_INCREMENT PRIMARY KEY,
            nome_empresa VARCHAR(255) NOT NULL
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Idiomas (
            id_idioma INT AUTO_INCREMENT PRIMARY KEY,
            nome_idioma VARCHAR(150) NOT NULL
        ) ENGINE=InnoDB;
    """))

    # 3. Associativas
    conn.execute(text("""
        CREATE TABLE Filme_Estrela (
            id_filme INT,
            id_pessoa INT,
            ordem_credito INT DEFAULT NULL,
            PRIMARY KEY (id_filme, id_pessoa),
            FOREIGN KEY (id_filme) REFERENCES Filmes(id_filme) ON DELETE CASCADE,
            FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Filme_Diretor (
            id_filme INT,
            id_pessoa INT,
            PRIMARY KEY (id_filme, id_pessoa),
            FOREIGN KEY (id_filme) REFERENCES Filmes(id_filme) ON DELETE CASCADE,
            FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Filme_Roteirista (
            id_filme INT,
            id_pessoa INT,
            PRIMARY KEY (id_filme, id_pessoa),
            FOREIGN KEY (id_filme) REFERENCES Filmes(id_filme) ON DELETE CASCADE,
            FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Filme_Genero (
            id_filme INT,
            id_genero INT,
            PRIMARY KEY (id_filme, id_genero),
            FOREIGN KEY (id_filme) REFERENCES Filmes(id_filme) ON DELETE CASCADE,
            FOREIGN KEY (id_genero) REFERENCES Generos(id_genero) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Filme_Pais_Origem (
            id_filme INT,
            id_pais INT,
            PRIMARY KEY (id_filme, id_pais),
            FOREIGN KEY (id_filme) REFERENCES Filmes(id_filme) ON DELETE CASCADE,
            FOREIGN KEY (id_pais) REFERENCES Paises(id_pais) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Filme_Empresa_Producao (
            id_filme INT,
            id_empresa INT,
            PRIMARY KEY (id_filme, id_empresa),
            FOREIGN KEY (id_filme) REFERENCES Filmes(id_filme) ON DELETE CASCADE,
            FOREIGN KEY (id_empresa) REFERENCES Empresas(id_empresa) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """))

    conn.execute(text("""
        CREATE TABLE Filme_Idioma (
            id_filme INT,
            id_idioma INT,
            PRIMARY KEY (id_filme, id_idioma),
            FOREIGN KEY (id_filme) REFERENCES Filmes(id_filme) ON DELETE CASCADE,
            FOREIGN KEY (id_idioma) REFERENCES Idiomas(id_idioma) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """))

print("✅ Estrutura criada com sucesso e idêntica ao modelo SQL.")
