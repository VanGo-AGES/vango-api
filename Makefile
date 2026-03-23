.DEFAULT_GOAL := help

.PHONY: setup docker-up docker-down no-docker-setup run-local test test-failed test-cov show-cov clean-cov clean lint help

# 0.1 Subir infraestrutura e API com Docker Compose
docker-up:
	@echo "🐳 Subindo containers (db + api)..."
	docker compose up -d --build db api

# 0.1 Derrubar ambiente Docker
docker-down:
	@echo "🛑 Derrubando containers..."
	docker compose down

# 0.1 Preparar ambiente local usando Docker Compose (sem dev container)
setup:
	@if [ ! -f .env ]; then cp .env.example .env; echo "📄 .env criado a partir de .env.example"; fi
	@$(MAKE) docker-up
	@echo "🗃️ Aplicando migrations..."
	docker compose exec -T api alembic upgrade head
	@echo "✅ Ambiente pronto! API: http://localhost:8000/docs"

# 0.2 Preparar ambiente sem Docker (usa Python local + DB externo/local)
no-docker-setup:
	@command -v python3 >/dev/null 2>&1 || { echo "❌ python3 não encontrado."; exit 1; }
	@python3 -m venv --help >/dev/null 2>&1 || { echo "❌ Módulo venv indisponível. Instale o pacote python3-venv."; exit 1; }
	@if [ ! -d .venv ]; then python3 -m venv .venv && echo "✅ .venv criado"; fi
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@if [ ! -f .env ]; then cp .env.example .env; echo "📄 .env criado a partir de .env.example"; fi
	@grep -q '^DATABASE_URL=' .env || { echo "❌ Defina DATABASE_URL no .env para rodar sem Docker."; exit 1; }
	@echo "🗃️ Aplicando migrations localmente..."
	@.venv/bin/alembic upgrade head
	@echo "✅ Ambiente local pronto (sem Docker)."

# 0.2 Rodar API local sem Docker
run-local:
	@command -v .venv/bin/uvicorn >/dev/null 2>&1 || { echo "❌ .venv não configurado. Rode: make no-docker-setup"; exit 1; }
	@.venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 1. Rodar testes normal (Rápido, sem HTML)
test:
	pytest tests/

# 2. Rodar apenas testes falhados (Otimização para Debug)
test-failed:
	pytest --lf tests/

# 3. Rodar testes criando o HTML (Visão completa)
test-cov:
	pytest --cov=src --cov-report=html:cov_html tests/

# 4. Executar/Servir o HTML de cobertura
show-cov:
	@echo "🚀 Servindo cobertura em http://localhost:8080..."
	@cd cov_html && python3 -m http.server 8080

# 5. Limpar APENAS o HTML de cobertura
clean-cov:
	rm -rf cov_html/
	rm -f .coverage
	@echo "🧹 Relatório de cobertura removido."

# 6. Limpar tudo (Lixos gerais, caches e cobertura)
clean: clean-cov
	rm -rf .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✨ Todo o lixo de compilação foi limpo!"

# 7. Rodar o lint
lint:
	ruff check . --fix

# Menu de ajuda dinâmico
help:
	@echo "VanTrack CLI - Escolha uma ação:"
	@echo "  make docker-up   - Sobe db/api com Docker Compose"
	@echo "  make docker-down - Derruba os containers do projeto"
	@echo "  make setup       - Prepara .env, sobe db/api no Docker e aplica migrations"
	@echo "  make no-docker-setup - Prepara .venv, instala libs e aplica migrations sem Docker"
	@echo "  make run-local   - Sobe a API local usando .venv (sem Docker)"
	@echo "  make test        - Executa testes rapidamente (sem coverage)"
	@echo "  make test-failed - Executa apenas os testes que falharam na última rodada"
	@echo "  make test-cov    - Executa testes e gera relatório HTML"
	@echo "  make show-cov    - Inicia servidor para ver o HTML (porta 8080)"
	@echo "  make clean-cov   - Remove apenas os arquivos de cobertura"
	@echo "  make clean       - Remove caches, pycache e cobertura"
	@echo "  make lint        - Formata e corrige estilo com Ruff"
