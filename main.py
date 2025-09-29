import pandas as pd

# Se o arquivo usa vírgula como separador padrão:
df = pd.read_csv(r"base de dados nao normalizada\world_imdb_movies_top_movies_per_year.csv[1]", encoding='utf-8')

# Filtrar filmes após 2000 em inglês
filmes_ingles_2000 = df[
    (df['year'] >= 2000) &
    (df['language'].str.contains('English', case=False, na=False))
]

print(filmes_ingles_2000.head())
filmes_ingles_2000.to_csv("filmes_ingles_apos_2000.csv", index=False)


df = filmes_ingles_2000



movies = df.drop(columns=['director','writer','star','genre','language'])


movie_director = (
    df[['id','director']]
    .assign(director=df['director'].str.split(',\s*'))
    .explode('director')
)

movie_writer = (
    df[['id','writer']]
    .assign(writer=df['writer'].str.split(',\s*'))
    .explode('writer')
)


movie_star = (
    df[['id','star']]
    .assign(star=df['star'].str.split(',\s*'))
    .explode('star')
)


movie_genre = (
    df[['id','genre']]
    .assign(genre=df['genre'].str.split(',\s*'))
    .explode('genre')

)

movie_language = (
    df[['id','language']]
    .assign(language=df['language'].str.split(',\s*'))
    .explode('language')
)

import pandas as pd


# --- Pessoas (diretores, roteiristas, atores)
pessoas = pd.concat([
    movie_director[['director']].rename(columns={'director':'nome'}),
    movie_writer[['writer']].rename(columns={'writer':'nome'}),
    movie_star[['star']].rename(columns={'star':'nome'})
]).drop_duplicates().reset_index(drop=True)

pessoas['id_pessoa'] = pessoas.index + 1

# --- Gêneros
generos = movie_genre[['genre']].drop_duplicates().reset_index(drop=True)
generos['id_genero'] = generos.index + 1

# --- Idiomas
idiomas = movie_language[['language']].drop_duplicates().reset_index(drop=True)
idiomas['id_idioma'] = idiomas.index + 1

# --- Países (exemplo com country_origin)
paises = movies[['country_origin']].drop_duplicates().reset_index(drop=True)
paises['id_pais'] = paises.index + 1

# --- Empresas (exemplo com production_company)
empresas = movies[['production_company']].drop_duplicates().reset_index(drop=True)
empresas['id_empresa'] = empresas.index + 1

# Filme ↔ Pessoas
filme_equipe = pd.concat([
    movie_director.merge(pessoas, left_on='director', right_on='nome')[['id', 'id_pessoa']].assign(papel='Diretor'),
    movie_writer.merge(pessoas, left_on='writer', right_on='nome')[['id', 'id_pessoa']].assign(papel='Roteirista'),
    movie_star.merge(pessoas, left_on='star', right_on='nome')[['id', 'id_pessoa']].assign(papel='Ator')
])

filme_equipe = filme_equipe.rename(columns={'id':'id_filme'})

# Filme ↔ Gênero
filme_genero = movie_genre.merge(generos, left_on='genre', right_on='genre')[['id', 'id_genero']].rename(columns={'id':'id_filme'})

# Filme ↔ Idioma
filme_idioma = movie_language.merge(idiomas, left_on='language', right_on='language')[['id', 'id_idioma']].rename(columns={'id':'id_filme'})

# Filme ↔ País
filme_pais = movies.merge(paises, left_on='country_origin', right_on='country_origin')[['id', 'id_pais']].rename(columns={'id':'id_filme'})

# Filme ↔ Empresa
filme_empresa = movies.merge(empresas, left_on='production_company', right_on='production_company')[['id', 'id_empresa']].rename(columns={'id':'id_filme'})



from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Usuário do MySQL
user = "user"               
# Senha do MySQL
password = "user123"        
# Codifica caracteres especiais (recomendado)
password_enc = quote_plus(password)
# Host do container
host = "localhost"          
# Porta mapeada no host
port = 33016                
# Nome do banco
database = "filmes"     

# Cria engine do SQLAlchemy
engine = create_engine(f"mysql+pymysql://{user}:{password_enc}@{host}:{port}/{database}")
print(engine)

# Criação de tabelas
with engine.begin() as conn:
    # Tabelas de dimensão
    conn.execute(text("""
        CREATE TABLE pessoas (
            id_pessoa INT AUTO_INCREMENT PRIMARY KEY,
            nome_pessoa VARCHAR(255) UNIQUE
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE generos (
            id_genero INT AUTO_INCREMENT PRIMARY KEY,
            nome_genero VARCHAR(255) UNIQUE
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE idiomas (
            id_idioma INT AUTO_INCREMENT PRIMARY KEY,
            nome_idioma VARCHAR(255) UNIQUE
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE paises (
            id_pais INT AUTO_INCREMENT PRIMARY KEY,
            nome_pais VARCHAR(255) UNIQUE
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE empresas (
            id_empresa INT AUTO_INCREMENT PRIMARY KEY,
            nome_empresa VARCHAR(255) UNIQUE
        );
    """))
    
    # Tabela principal
    conn.execute(text("""
        CREATE TABLE movies (
            id VARCHAR(50) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            link VARCHAR(255),
            year INT,
            duration VARCHAR(50),
            rating_mpa VARCHAR(50),
            rating_imdb FLOAT,
            vote BIGINT,
            budget BIGINT,
            gross_world_wide BIGINT,
            gross_us_canada BIGINT,
            gross_opening_weekend BIGINT,
            country_origin VARCHAR(255),
            filming_location VARCHAR(255),
            production_company VARCHAR(255),
            win INT,
            nomination INT,
            oscar INT
        );
    """))

    # Tabelas associativas
    conn.execute(text("""
        CREATE TABLE filme_equipe (
            id_filme VARCHAR(50),
            id_pessoa INT,
            papel VARCHAR(50),
            FOREIGN KEY (id_filme) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (id_pessoa) REFERENCES pessoas(id_pessoa)
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE filme_genero (
            id_filme VARCHAR(50),
            id_genero INT,
            FOREIGN KEY (id_filme) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (id_genero) REFERENCES generos(id_genero)
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE filme_idioma (
            id_filme VARCHAR(50),
            id_idioma INT,
            FOREIGN KEY (id_filme) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (id_idioma) REFERENCES idiomas(id_idioma)
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE filme_pais (
            id_filme VARCHAR(50),
            id_pais INT,
            FOREIGN KEY (id_filme) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (id_pais) REFERENCES paises(id_pais)
        );
    """))
    
    conn.execute(text("""
        CREATE TABLE filme_empresa (
            id_filme VARCHAR(50),
            id_empresa INT,
            FOREIGN KEY (id_filme) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY (id_empresa) REFERENCES empresas(id_empresa)
        );
    """))

print("Todas as tabelas foram criadas com sucesso no MySQL!")
