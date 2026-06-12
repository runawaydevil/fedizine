Fedizine
========

A tiny press for the Fediverse. Collects RSS/ActivityPub fragments, curates at the Editorial Desk, publishes a monthly web issue and A5 PDF.

<p align="center">
  <img src="assets/logo.png" width="320" alt="Fedizine">
</p>

Stack: Python 3.12, FastAPI, PostgreSQL, Redis, Celery, Jinja2, WeasyPrint.

Install (Docker)
----------------

    cp .env.example .env
    docker compose up --build -d

Open http://localhost:4927

Editorial Desk: http://localhost:4927/desk/login

First user:

    docker compose exec app fedizine create-user --password "your-password"

Workflow: sources -> collect -> fragments -> issues -> proof -> publish

CLI:

    docker compose exec app fedizine collect
    docker compose exec app fedizine score --month 2026-06
    docker compose exec app fedizine build-edition --month 2026-06
    docker compose exec app fedizine build-pdf --month 2026-06
    docker compose exec app fedizine publish --month 2026-06

Public: /  /archive/  /feed.xml  /YYYY-MM/  /YYYY-MM/zine.pdf

Desk: /desk/login  /desk/sources  /desk/fragments  /desk/issues  /desk/proof

Old /mesa/* URLs are gone (404).

Local dev (without Docker):

    pip install -e .
    alembic upgrade head
    uvicorn app.main:app --reload --port 8000

Published files land in storage/public/ (HTML snapshots and PDFs).

