# TurfBook — Owner

Owner microservice for TurfBook, a synthetic grass court booking platform. It owns the
owner profile (RUC, identity documents, address). Built with FastAPI following hexagonal
architecture, designed to run serverless on AWS Lambda.

## Getting started

```bash
conda create -n turfbook-owner-env python=3.12
conda activate turfbook-owner-env
pip install -r requirements/local.txt
pre-commit install

cp .env.example .env
docker compose up --build
# API → http://localhost:8001   Docs → http://localhost:8001/docs

docker compose exec app pytest
pre-commit run --all-files
```
