.PHONY: up down migrate migrate-down test eval run run-worker run-ui deploy lint

up:
	docker-compose -f infra/docker-compose.yml up -d

down:
	docker-compose -f infra/docker-compose.yml down

migrate:
	alembic upgrade head

migrate-down:
	alembic downgrade -1

test:
	pytest tests/unit/ -v --tb=short

test-all:
	pytest tests/ -v --tb=short

eval:
	python evals/run_eval.py

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	python -m app.core.queue worker

run-ui:
	streamlit run app/ui/review_app.py

lint:
	ruff check .

deploy:
	bash infra/deploy.sh
