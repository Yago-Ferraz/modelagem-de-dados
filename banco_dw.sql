-- ========================================================
-- CRIAÇÃO DO BANCO DE DADOS DIMENSIONAL: FILMES_DW
-- ========================================================

CREATE DATABASE filmes_dw;
USE filmes_dw;

-- ========================================================
-- 1. DIMENSÕES BASE
-- ========================================================

CREATE TABLE dim_tempo (
    id_tempo_sk INT AUTO_INCREMENT PRIMARY KEY,
    data_completa DATE,
    ano INT,
    mes INT,
    trimestre INT,
    nome_mes VARCHAR(20)
) ENGINE=InnoDB;

CREATE TABLE dim_diretor (
    id_diretor_sk INT AUTO_INCREMENT PRIMARY KEY,
    nome_diretor VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dim_idioma (
    id_idioma_sk INT AUTO_INCREMENT PRIMARY KEY,
    nome_idioma VARCHAR(150) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dim_genero (
    id_genero_sk INT AUTO_INCREMENT PRIMARY KEY,
    nome_genero VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dim_pais (
    id_pais_sk INT AUTO_INCREMENT PRIMARY KEY,
    nome_pais VARCHAR(150) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dim_empresa (
    id_empresa_sk INT AUTO_INCREMENT PRIMARY KEY,
    nome_empresa VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dim_estrela (
    id_estrela_sk INT AUTO_INCREMENT PRIMARY KEY,
    nome_estrela VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dim_roteirista (
    id_roteirista_sk INT AUTO_INCREMENT PRIMARY KEY,
    nome_roteirista VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- ========================================================
-- 2. DIMENSÃO PRINCIPAL: FILME
-- ========================================================

CREATE TABLE dim_filme (
    id_filme_sk INT AUTO_INCREMENT PRIMARY KEY,
    id_filme_nk INT,  -- chave natural do sistema transacional
    titulo VARCHAR(255),
    link_imdb VARCHAR(500),
    classificacao_mpa VARCHAR(20),
    duracao_minutos INT,
    CONSTRAINT uq_dim_filme UNIQUE (id_filme_nk)
) ENGINE=InnoDB;

-- ========================================================
-- 3. TABELAS PONTE (BRIDGE TABLES)
-- ========================================================

CREATE TABLE bridge_filme_genero (
    id_filme_sk INT,
    id_genero_sk INT,
    PRIMARY KEY (id_filme_sk, id_genero_sk),
    FOREIGN KEY (id_filme_sk) REFERENCES dim_filme(id_filme_sk) ON DELETE CASCADE,
    FOREIGN KEY (id_genero_sk) REFERENCES dim_genero(id_genero_sk) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE bridge_filme_pais (
    id_filme_sk INT,
    id_pais_sk INT,
    PRIMARY KEY (id_filme_sk, id_pais_sk),
    FOREIGN KEY (id_filme_sk) REFERENCES dim_filme(id_filme_sk) ON DELETE CASCADE,
    FOREIGN KEY (id_pais_sk) REFERENCES dim_pais(id_pais_sk) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE bridge_filme_empresa (
    id_filme_sk INT,
    id_empresa_sk INT,
    PRIMARY KEY (id_filme_sk, id_empresa_sk),
    FOREIGN KEY (id_filme_sk) REFERENCES dim_filme(id_filme_sk) ON DELETE CASCADE,
    FOREIGN KEY (id_empresa_sk) REFERENCES dim_empresa(id_empresa_sk) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE bridge_filme_estrela (
    id_filme_sk INT,
    id_estrela_sk INT,
    PRIMARY KEY (id_filme_sk, id_estrela_sk),
    FOREIGN KEY (id_filme_sk) REFERENCES dim_filme(id_filme_sk) ON DELETE CASCADE,
    FOREIGN KEY (id_estrela_sk) REFERENCES dim_estrela(id_estrela_sk) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE bridge_filme_roteirista (
    id_filme_sk INT,
    id_roteirista_sk INT,
    PRIMARY KEY (id_filme_sk, id_roteirista_sk),
    FOREIGN KEY (id_filme_sk) REFERENCES dim_filme(id_filme_sk) ON DELETE CASCADE,
    FOREIGN KEY (id_roteirista_sk) REFERENCES dim_roteirista(id_roteirista_sk) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ========================================================
-- 4. TABELA FATO: FILMES
-- ========================================================

CREATE TABLE fato_filme (
    id_filme_sk INT,
    id_tempo_sk INT,
    id_diretor_sk INT,
    id_idioma_sk INT,
    -- MÉTRICAS
    nota_imdb DECIMAL(3,1),
    votos_imdb INT,
    orcamento DECIMAL(15,2),
    bilheteria_mundial DECIMAL(15,2),
    bilheteria_eua_canada DECIMAL(15,2),
    bilheteria_abertura DECIMAL(15,2),
    vitorias_premios INT,
    nominacoes_premios INT,
    vitorias_oscar INT,
    PRIMARY KEY (id_filme_sk, id_tempo_sk, id_diretor_sk, id_idioma_sk),
    FOREIGN KEY (id_filme_sk) REFERENCES dim_filme(id_filme_sk),
    FOREIGN KEY (id_tempo_sk) REFERENCES dim_tempo(id_tempo_sk),
    FOREIGN KEY (id_diretor_sk) REFERENCES dim_diretor(id_diretor_sk),
    FOREIGN KEY (id_idioma_sk) REFERENCES dim_idioma(id_idioma_sk)
) ENGINE=InnoDB;

-- ========================================================
-- 5. ÍNDICES RECOMENDADOS
-- ========================================================

CREATE INDEX idx_tempo_ano ON dim_tempo(ano);
CREATE INDEX idx_filme_titulo ON dim_filme(titulo);
CREATE INDEX idx_diretor_nome ON dim_diretor(nome_diretor);
CREATE INDEX idx_idioma_nome ON dim_idioma(nome_idioma);
CREATE INDEX idx_genero_nome ON dim_genero(nome_genero);
CREATE INDEX idx_pais_nome ON dim_pais(nome_pais);
CREATE INDEX idx_empresa_nome ON dim_empresa(nome_empresa);
CREATE INDEX idx_estrela_nome ON dim_estrela(nome_estrela);
CREATE INDEX idx_roteirista_nome ON dim_roteirista(nome_roteirista);

-- ========================================================
-- FIM DO SCRIPT
-- ========================================================
