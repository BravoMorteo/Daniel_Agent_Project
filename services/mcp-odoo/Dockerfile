FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar archivos de configuración primero (para aprovechar cache de Docker)
COPY pyproject.toml /app/

# Instalar dependencias
RUN pip install --upgrade pip && \
    pip install "mcp[cli]>=1.2.0" \
                "uvicorn>=0.30.0" \
                "starlette>=0.37.0" \
                "pydantic>=2.7.0" \
                "python-dotenv>=1.0.0" \
                "requests>=2.32.5"

# Copiar el resto del código
COPY . /app

EXPOSE 8000

# Comando para iniciar el servidor
CMD ["python", "server.py"]
