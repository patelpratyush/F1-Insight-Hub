.PHONY: up down migrate api worker web test
up:
	docker compose up -d --wait postgres redis s3
down:
	docker compose down
migrate:
	uv run --directory packages/db-py alembic upgrade head
api:
	uv run uvicorn f1_api.main:app --reload --port 8000
worker:
	uv run arq f1_worker.settings.WorkerSettings
web:
	pnpm --filter @f1/web dev
test:
	uv run pytest && pnpm test
