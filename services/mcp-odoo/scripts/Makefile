IMAGE?=mcp-odoo
TAG?=latest

run:
	uvicorn server:app --reload --port $${PORT:-8000}

docker-build:
	docker build -t $(IMAGE):$(TAG) .

docker-run:
	docker run --rm -it -p 8000:8000 --env-file .env $(IMAGE):$(TAG)
