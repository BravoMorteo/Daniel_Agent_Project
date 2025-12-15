# MCP-Odoo

Servidor Model Context Protocol (MCP) para integración con Odoo ERP.

## 🎯 Funcionalidad

Este servidor MCP permite interactuar con Odoo ERP a través de:
- 🔍 **Búsqueda** de proyectos, tareas, clientes, ventas
- 📋 **Gestión de CRM** (leads, oportunidades, contactos)
- 💼 **Gestión de Ventas** (pedidos, productos, clientes)
- 📊 **Gestión de Proyectos** (proyectos, tareas, sprints)
- 👥 **Gestión de Usuarios** (usuarios, permisos)

## 📁 Estructura del Proyecto

```
mcp-odoo/
├── server.py                   # 🚀 Punto de entrada principal
├── core/                       # � Módulos principales
│   ├── __init__.py
│   ├── config.py              # ⚙️ Configuración y variables de entorno
│   ├── odoo_client.py         # 🔌 Cliente Odoo (XML-RPC)
│   ├── helpers.py             # 🛠️ Funciones helper (URL, encoding, etc.)
│   └── README.md              # Documentación del core
├── tools/                      # 🔧 Tools modulares de MCP
│   ├── __init__.py            # Autoload de tools
│   ├── crm.py                 # Tools de CRM
│   ├── projects.py            # Tools de proyectos
│   ├── sales.py               # Tools de ventas
│   ├── tasks.py               # Tools de tareas
│   ├── users.py               # Tools de usuarios
│   ├── search.py              # Tools de búsqueda
│   └── README.md              # Documentación de tools
├── scripts/                    # 🛠️ Scripts de deployment
│   ├── Dockerfile             # Configuración Docker
│   ├── Makefile               # Comandos Make
│   ├── build.sh               # Script de build
│   └── README.md              # Documentación de deployment
├── README.md                  # 📖 Este archivo
├── ARCHITECTURE.md            # 🏗️ Arquitectura detallada
└── pyproject.toml             # 📦 Dependencias
```

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

Crea un archivo `.env` con:

```bash
# Odoo Configuration
ODOO_URL=https://tu-odoo.com
ODOO_DB=nombre_base_datos
ODOO_LOGIN=tu_email@ejemplo.com
ODOO_API_KEY=tu_api_key

# Server Configuration (opcional)
PORT=8000
```

### 2. Instalar Dependencias

```bash
# Con pip
pip install -e .

# O con uv (recomendado)
uv pip install -e .
```

### 3. Ejecutar Servidor

```bash
python server.py
```

El servidor estará disponible en: `http://localhost:8000`

## 🔧 Componentes Principales

### `core/config.py`
Maneja toda la configuración del servidor:
- Carga variables de entorno desde `.env`
- Valida configuración requerida
- Expone constantes de configuración

### `core/odoo_client.py`
Cliente XML-RPC para Odoo con métodos CRUD:
- `search()` - Buscar registros
- `search_read()` - Buscar y leer campos
- `read()` - Leer campos de registros
- `create()` - Crear registros
- `write()` - Actualizar registros
- `unlink()` - Eliminar registros

### `core/helpers.py`
Funciones de utilidad:
- `encode_content()` - Formatea respuestas MCP
- `odoo_form_url()` - Genera URLs de formularios Odoo
- `wants_projects()` / `wants_tasks()` - Detecta intención de búsqueda

### `tools/`
Cada archivo en `tools/` define un conjunto de herramientas MCP:

#### `search.py`
- `search` - Busca proyectos y tareas
- `fetch` - Recupera detalles completos

#### `crm.py`
- Tools de gestión de CRM (leads, oportunidades)

#### `projects.py`
- Tools de gestión de proyectos

#### `sales.py`
- Tools de gestión de ventas

#### `tasks.py`
- Tools de gestión de tareas

#### `users.py`
- Tools de gestión de usuarios

## 🔄 Flujo de Datos

```
Cliente MCP (ej: Claude Desktop)
            ↓
      [server.py]
            ↓
      Init Tools
            ↓
    [tools/*.py]
            ↓
   [OdooClient]
            ↓
     XML-RPC
            ↓
      Odoo ERP
```

## 📝 API Endpoints

### HTTP
- `GET /health` - Health check (para Docker/AWS)
- `POST /mcp` - Endpoint MCP (Streamable HTTP)

### MCP Tools

Todos los tools disponibles se cargan automáticamente desde `tools/`.

**Ejemplo de uso (búsqueda):**
```json
{
  "tool": "search",
  "arguments": {
    "query": "proyectos de desarrollo",
    "limit": 10
  }
}
```

**Respuesta:**
```json
{
  "content": [{
    "type": "text",
    "text": "{\"results\": [{\"id\": \"project:1\", \"title\": \"Project · Desarrollo Web\", \"url\": \"...\"}]}"
  }]
}
```

## 🔌 Integración con Claude Desktop

1. Editar `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["/ruta/a/mcp-odoo/server.py"],
      "env": {
        "ODOO_URL": "https://tu-odoo.com",
        "ODOO_DB": "tu_db",
        "ODOO_LOGIN": "tu_login",
        "ODOO_API_KEY": "tu_key"
      }
    }
  }
}
```

2. Reiniciar Claude Desktop

3. Los tools de Odoo estarán disponibles en la interfaz

## 🧪 Testing

```bash
# Ejecutar tests (si existen)
pytest

# Test manual de conexión
python -c "from core import OdooClient; c = OdooClient(); print(c.search('res.users', [], 1))"
```

## 🔐 Seguridad

- Nunca commitear el archivo `.env`
- Las API keys deben mantenerse secretas
- El servidor debe ejecutarse en red privada o con autenticación

## 📦 Dependencias

- `fastmcp` - Framework MCP
- `python-dotenv` - Carga variables de entorno
- `uvicorn` - Servidor ASGI

## 🛠️ Desarrollo

### Agregar Nuevos Tools

1. Crear archivo en `tools/nuevo_tool.py`:

```python
def register(mcp, deps):
    @mcp.tool(name="mi_tool", description="...")
    def mi_tool(arg: str) -> dict:
        odoo = deps["odoo"]
        # ... lógica
        return {"result": "..."}
```

2. Los tools se cargarán automáticamente

### Estructura de un Tool

```python
def register(mcp, deps):
    """
    mcp: Instancia de FastMCP
    deps: {"odoo": OdooClient}
    """
    
    @mcp.tool(name="nombre", description="Descripción")
    def tool_function(param: type) -> dict:
        odoo = deps["odoo"]
        # Implementación
        return resultado
```

## 📚 Recursos

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Odoo XML-RPC API](https://www.odoo.com/documentation/17.0/developer/reference/external_api.html)
- [FastMCP](https://github.com/jlowin/fastmcp)

## 🐛 Debug

Ver logs del servidor:
```bash
python server.py
```

Los logs mostrarán:
- `[INFO]` - Información general
- `[WARN]` - Advertencias (ej: variables faltantes)
- `[ERROR]` - Errores

## 📊 Monitoreo

El endpoint `/health` devuelve el estado del servidor:
```bash
curl http://localhost:8000/health
# {"ok": true}
```

---

**Última actualización:** 15 de diciembre de 2025
