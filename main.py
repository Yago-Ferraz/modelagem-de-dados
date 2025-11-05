import pandas as pd
import pymysql
import re
import os
import sys

# Aumenta o limite de recursão (mantido por precaução)
sys.setrecursionlimit(2000)

class FilmesNormalizer:
    def __init__(self, host='localhost', user='root', password='root123', database='filmes_dw'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

    # ----------------------------
    # 1. Conexão com o banco
    # ----------------------------
    def conectar_banco(self, criar_db=False):
        try:
            print("[INFO] Conectando ao banco...")
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                charset='utf8mb4',
                port=33016,
                autocommit=False
            )
            self.cursor = self.connection.cursor()
            if criar_db:
                self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                print(f"[INFO] Banco '{self.database}' criado ou já existia.")
            self.cursor.execute(f"USE {self.database}")
            print(f"[INFO] Usando banco '{self.database}'")
            return True
        except Exception as e:
            print(f"[ERRO] Erro ao conectar/criar banco: {e}")
            return False

    def desconectar_banco(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("[INFO] Conexão com o banco encerrada.")
            
    # ----------------------------
    # 2. Popular Dimensão Tempo Detalhada
    # ----------------------------
    def popular_dim_tempo(self, anos_a_popular):
        """Popula a Dim_Tempo com base nos anos encontrados no dataset, usando placeholders."""
        print("[INFO] Populando Dim_Tempo detalhada...")
        
        df_tempo = pd.DataFrame({'ano_lancamento': sorted(list(set(anos_a_popular)))})
        
        df_tempo['id_tempo'] = df_tempo['ano_lancamento'] 
        df_tempo['decada'] = (df_tempo['ano_lancamento'] // 10) * 10
        
        # PLACEHOLDERS
        df_tempo['trimestre'] = 'Ano Inteiro'
        df_tempo['semestre'] = 'Ano Inteiro'
        df_tempo['estacao_do_ano'] = 'Indefinida'
        df_tempo['nome_mes'] = 'Ano Inteiro'
        df_tempo['nome_dia_semana'] = 'Indefinido'
        df_tempo['e_fim_de_semana'] = 0
        df_tempo['e_feriado_nacional'] = 0
        df_tempo['tipo_dia'] = 'Ano Completo'
        
        df_tempo = df_tempo.drop_duplicates(subset=['id_tempo'])
        
        sql_insert_tempo = """
            INSERT IGNORE INTO Dim_Tempo (
                id_tempo, ano_lancamento, decada, trimestre, semestre, 
                estacao_do_ano, nome_mes, nome_dia_semana, e_fim_de_semana, 
                e_feriado_nacional, tipo_dia
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for _, row in df_tempo.iterrows():
            try:
                self.cursor.execute(sql_insert_tempo, (
                    row['id_tempo'], row['ano_lancamento'], row['decada'],
                    row['trimestre'], row['semestre'], row['estacao_do_ano'],
                    row['nome_mes'], row['nome_dia_semana'], row['e_fim_de_semana'],
                    row['e_feriado_nacional'], row['tipo_dia']
                ))
            except Exception:
                pass
                
        self.connection.commit()
        print(f"[INFO] Dim_Tempo populada com {len(df_tempo)} anos únicos.")

    # ----------------------------
    # 3. Criação das tabelas (Modelo Direto Fato-Dimensões)
    # ----------------------------
    def criar_tabelas(self):
        try:
            print("[INFO] Criando tabelas com relacionamento direto (Fato -> Dimensões)...")
            sqls = [
                """CREATE TABLE IF NOT EXISTS Pessoas (
                    id_pessoa INT AUTO_INCREMENT PRIMARY KEY,
                    nome_pessoa VARCHAR(255) NOT NULL,
                    UNIQUE KEY uk_pessoa (nome_pessoa)
                ) ENGINE=InnoDB;""",
                
                """CREATE TABLE IF NOT EXISTS Generos (
                    id_genero INT AUTO_INCREMENT PRIMARY KEY,
                    nome_genero VARCHAR(100) NOT NULL,
                    UNIQUE KEY uk_genero (nome_genero)
                ) ENGINE=InnoDB;""",
                
                """CREATE TABLE IF NOT EXISTS Paises (
                    id_pais INT AUTO_INCREMENT PRIMARY KEY,
                    nome_pais VARCHAR(150) NOT NULL,
                    UNIQUE KEY uk_pais (nome_pais)
                ) ENGINE=InnoDB;""",
                
                """CREATE TABLE IF NOT EXISTS Empresas (
                    id_empresa INT AUTO_INCREMENT PRIMARY KEY,
                    nome_empresa VARCHAR(255) NOT NULL,
                    UNIQUE KEY uk_empresa (nome_empresa)
                ) ENGINE=InnoDB;""",
                
                """CREATE TABLE IF NOT EXISTS Idiomas (
                    id_idioma INT AUTO_INCREMENT PRIMARY KEY,
                    nome_idioma VARCHAR(150) NOT NULL,
                    UNIQUE KEY uk_idioma (nome_idioma)
                ) ENGINE=InnoDB;""",

                """CREATE TABLE IF NOT EXISTS Dim_Tempo (
                    id_tempo INT PRIMARY KEY,
                    ano_lancamento INT NOT NULL,
                    decada INT,
                    trimestre VARCHAR(20),
                    semestre VARCHAR(20),
                    estacao_do_ano VARCHAR(20),
                    nome_mes VARCHAR(20),
                    nome_dia_semana VARCHAR(20),
                    e_fim_de_semana TINYINT(1),
                    e_feriado_nacional TINYINT(1),
                    tipo_dia VARCHAR(20),
                    UNIQUE KEY uk_ano_lancamento (ano_lancamento)
                ) ENGINE=InnoDB;""",

                # ----------------------------
                # FATO FILME DIRETAMENTE LIGADA ÀS DIMENSÕES
                # ----------------------------
                """CREATE TABLE IF NOT EXISTS Fato_Filme (
                    id_filme INT AUTO_INCREMENT PRIMARY KEY,
                    id_tempo INT,
                    id_pessoa INT,
                    id_genero INT,
                    id_pais INT,
                    id_empresa INT,
                    id_idioma INT,

                    titulo VARCHAR(255) NOT NULL,
                    link_imdb VARCHAR(500),
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
                    vitorias_oscar INT,

                    FOREIGN KEY (id_tempo) REFERENCES Dim_Tempo(id_tempo),
                    FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa),
                    FOREIGN KEY (id_genero) REFERENCES Generos(id_genero),
                    FOREIGN KEY (id_pais) REFERENCES Paises(id_pais),
                    FOREIGN KEY (id_empresa) REFERENCES Empresas(id_empresa),
                    FOREIGN KEY (id_idioma) REFERENCES Idiomas(id_idioma)
                ) ENGINE=InnoDB;""",

                # ----------------------------
                # TABELAS ASSOCIATIVAS (ligadas apenas às dimensões)
                # ----------------------------
                """CREATE TABLE IF NOT EXISTS filme_estrela (
                    id_pessoa INT PRIMARY KEY,
                    ordem_credito INT DEFAULT NULL,
                    FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE
                ) ENGINE=InnoDB;""",

                """CREATE TABLE IF NOT EXISTS filme_diretor (
                    id_pessoa INT PRIMARY KEY,
                    FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE
                ) ENGINE=InnoDB;""",

                """CREATE TABLE IF NOT EXISTS filme_roteirista (
                    id_pessoa INT PRIMARY KEY,
                    FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE
                ) ENGINE=InnoDB;""",

                """CREATE TABLE IF NOT EXISTS filme_genero (
                    id_genero INT PRIMARY KEY,
                    FOREIGN KEY (id_genero) REFERENCES Generos(id_genero) ON DELETE CASCADE
                ) ENGINE=InnoDB;""",

                """CREATE TABLE IF NOT EXISTS filme_pais_origem (
                    id_pais INT PRIMARY KEY,
                    FOREIGN KEY (id_pais) REFERENCES Paises(id_pais) ON DELETE CASCADE
                ) ENGINE=InnoDB;""",

                """CREATE TABLE IF NOT EXISTS filme_empresa_producao (
                    id_empresa INT PRIMARY KEY,
                    FOREIGN KEY (id_empresa) REFERENCES Empresas(id_empresa) ON DELETE CASCADE
                ) ENGINE=InnoDB;""",

                """CREATE TABLE IF NOT EXISTS filme_idioma (
                    id_idioma INT PRIMARY KEY,
                    FOREIGN KEY (id_idioma) REFERENCES Idiomas(id_idioma) ON DELETE CASCADE
                ) ENGINE=InnoDB;"""
            ]
            
            for sql in sqls:
                self.cursor.execute(sql)
            self.connection.commit()
            print("[INFO] Tabelas criadas com sucesso (modelo direto).")
        except Exception as e:
            print(f"[ERRO] Erro ao criar tabelas: {e}")
            self.connection.rollback()

    # ----------------------------
    # 4. Funções Auxiliares
    # ----------------------------
    def inserir_ou_obter_id(self, tabela, campo_nome, valor, campo_id):
        if not valor or pd.isna(valor) or str(valor).strip() == '':
            return None
        valor = str(valor).strip()
        
        if tabela == 'Dim_Tempo':
            return valor 
            
        self.cursor.execute(f"SELECT {campo_id} FROM {tabela} WHERE {campo_nome} = %s", (valor,))
        resultado = self.cursor.fetchone()
        if resultado:
            return resultado[0]
        
        self.cursor.execute(f"INSERT INTO {tabela} ({campo_nome}) VALUES (%s)", (valor,))
        return self.cursor.lastrowid

    def processar_lista_valores(self, valores_str, separador=','):
        if not valores_str or pd.isna(valores_str):
            return []
        return [v.strip() for v in str(valores_str).split(separador) if v.strip()]

    def limpar_duracao(self, duracao_str):
        if not duracao_str or pd.isna(duracao_str):
            return None
        total_minutos = 0
        horas_match = re.search(r'(\d+)h', str(duracao_str))
        if horas_match:
            total_minutos += int(horas_match.group(1)) * 60
        minutos_match = re.search(r'(\d+)m', str(duracao_str))
        if minutos_match:
            total_minutos += int(minutos_match.group(1))
        return total_minutos if total_minutos > 0 else None

    def limpar_valor_numerico(self, valor):
        if pd.isna(valor) or valor == '' or valor is None:
            return None
        try:
            return float(valor)
        except (ValueError, TypeError):
            return None

    # ----------------------------
    # 5. Processamento de Filme (ETL)
    # ----------------------------
    def processar_filme(self, row, numero_linha=None):
        try:
            titulo = row.get('title')
            ano_lancamento = int(row['year']) if pd.notna(row.get('year')) else None
            id_tempo = ano_lancamento

            if numero_linha and titulo:
                print(f"[INFO] Processando filme #{numero_linha}: {titulo}")

            # Seleciona apenas o primeiro valor de cada lista para vínculo direto
            def primeiro_valor(coluna):
                valores = self.processar_lista_valores(row.get(coluna, ''))
                return valores[0] if valores else None

            id_pessoa = self.inserir_ou_obter_id('Pessoas', 'nome_pessoa', primeiro_valor('star'), 'id_pessoa')
            id_genero = self.inserir_ou_obter_id('Generos', 'nome_genero', primeiro_valor('genre'), 'id_genero')
            id_pais = self.inserir_ou_obter_id('Paises', 'nome_pais', primeiro_valor('country_origin'), 'id_pais')
            id_empresa = self.inserir_ou_obter_id('Empresas', 'nome_empresa', primeiro_valor('production_company'), 'id_empresa')
            id_idioma = self.inserir_ou_obter_id('Idiomas', 'nome_idioma', primeiro_valor('language'), 'id_idioma')

            # INSERE DIRETAMENTE NA FATO
            query = """
                INSERT INTO Fato_Filme (
                    id_tempo, id_pessoa, id_genero, id_pais, id_empresa, id_idioma,
                    titulo, link_imdb, duracao_minutos, classificacao_mpa,
                    nota_imdb, votos_imdb, orcamento, bilheteria_mundial,
                    bilheteria_eua_canada, bilheteria_abertura, vitorias_premios,
                    nominacoes_premios, vitorias_oscar
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            valores = (
                id_tempo, id_pessoa, id_genero, id_pais, id_empresa, id_idioma,
                titulo, row.get('link'), self.limpar_duracao(row.get('duration')), row.get('rating_mpa'),
                self.limpar_valor_numerico(row.get('rating_imdb')), self.limpar_valor_numerico(row.get('vote')),
                self.limpar_valor_numerico(row.get('budget')), self.limpar_valor_numerico(row.get('gross_world_wide')),
                self.limpar_valor_numerico(row.get('gross_us_canada')), self.limpar_valor_numerico(row.get('gross_opening_weekend')),
                self.limpar_valor_numerico(row.get('win')), self.limpar_valor_numerico(row.get('nomination')), self.limpar_valor_numerico(row.get('oscar'))
            )
            self.cursor.execute(query, valores)
            self.connection.commit()

            return True
        except Exception as e:
            print(f"[ERRO] Ao processar filme '{titulo}': {e}")
            self.connection.rollback()
            return False

    # ----------------------------
    # 6. Normalização CSV e Execução
    # ----------------------------
    def normalizar_csv(self, arquivo_csv, limite=None):
        if not os.path.exists(arquivo_csv):
            print(f"[ERRO] Arquivo não encontrado: {arquivo_csv}")
            return
        
        print(f"[INFO] Iniciando leitura do CSV: {arquivo_csv}")
        chunk_size = 500 
        total = 0
        anos_unicos = set()
        
        # Coleta dos anos
        print("[INFO] Coletando anos únicos...")
        for chunk in pd.read_csv(arquivo_csv, chunksize=chunk_size, usecols=['year']):
            anos_unicos.update(chunk['year'].dropna().astype(int).tolist())
        
        if anos_unicos:
            self.popular_dim_tempo(anos_unicos)
        
        print("[INFO] Iniciando inserção dos dados...")
        for chunk in pd.read_csv(arquivo_csv, chunksize=chunk_size):
            if limite is not None and total >= limite:
                break
            
            chunk_process = chunk if limite is None else chunk.head(limite - total)
            print(f"[INFO] Processando linhas {total+1} até {total+len(chunk_process)}")
            
            for _, row in chunk_process.iterrows():
                if limite is not None and total >= limite:
                    break
                self.processar_filme(row, total + 1)
                total += 1
                        
        print(f"[INFO] Normalização concluída! Total de filmes processados: {total}")

# ----------------------------
# EXECUÇÃO PRINCIPAL
# ----------------------------
if __name__ == "__main__":
    arquivo_csv = "filmes_ingles_apos_2000.csv"
    DB_NAME = 'filmes_dw_modelo_direto' 
    LIMITE_PROCESSAMENTO = 1000
    
    normalizer = FilmesNormalizer(user='root', password='root123', database=DB_NAME)
    
    if normalizer.conectar_banco(criar_db=True):
        normalizer.criar_tabelas() 
        normalizer.normalizar_csv(arquivo_csv, limite=LIMITE_PROCESSAMENTO)
        normalizer.desconectar_banco()
        print(f"\n[SUCESSO] Banco DW '{DB_NAME}' criado e dados inseridos com sucesso!")
