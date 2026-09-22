.PHONY: help up down logs backend-install migrate seed test lint frontend-install frontend-dev

help:
	@echo "make up            - docker compose up --build"
	@echo "make down          - docker compose down -v"
	@echo "make logs          - follow container logs"
	@echo "make backend-install - install python deps"
	@echo "make migrate       - alembic upgrade head"
	@echo "make seed          - seed demo data"
	@echo "make test          - run backend tests"
	@echo "make frontend-dev  - run the vite dev server"

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f

backend-install:
	cd backend && pip install -r requirements.txt

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.db.seed

test:
	cd backend && pytest

lint:
	cd backend && ruff check app tests

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev
