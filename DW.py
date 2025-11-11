import pandas as pd
import pymysql
import re
import os

class FilmesNormalizer:
    def __init__(self, host='localhost', user='root', password='', database='filmes_dw'): # Mudei o DB para filmes_dw
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
                self.cursor.execute(f"DROP DATABASE IF EXISTS {self.database}")
                print(f"[INFO] Banco '{self.database}' antigo removido (se existia).")
                self.cursor.execute(f"CREATE DATABASE {self.database}")
                print(f"[INFO] Banco '{self.database}' criado.")
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
                # ----------------------------------------------------
                # 1. TABELAS DE DIMENSÃO SIMPLES
                # ----------------------------------------------------
                """
                CREATE TABLE IF NOT EXISTS Dim_Pessoa (
                    id_pessoa INT AUTO_INCREMENT PRIMARY KEY,
                    nome_pessoa VARCHAR(255) NOT NULL
                ) ENGINE=InnoDB;
                """,
                """
                CREATE TABLE IF NOT EXISTS Dim_Diretor (
                    id_diretor INT AUTO_INCREMENT PRIMARY KEY,
                    id_pessoa INT NOT NULL,
                    FOREIGN KEY (id_pessoa) REFERENCES Dim_Pessoa(id_pessoa) ON DELETE CASCADE
                ) ENGINE=InnoDB;
                """,
                """
                CREATE TABLE IF NOT EXISTS Dim_Roteirista (
                    id_roteirista INT AUTO_INCREMENT PRIMARY KEY,
                    id_pessoa INT NOT NULL,
                    FOREIGN KEY (id_pessoa) REFERENCES Dim_Pessoa(id_pessoa) ON DELETE CASCADE
                ) ENGINE=InnoDB;
                """,
                """
                CREATE TABLE IF NOT EXISTS Dim_Estrela (
                    id_estrela INT AUTO_INCREMENT PRIMARY KEY,
                    id_pessoa INT NOT NULL,
                    FOREIGN KEY (id_pessoa) REFERENCES Dim_Pessoa(id_pessoa) ON DELETE CASCADE
                ) ENGINE=InnoDB;
                """,
                """
                CREATE TABLE IF NOT EXISTS Dim_Genero (
                    id_genero INT AUTO_INCREMENT PRIMARY KEY,
                    nome_genero VARCHAR(100) NOT NULL
                ) ENGINE=InnoDB;
                """,
                """
                CREATE TABLE IF NOT EXISTS Dim_Pais (
                    id_pais INT AUTO_INCREMENT PRIMARY KEY,
                    nome_pais VARCHAR(150) NOT NULL
                ) ENGINE=InnoDB;
                """,
                """
                CREATE TABLE IF NOT EXISTS Dim_Empresa (
                    id_empresa INT AUTO_INCREMENT PRIMARY KEY,
                    nome_empresa VARCHAR(255) NOT NULL
                ) ENGINE=InnoDB;
                """,
                """
                CREATE TABLE IF NOT EXISTS Dim_Idioma (
                    id_idioma INT AUTO_INCREMENT PRIMARY KEY,
                    nome_idioma VARCHAR(150) NOT NULL
                ) ENGINE=InnoDB;
                """,
                # ----------------------------------------------------
                # 2. DIMENSÃO TEMPO (Essencial para DW)
                # O id_tempo será o próprio ano para simplificação
                # ----------------------------------------------------
                """
                CREATE TABLE IF NOT EXISTS Dim_Tempo (
                    id_tempo INT PRIMARY KEY,
                    ano_lancamento INT NOT NULL,
                    -- Adicione mais atributos de tempo se necessário (ex: trimestre, decada)
                    UNIQUE KEY uk_ano_lancamento (ano_lancamento)
                ) ENGINE=InnoDB;
                """,
                # ----------------------------------------------------
                # 3. DIMENSÃO FILME (Atributos Descritivos)
                # ----------------------------------------------------
                """
                CREATE TABLE IF NOT EXISTS Dim_Filme (
                    id_filme INT AUTO_INCREMENT PRIMARY KEY, 
                    titulo VARCHAR(255) NOT NULL,
                    link_imdb VARCHAR(500),
                    duracao_minutos INT,
                    classificacao_mpa VARCHAR(20)
                ) ENGINE=InnoDB;
                """,
                # ----------------------------------------------------
                # 4. TABELA FATO (Centro do Star Schema - Métricas e FKs)
                # ----------------------------------------------------
                """
                CREATE TABLE IF NOT EXISTS Fato_Filme (
                    id_fato INT AUTO_INCREMENT PRIMARY KEY,
                    id_filme INT NOT NULL,
                    id_tempo INT,
                    id_genero INT,
                    id_pais INT,
                    id_empresa INT,
                    id_idioma INT,
                    id_diretor INT,
                    id_roteirista INT,
                    id_estrela INT,
                    
                    nota_imdb DECIMAL(3,1),
                    votos_imdb INT,
                    orcamento DECIMAL(15,2),
                    bilheteria_mundial DECIMAL(15,2),
                    bilheteria_eua_canada DECIMAL(15,2),
                    bilheteria_abertura DECIMAL(15,2),
                    vitorias_premios INT,
                    nominacoes_premios INT,
                    vitorias_oscar INT,
                    
                    FOREIGN KEY (id_filme) REFERENCES Dim_Filme(id_filme) ON DELETE CASCADE,
                    FOREIGN KEY (id_tempo) REFERENCES Dim_Tempo(id_tempo),
                    FOREIGN KEY (id_genero) REFERENCES Dim_Genero(id_genero),
                    FOREIGN KEY (id_pais) REFERENCES Dim_Pais(id_pais),
                    FOREIGN KEY (id_empresa) REFERENCES Dim_Empresa(id_empresa),
                    FOREIGN KEY (id_idioma) REFERENCES Dim_Idioma(id_idioma),
                    FOREIGN KEY (id_diretor) REFERENCES Dim_Diretor(id_diretor),
                    FOREIGN KEY (id_roteirista) REFERENCES Dim_Roteirista(id_roteirista),
                    FOREIGN KEY (id_estrela) REFERENCES Dim_Estrela(id_estrela)
                ) ENGINE=InnoDB;
                """,

            ]
            for sql in sqls:
                self.cursor.execute(sql)
            self.connection.commit()
            print("[INFO] Tabelas criadas com sucesso.")
        except Exception as e:
            print(f"[ERRO] Erro ao criar tabelas: {e}")
            self.connection.rollback()

    # ----------------------------
    # Inserção de dados
    # ----------------------------
    # Mantida a função de dimensão (funciona para tempo, pessoas, generos, etc.)
    def inserir_ou_obter_id(self, tabela, campo_nome, valor, campo_id):
        if not valor or pd.isna(valor) or str(valor).strip() == '':
            return None
        valor = str(valor).strip()
        
        self.cursor.execute(f"SELECT {campo_id} FROM {tabela} WHERE {campo_nome} = %s", (valor,))
        resultado = self.cursor.fetchone()
        if resultado:
            return resultado[0]
        
        # Caso especial para Dim_Tempo, onde o ID é o próprio ano
        if tabela == 'Dim_Tempo':
            # Se não existir, insere o ano como ID e como valor
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
            # print(f"[ALERTA] Valor numérico inválido: {valor}") # Comentar para reduzir logs
            return None

    def processar_filme(self, row, numero_linha=None):
        try:
            titulo = None if pd.isna(row.get('title')) else row.get('title')
            ano_lancamento = int(row['year']) if pd.notna(row.get('year')) else None

            if numero_linha:
                print(f"[INFO] Processando filme #{numero_linha}: {titulo}")

            # -----------------------------------------------------------------
            # 1. INSERIR NA DIM_FILME (Atributos Descritivos)
            # -----------------------------------------------------------------
            query_dim_filme = """
                INSERT INTO Dim_Filme (
                    titulo, link_imdb, duracao_minutos, classificacao_mpa
                ) VALUES (%s, %s, %s, %s)
            """
            valores_dim = (
                titulo,
                None if pd.isna(row.get('link')) else row.get('link'),
                self.limpar_duracao(row.get('duration')),
                None if pd.isna(row.get('rating_mpa')) else row.get('rating_mpa')
            )
            self.cursor.execute(query_dim_filme, valores_dim)
            id_filme = self.cursor.lastrowid # Este é agora o PK para Dim_Filme e Fato_Filme

            # -----------------------------------------------------------------
            # 2. INSERIR NA DIM_TEMPO (Ano de Lançamento)
            # -----------------------------------------------------------------
            id_tempo = None
            if ano_lancamento is not None:
                # O id_tempo será o próprio ano (Simplificação)
                id_tempo = self.inserir_ou_obter_id('Dim_Tempo', 'ano_lancamento', ano_lancamento, 'id_tempo')
            
            # -----------------------------------------------------------------
            # 3. OBTER IDS DAS DIMENSÕES (Pegando o primeiro de cada lista)
            # -----------------------------------------------------------------
            # Gênero (pega o primeiro da lista)
            id_genero = None
            generos = self.processar_lista_valores(row.get('genre',''))
            if generos:
                id_genero = self.inserir_ou_obter_id('Dim_Genero', 'nome_genero', generos[0], 'id_genero')
            
            # País (pega o primeiro da lista)
            id_pais = None
            paises = self.processar_lista_valores(row.get('country_origin',''))
            if paises:
                id_pais = self.inserir_ou_obter_id('Dim_Pais', 'nome_pais', paises[0], 'id_pais')
            
            # Empresa (pega a primeira da lista)
            id_empresa = None
            empresas = self.processar_lista_valores(row.get('production_company',''))
            if empresas:
                id_empresa = self.inserir_ou_obter_id('Dim_Empresa', 'nome_empresa', empresas[0], 'id_empresa')
            
            # Idioma (pega o primeiro da lista)
            id_idioma = None
            idiomas = self.processar_lista_valores(row.get('language',''))
            if idiomas:
                id_idioma = self.inserir_ou_obter_id('Dim_Idioma', 'nome_idioma', idiomas[0], 'id_idioma')
            
            # Diretor (pega o primeiro da lista)
            id_diretor = None
            diretores = self.processar_lista_valores(row.get('director',''))
            if diretores:
                id_pessoa_diretor = self.inserir_ou_obter_id('Dim_Pessoa', 'nome_pessoa', diretores[0], 'id_pessoa')
                if id_pessoa_diretor:
                    # Verifica se já existe na Dim_Diretor
                    self.cursor.execute("SELECT id_diretor FROM Dim_Diretor WHERE id_pessoa = %s", (id_pessoa_diretor,))
                    resultado = self.cursor.fetchone()
                    if resultado:
                        id_diretor = resultado[0]
                    else:
                        self.cursor.execute("INSERT INTO Dim_Diretor (id_pessoa) VALUES (%s)", (id_pessoa_diretor,))
                        id_diretor = self.cursor.lastrowid
            
            # Roteirista (pega o primeiro da lista)
            id_roteirista = None
            roteiristas = self.processar_lista_valores(row.get('writer',''))
            if roteiristas:
                id_pessoa_roteirista = self.inserir_ou_obter_id('Dim_Pessoa', 'nome_pessoa', roteiristas[0], 'id_pessoa')
                if id_pessoa_roteirista:
                    # Verifica se já existe na Dim_Roteirista
                    self.cursor.execute("SELECT id_roteirista FROM Dim_Roteirista WHERE id_pessoa = %s", (id_pessoa_roteirista,))
                    resultado = self.cursor.fetchone()
                    if resultado:
                        id_roteirista = resultado[0]
                    else:
                        self.cursor.execute("INSERT INTO Dim_Roteirista (id_pessoa) VALUES (%s)", (id_pessoa_roteirista,))
                        id_roteirista = self.cursor.lastrowid
            
            # Estrela (pega a primeira da lista)
            id_estrela = None
            estrelas = self.processar_lista_valores(row.get('star',''))
            if estrelas:
                id_pessoa_estrela = self.inserir_ou_obter_id('Dim_Pessoa', 'nome_pessoa', estrelas[0], 'id_pessoa')
                if id_pessoa_estrela:
                    # Verifica se já existe na Dim_Estrela
                    self.cursor.execute("SELECT id_estrela FROM Dim_Estrela WHERE id_pessoa = %s", (id_pessoa_estrela,))
                    resultado = self.cursor.fetchone()
                    if resultado:
                        id_estrela = resultado[0]
                    else:
                        self.cursor.execute("INSERT INTO Dim_Estrela (id_pessoa) VALUES (%s)", (id_pessoa_estrela,))
                        id_estrela = self.cursor.lastrowid

            # -----------------------------------------------------------------
            # 4. INSERIR NA FATO_FILME (Métricas e todas as FKs)
            # -----------------------------------------------------------------
            query_fato_filme = """
                INSERT INTO Fato_Filme (
                    id_filme, id_tempo, id_genero, id_pais, id_empresa, id_idioma,
                    id_diretor, id_roteirista, id_estrela,
                    nota_imdb, votos_imdb, orcamento,
                    bilheteria_mundial, bilheteria_eua_canada, bilheteria_abertura,
                    vitorias_premios, nominacoes_premios, vitorias_oscar
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            valores_fato = (
                id_filme,
                id_tempo,
                id_genero,
                id_pais,
                id_empresa,
                id_idioma,
                id_diretor,
                id_roteirista,
                id_estrela,
                self.limpar_valor_numerico(row.get('rating_imdb')),
                self.limpar_valor_numerico(row.get('vote')),
                self.limpar_valor_numerico(row.get('budget')),
                self.limpar_valor_numerico(row.get('gross_world_wide')),
                self.limpar_valor_numerico(row.get('gross_us_canada')),
                self.limpar_valor_numerico(row.get('gross_opening_weekend')),
                self.limpar_valor_numerico(row.get('win')),
                self.limpar_valor_numerico(row.get('nomination')),
                self.limpar_valor_numerico(row.get('oscar'))
            )
            self.cursor.execute(query_fato_filme, valores_fato)
            id_fato = self.cursor.lastrowid

            self.connection.commit() # commit por filme
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
                    
            # A exceção para [ERRO GERAL] foi mantida, mas a lógica de limite está acima

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
    DB_NAME = 'filmes' 
    
    # 2. Definir o limite
    LIMITE_PROCESSAMENTO = 500 # Use None para processar todos
    
    normalizer = FilmesNormalizer(user='user', password='user123', database=DB_NAME)
    
    if normalizer.conectar_banco(criar_db=True):
        # O banco será recriado automaticamente (DROP + CREATE)
        normalizer.criar_tabelas() 
        
        normalizer.normalizar_csv(arquivo_csv, limite=LIMITE_PROCESSAMENTO)
        normalizer.desconectar_banco()
        print(f"[INFO] Banco DW '{DB_NAME}' criado e dados inseridos com sucesso!")