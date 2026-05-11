FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

# Install dependencies — cached unless pyproject.toml changes
COPY pyproject.toml .
RUN uv sync --no-dev --extra scraping
RUN uv run playwright install --with-deps chromium

# Copy source and migration files
COPY app/ app/
COPY migrations/ migrations/
COPY alembic.ini .

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
