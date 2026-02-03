#!/usr/bin/env bash
# Script para ejecutar el servidor MCP-Odoo con el entorno virtual correcto

# Navegar al directorio del script
cd "$(dirname "$0")"

# Verificar si uv está instalado para usar 'uv run'
if command -v uv >/dev/null 2>&1; then
    echo "🚀 Iniciando servidor con 'uv run'..."
    uv run python server.py
else
    # Si no hay uv, intentar usar el entorno virtual directamente
    if [ -d ".venv" ]; then
        echo "🐍 Iniciando servidor con entorno virtual local (.venv)..."
        ./.venv/bin/python server.py
    else
        echo "❌ Error: No se encontró el entorno virtual (.venv) ni 'uv'."
        echo "Por favor, instala las dependencias primero con 'uv sync' o 'pip install -e .'"
        exit 1
    fi
fi
