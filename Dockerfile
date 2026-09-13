FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv sync --no-dev

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

ENV PYTHONPATH=/app/src

CMD ["sh", "-c", "uv run gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind ${APP_HOST:-0.0.0.0}:${APP_PORT:-8000} --workers 4 --timeout 120"]
