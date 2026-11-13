# Etapa 1: Build del Frontend React con Vite y TypeScript
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Etapa 2: Runtime en Python con FastAPI
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_PATH=/app/data/evaluations.db

WORKDIR /app

# Crear usuario no-root para ejecutar el servicio de forma segura
RUN useradd --create-home --shell /bin/bash appuser

COPY pyproject.toml README.md ./
COPY src ./src
# Copiar el bundle de React compilado a static
COPY --from=frontend-builder /app/src/api/static ./src/api/static

RUN pip install --upgrade pip && pip install .

RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
