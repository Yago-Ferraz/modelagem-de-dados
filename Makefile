VENV = venv
PIP = $(VENV)\Scripts\pip.exe
PYTHON = $(VENV)\Scripts\python.exe
DC=docker-compose

# Criar a venv
criar_venv:
	python -m venv $(VENV)

# Ativar a venv (abre um terminal CMD já ativado)
ativar:
	@cmd /k "$(VENV)\Scripts\activate.bat"

# Instalar pacotes do requirements.txt
instalar:
	$(PIP) install -r requirements.txt

# Atualizar todos os pacotes instalados
atualizar_requirements:
	@echo "Atualizando requirements.txt com os pacotes instalados na venv..."
	$(PIP) freeze > requirements.txt
	@echo "Concluido!"

# Listar pacotes instalados
listar:
	$(PIP) list

listar:
	$(PIP) list

up:
	$(DC) up -d

rebuild:
	$(DC) down
	$(DC) build --no-cache
	$(DC) up -d

shell:
	docker exec -it filmes_db mysql -u root -p

apagar:
	$(DC) down
	docker volume rm modelagem-de-dados_filmes_data
