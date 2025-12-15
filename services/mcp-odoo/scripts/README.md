# 🛠️ Scripts de Deployment y Build

Esta carpeta contiene archivos de configuración y scripts para deployment y construcción del servidor MCP-Odoo.

## 📁 Archivos

### `Dockerfile`
Configuración Docker para containerizar el servidor MCP-Odoo.

**Uso:**
```bash
# Desde la raíz de mcp-odoo/
docker build -f scripts/Dockerfile -t mcp-odoo:latest .
docker run --env-file .env -p 8000:8000 mcp-odoo:latest
```

### `build.sh`
Script de build automatizado.

**Uso:**
```bash
cd scripts/
./build.sh
```

### `Makefile`
Targets Make para tareas comunes de desarrollo y deployment.

**Uso:**
```bash
# Ver todos los comandos disponibles
make help

# Ejemplos comunes
make install   # Instalar dependencias
make dev       # Ejecutar en modo desarrollo
make build     # Construir imagen Docker
make test      # Ejecutar tests
```

## 🚀 Deployment

### Desarrollo Local
```bash
# Desde mcp-odoo/
python server.py
```

### Docker
```bash
# Build
docker build -f scripts/Dockerfile -t mcp-odoo .

# Run
docker run --env-file .env -p 8000:8000 mcp-odoo
```

### Producción
```bash
# Con Make
make prod

# O manualmente con uvicorn
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📝 Notas

- Los archivos `.env` nunca deben incluirse en el contenedor
- Usar variables de entorno o secrets para credenciales
- Para deployment en producción, considerar usar `gunicorn` o `uvicorn` con workers
