FROM python:3.12-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

# Install dependencies — cached unless pyproject.toml changes
COPY pyproject.toml .
RUN uv sync --no-dev

# Copy source (overridden by volume mount in dev)
COPY app/ app/

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
