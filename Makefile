.PHONY: up down build test run-local db-shell

# --- Docker Commands ---
up:
	@echo "Starting the Agentic Pipeline (Postgres + FastAPI)..."
	docker-compose -f infra/docker-compose.yml up -d

down:
	@echo "Stopping the Agentic Pipeline..."
	docker-compose -f infra/docker-compose.yml down

build:
	@echo "Rebuilding the API image..."
	docker-compose -f infra/docker-compose.yml build

db-shell:
	@echo "Entering PostgreSQL shell..."
	docker exec -it $$(docker-compose -f infra/docker-compose.yml ps -q db) psql -U admin -d agentic_db

# --- Local Development Commands ---
run-local:
	@echo "Running FastAPI locally (make sure DB is up via docker or otherwise)..."
	python -m src.main

run-hitl:
	@echo "Running Streamlit Human-in-the-Loop interface..."
	streamlit run src/hitl_app.py

test:
	@echo "Running pytest suite..."
	PYTHONPATH=. pytest -v tests/
