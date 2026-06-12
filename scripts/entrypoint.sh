#!/bin/sh
set -e

echo "Aguardando PostgreSQL..."
until python -c "
import os, sys
from sqlalchemy import create_engine, text
url = os.environ.get('DATABASE_URL', '')
if not url:
    sys.exit(1)
engine = create_engine(url)
with engine.connect() as conn:
    conn.execute(text('SELECT 1'))
" 2>/dev/null; do
  sleep 2
done

echo "Aplicando migrations..."
alembic upgrade head

echo "Iniciando Fedizine na porta ${APP_PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT:-8000}"
