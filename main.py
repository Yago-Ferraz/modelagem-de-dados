import pandas as pd
import pymysql
import re
import os
import sys

# Aumenta o limite de recursão para processar grandes listas (embora possa não ser necessário aqui)
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
    # Conexão com o banco
    # ----------------------------
    def conectar_banco(self, criar_db=False):
        try:
            print("[INFO] Conectando ao banco...")
            # Tenta conectar sem especificar um banco de dados (Necessário para a criação do DB)
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
    # Criação das tabelas (MODELO DIMENSIONAL STAR SCHEMA)
    # ----------------------------
    def criar_tabelas(self):
        try:
            print("[INFO] Criando tabelas...")
            sqls = [
                # 1. TABELAS DE DIMENSÃO SIMPLES
                """CREATE TABLE IF NOT EXISTS Pessoas (id_pessoa INT AUTO_INCREMENT PRIMARY KEY, nome_pessoa VARCHAR(255) NOT NULL) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS Generos (id_genero INT AUTO_INCREMENT PRIMARY KEY, nome_genero VARCHAR(100) NOT NULL) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS Paises (id_pais INT AUTO_INCREMENT PRIMARY KEY, nome_pais VARCHAR(150) NOT NULL) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS Empresas (id_empresa INT AUTO_INCREMENT PRIMARY KEY, nome_empresa VARCHAR(255) NOT NULL) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS Idiomas (id_idioma INT AUTO_INCREMENT PRIMARY KEY, nome_idioma VARCHAR(150) NOT NULL) ENGINE=InnoDB;""",
                
                # 2. DIMENSÃO TEMPO
                """CREATE TABLE IF NOT EXISTS Dim_Tempo (id_tempo INT PRIMARY KEY, ano_lancamento INT NOT NULL, UNIQUE KEY uk_ano_lancamento (ano_lancamento)) ENGINE=InnoDB;""",
                
                # 3. DIMENSÃO FILME (DESCRIÇÃO)
                """CREATE TABLE IF NOT EXISTS Dim_Filme (id_filme INT AUTO_INCREMENT PRIMARY KEY, titulo VARCHAR(255) NOT NULL, link_imdb VARCHAR(500), duracao_minutos INT, classificacao_mpa VARCHAR(20)) ENGINE=InnoDB;""",
                
                # 4. TABELA FATO (MÉTRICAS E FKs)
                """
                CREATE TABLE IF NOT EXISTS Fato_Filme (
                    id_filme INT PRIMARY KEY, id_tempo INT,
                    nota_imdb DECIMAL(3,1), votos_imdb INT, orcamento DECIMAL(15,2),
                    bilheteria_mundial DECIMAL(15,2), bilheteria_eua_canada DECIMAL(15,2), bilheteria_abertura DECIMAL(15,2),
                    vitorias_premios INT, nominacoes_premios INT, vitorias_oscar INT,
                    FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE,
                    FOREIGN KEY (id_tempo) REFERENCES Dim_Tempo(id_tempo)
                ) ENGINE=InnoDB;
                """,
                # 5. TABELAS ASSOCIATIVAS (Bridge Tables) - REFERENCIAM CORRETAMENTE A Dim_Filme
                """CREATE TABLE IF NOT EXISTS filme_estrela (id_filme INT, id_pessoa INT, ordem_credito INT DEFAULT NULL, PRIMARY KEY (id_filme, id_pessoa), FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE, FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS filme_diretor (id_filme INT, id_pessoa INT, PRIMARY KEY (id_filme, id_pessoa), FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE, FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS filme_roteirista (id_filme INT, id_pessoa INT, PRIMARY KEY (id_filme, id_pessoa), FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE, FOREIGN KEY (id_pessoa) REFERENCES Pessoas(id_pessoa) ON DELETE CASCADE) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS filme_genero (id_filme INT, id_genero INT, PRIMARY KEY (id_filme, id_genero), FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE, FOREIGN KEY (id_genero) REFERENCES Generos(id_genero) ON DELETE CASCADE) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS filme_pais_origem (id_filme INT, id_pais INT, PRIMARY KEY (id_filme, id_pais), FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE, FOREIGN KEY (id_pais) REFERENCES Paises(id_pais) ON DELETE CASCADE) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS filme_empresa_producao (id_filme INT, id_empresa INT, PRIMARY KEY (id_filme, id_empresa), FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE, FOREIGN KEY (id_empresa) REFERENCES Empresas(id_empresa) ON DELETE CASCADE) ENGINE=InnoDB;""",
                """CREATE TABLE IF NOT EXISTS filme_idioma (id_filme INT, id_idioma INT, PRIMARY KEY (id_filme, id_idioma), FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE, FOREIGN KEY (id_idioma) REFERENCES Idiomas(id_idioma) ON DELETE CASCADE) ENGINE=InnoDB;"""
            ]
            for sql in sqls:
                self.cursor.execute(sql)
            self.connection.commit()
            print("[INFO] Tabelas criadas com sucesso.")
        except Exception as e:
            print(f"[ERRO] Erro ao criar tabelas: {e}")
            self.connection.rollback()
            
    # ----------------------------
    # Inserção de dados (Funções Auxiliares)
    # ----------------------------
    def inserir_ou_obter_id(self, tabela, campo_nome, valor, campo_id):
        if not valor or pd.isna(valor) or str(valor).strip() == '':
            return None
        valor = str(valor).strip()
        
        self.cursor.execute(f"SELECT {campo_id} FROM {tabela} WHERE {campo_nome} = %s", (valor,))
        resultado = self.cursor.fetchone()
        if resultado:
            return resultado[0]
        
        # Caso especial para Dim_Tempo
        if tabela == 'Dim_Tempo':
            self.cursor.execute(f"INSERT IGNORE INTO {tabela} ({campo_id}, {campo_nome}) VALUES (%s, %s)", (valor, valor))
            return valor
            
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
    # Processamento de Filme (ETL para o DW)
    # ----------------------------
    def processar_filme(self, row, numero_linha=None):
        try:
            titulo = None if pd.isna(row.get('title')) else row.get('title')
            ano_lancamento = int(row['year']) if pd.notna(row.get('year')) else None

            if numero_linha:
                print(f"[INFO] Processando filme #{numero_linha}: {titulo}")

            # 1. INSERIR NA DIM_FILME (Atributos Descritivos)
            query_dim_filme = "INSERT INTO Dim_Filme (titulo, link_imdb, duracao_minutos, classificacao_mpa) VALUES (%s, %s, %s, %s)"
            valores_dim = (titulo, row.get('link'), self.limpar_duracao(row.get('duration')), row.get('rating_mpa'))
            self.cursor.execute(query_dim_filme, valores_dim)
            id_filme = self.cursor.lastrowid 

            # 2. INSERIR NA DIM_TEMPO (Ano de Lançamento)
            id_tempo = self.inserir_ou_obter_id('Dim_Tempo', 'ano_lancamento', ano_lancamento, 'id_tempo')
            
            # 3. INSERIR NA FATO_FILME (Métricas e FKs)
            query_fato_filme = """
                INSERT INTO Fato_Filme (
                    id_filme, id_tempo, nota_imdb, votos_imdb, orcamento,
                    bilheteria_mundial, bilheteria_eua_canada, bilheteria_abertura,
                    vitorias_premios, nominacoes_premios, vitorias_oscar
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            valores_fato = (
                id_filme, id_tempo, self.limpar_valor_numerico(row.get('rating_imdb')), self.limpar_valor_numerico(row.get('vote')), self.limpar_valor_numerico(row.get('budget')),
                self.limpar_valor_numerico(row.get('gross_world_wide')), self.limpar_valor_numerico(row.get('gross_us_canada')), self.limpar_valor_numerico(row.get('gross_opening_weekend')),
                self.limpar_valor_numerico(row.get('win')), self.limpar_valor_numerico(row.get('nomination')), self.limpar_valor_numerico(row.get('oscar'))
            )
            self.cursor.execute(query_fato_filme, valores_fato)
            
            # 4. INSERIR NAS TABELAS PONTE (Bridge Tables)
            dim_id_map = {'Generos': 'id_genero', 'Paises': 'id_pais', 'Empresas': 'id_empresa', 'Idiomas': 'id_idioma', 'Pessoas': 'id_pessoa'}
            def inserir_associativa(tabela_assoc, tabela_dim, campo_nome, coluna_csv):
                coluna_id = dim_id_map[tabela_dim]
                for v in self.processar_lista_valores(row.get(coluna_csv,'')):
                    id_dim = self.inserir_ou_obter_id(tabela_dim, campo_nome, v, coluna_id) 
                    if id_dim:
                        self.cursor.execute(f"INSERT IGNORE INTO {tabela_assoc} (id_filme, {coluna_id}) VALUES (%s,%s)", (id_filme, id_dim))

            # Associações de Pessoas
            for i, estrela in enumerate(self.processar_lista_valores(row.get('star',''))):
                id_pessoa = self.inserir_ou_obter_id('Pessoas','nome_pessoa', estrela, 'id_pessoa')
                if id_pessoa:
                    self.cursor.execute("INSERT IGNORE INTO filme_estrela (id_filme,id_pessoa,ordem_credito) VALUES (%s,%s,%s)", (id_filme,id_pessoa,i+1))
            for diretor in self.processar_lista_valores(row.get('director','')):
                id_pessoa = self.inserir_ou_obter_id('Pessoas','nome_pessoa', diretor, 'id_pessoa')
                if id_pessoa:
                    self.cursor.execute("INSERT IGNORE INTO filme_diretor (id_filme,id_pessoa) VALUES (%s,%s)", (id_filme,id_pessoa))
            for roteirista in self.processar_lista_valores(row.get('writer','')):
                id_pessoa = self.inserir_ou_obter_id('Pessoas','nome_pessoa', roteirista, 'id_pessoa')
                if id_pessoa:
                    self.cursor.execute("INSERT IGNORE INTO filme_roteirista (id_filme,id_pessoa) VALUES (%s,%s)", (id_filme,id_pessoa))

            # Associações Gerais
            inserir_associativa('filme_genero','Generos','nome_genero','genre')
            inserir_associativa('filme_pais_origem','Paises','nome_pais','country_origin')
            inserir_associativa('filme_empresa_producao','Empresas','nome_empresa','production_company')
            inserir_associativa('filme_idioma','Idiomas','nome_idioma','language')

            self.connection.commit()
            return True
        except Exception as e:
            print(f"[ERRO] Ao processar filme '{titulo}': {e}")
            self.connection.rollback()
            return False


    # ----------------------------
    # Normalização CSV com logs e chunks
    # ----------------------------
    def normalizar_csv(self, arquivo_csv, limite=None):
        if not os.path.exists(arquivo_csv):
            print(f"[ERRO] Arquivo não encontrado: {arquivo_csv}")
            return
        
        print(f"[INFO] Iniciando leitura do CSV: {arquivo_csv}")
        chunk_size = 100
        total = 0
        try:
            for chunk in pd.read_csv(arquivo_csv, chunksize=chunk_size):
                
                # Interrompe o loop de chunks se o limite for atingido
                if limite is not None and total >= limite:
                    break
                    
                print(f"[INFO] Processando linhas {total+1} até {total+len(chunk)}")
                
                for idx, row in chunk.iterrows():
                    # Interrompe o loop interno se o limite for atingido
                    if limite is not None and total >= limite:
                        break
                        
                    self.processar_filme(row, total+idx+1)
                    total += 1 # Incrementa o total de filmes processados
                    
        except Exception as e:
            print(f"[ERRO GERAL] Ocorreu um erro durante a leitura/processamento do CSV: {e}")
            return

        print(f"[INFO] Normalização concluída! Total de filmes processados: {total}")

# ----------------------------
# EXECUÇÃO
# ----------------------------
if __name__ == "__main__":
    arquivo_csv = "filmes_ingles_apos_2000.csv"
    
    # 1. Definir o nome do banco para o Data Warehouse
    DB_NAME = 'filmes_dw' 
    
    # 2. Definir o limite
    LIMITE_PROCESSAMENTO = 5000 # Use None para processar todos
    
    # Inicializa o normalizador com o nome do DB
    normalizer = FilmesNormalizer(user='root', password='root123', database=DB_NAME)
    
    if normalizer.conectar_banco(criar_db=True):
        
        # Este é o ponto onde as tabelas DW são criadas
        normalizer.criar_tabelas() 
        
        normalizer.normalizar_csv(arquivo_csv, limite=LIMITE_PROCESSAMENTO)
        normalizer.desconectar_banco()
        print(f"[INFO] Banco DW '{DB_NAME}' criado e dados inseridos com sucesso!")