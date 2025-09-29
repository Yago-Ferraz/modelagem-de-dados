# Projeto Filmes

Este projeto realiza a **normalização e inserção de dados de filmes** em um banco de dados MySQL utilizando Python, Pandas e SQLAlchemy. Ele inclui scripts para criação de tabelas, tabelas associativas e inserção de dados.

---

## 🔹 Pré-requisitos

* Python 3.10+
* Docker e Docker Compose (opcional, recomendado para MySQL)
* Pip (gerenciador de pacotes Python)

---

## 🔹 Setup do ambiente Python

1. **Criar virtual environment:**

```bash
make criar_venv
```

2. **Ativar virtual environment:**

```bash
make ativar
```

3. **Instalar dependências:**

```bash
make instalar
```

4. **Atualizar `requirements.txt` (opcional):**

```bash
make atualizar_requirements
```

5. **Listar pacotes instalados (opcional):**

```bash
make listar
```

---

## 🔹 Rodando o MySQL com Docker

O projeto inclui um `docker-compose.yml` para criar um container MySQL.

1. **Subir o container:**

```bash
make up
```

2. **Reconstruir o container (caso queira resetar tudo):**

```bash
make rebuild
```

O MySQL estará disponível em `localhost:33016` com os seguintes dados:

* Usuário root: `root123`
* Banco: `filmes`
* Usuário comum: `user` / senha: `user123`

---

## 🔹 Conectando no MySQL Workbench

* Host: `localhost`
* Porta: `33016`
* Usuário: `user`
* Senha: `user123`
* Banco: `filmes`

---

## 🔹 Estrutura do banco

* **Tabela principal:** `movies`
* **Tabelas de dimensão:** `pessoas`, `generos`, `idiomas`, `paises`, `empresas`
* **Tabelas associativas:** `filme_equipe`, `filme_genero`, `filme_idioma`, `filme_pais`, `filme_empresa`

---

## 🔹 Executando o script Python

1. Certifique-se de que o ambiente virtual está ativo e que o MySQL está rodando.
2. Execute o script principal:

```bash
python main.py
```

O script vai:

* Normalizar os dados do CSV (`world_imdb_movies_top_movies_per_year.csv`)
* Criar todas as tabelas no banco MySQL
* Inserir os dados normalizados

> ⚠️ Se já existirem tabelas, elas serão apagadas e recriadas.

---

## 🔹 Observações

* O CSV deve estar na pasta `base de dados nao normalizada`.
* As senhas estão diretamente no script para facilitar o uso local/GitHub. Para produção, use variáveis de ambiente ou `.env`.
* Algumas colunas de texto no CSV são limpas para UTF-8 seguro.


