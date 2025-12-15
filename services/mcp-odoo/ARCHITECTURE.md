# Arquitectura MCP-Odoo

## 🏗️ Visión General

MCP-Odoo implementa una arquitectura modular de 3 capas para exponer funcionalidades de Odoo ERP a través del protocolo MCP.

## 📐 Diagrama de Arquitectura

```
┌────────────────────────────────────────────────────────┐
│           CLIENTE MCP                                  │
│  (Claude Desktop, CLI, Custom Client)                  │
└──────────────────────┬─────────────────────────────────┘
                       │
                  MCP Protocol
                       │
┌──────────────────────▼─────────────────────────────────┐
│                  SERVER.PY (Main)                      │
│  - Inicialización ASGI                                 │
│  - Health check endpoint                               │
│  - Carga lazy de tools                                 │
└──────────────────────┬─────────────────────────────────┘
                       │
       ┌───────────────┴──────────────┐
       │                              │
┌──────▼──────────┐         ┌────────▼────────┐
│  CORE/CONFIG.PY │         │    TOOLS/       │
│                 │         │   (Autoload)    │
│ - Env vars      │         │                 │
│ - Validación    │         │ ┌─────────────┐ │
│ - Constantes    │         │ │   crm.py    │ │
└─────────────────┘         │ ├─────────────┤ │
                            │ │ projects.py │ │
                            │ ├─────────────┤ │
                            │ │  sales.py   │ │
                            │ ├─────────────┤ │
                            │ │  tasks.py   │ │
                            │ ├─────────────┤ │
                            │ │  users.py   │ │
                            │ ├─────────────┤ │
                            │ │ search.py   │ │
                            │ └──────┬──────┘ │
                            └────────┼────────┘
                                     │
                    ┌────────────────┴──────────────┐
                    │                               │
          ┌─────────▼─────────┐       ┌───────────▼──────────┐
          │     CORE/          │       │   CORE/helpers.py   │
          │                    │       │                     │
          │ ┌────────────────┐ │       │ - encode_content() │
          │ │ odoo_client.py │ │       │ - odoo_form_url()  │
          │ │                │ │       │ - wants_*()        │
          │ │ - search()     │ │       └────────────────────┘
          │ │ - search_read()│ │
          │ │ - read()       │ │
          │ │ - create()     │ │
          │ │ - write()      │ │
          │ │ - unlink()     │ │
          │ └───────┬────────┘ │
          └─────────┼──────────┘
                    │
                XML-RPC
                    │
          ┌─────────▼──────────┐
          │    Odoo ERP        │
          │  (External API)    │
          └────────────────────┘
```

## 🎯 Capas de la Arquitectura

### 1. **Capa de Aplicación** (`server.py`)

**Responsabilidad:** Inicialización y orquestación del servidor MCP

#### Funciones principales:
- `app()` - Aplicación ASGI principal
- `mcp_app()` - Wrapper para compatibilidad de hosts
- `init_tools_once()` - Carga idempotente de tools

**Características:**
- Health check endpoint (`/health`)
- Carga lazy de tools (solo en primer request)
- Manejo de errores global

**Patrón:** Application Controller Pattern

### 2. **Capa de Tools** (`tools/`)

**Responsabilidad:** Definir herramientas MCP que exponen funcionalidad Odoo

#### Estructura de un Tool Module

Cada archivo debe exponer:
```python
def register(mcp, deps):
    @mcp.tool(name="tool_name", description="...")
    def tool_function(arg: type) -> dict:
        odoo = deps["odoo"]
        # Implementación
        return result
```

#### Tools Disponibles

##### `search.py`
- `search()` - Búsqueda multi-modelo (proyectos/tareas)
- `fetch()` - Recuperación de documento completo

##### `crm.py`
- Tools de gestión de CRM
- Operaciones con leads, oportunidades, contactos

##### `projects.py`
- Tools de gestión de proyectos
- CRUD de proyectos

##### `sales.py`
- Tools de gestión de ventas
- Pedidos, productos, clientes

##### `tasks.py`
- Tools de gestión de tareas
- CRUD de tareas, asignaciones

##### `users.py`
- Tools de gestión de usuarios
- Consulta de usuarios y permisos

#### Autoload System

`tools/__init__.py` implementa carga automática:

```python
def load_all(mcp, deps):
    # Descubre todos los módulos en tools/
    # Llama a register() de cada uno
    # Maneja errores gracefully
```

**Ventaja:** Agregar un nuevo tool = crear archivo, automáticamente disponible

**Patrón:** Plugin Pattern, Dynamic Loading

### 3. **Capa de Core** (`core/`)

**Responsabilidad:** Abstracciones y utilidades fundamentales

#### `odoo_client.py`
Cliente XML-RPC para Odoo:

```python
class OdooClient:
    def __init__(self):
        # Conecta usando variables de entorno
        self.url = Config.ODOO_URL
        self.db = Config.ODOO_DB
        # ...
    
    def search(self, model, domain, limit):
        # Búsqueda de IDs
    
    def search_read(self, model, domain, fields, limit):
        # Búsqueda + lectura en una llamada
    
    def read(self, model, ids, fields):
        # Lectura de campos
    
    def create(self, model, values):
        # Creación de registros
    
    def write(self, model, ids, values):
        # Actualización
    
    def unlink(self, model, ids):
        # Eliminación
```

**Patrón:** Repository Pattern, Facade Pattern

#### `helpers.py`
Funciones de utilidad:

```python
def encode_content(obj) -> dict:
    # Formatea respuestas MCP
    return {"content": [{"type": "text", "text": json.dumps(obj)}]}

def odoo_form_url(model, rec_id) -> str:
    # Genera URL del formulario Odoo
    return f"{Config.ODOO_URL}/web#id={rec_id}&model={model}&view_type=form"

def wants_projects(query) -> bool:
    # Detecta si query busca proyectos
    return any(t in query.lower() for t in ("proyecto", "project", ...))

def wants_tasks(query) -> bool:
    # Detecta si query busca tareas
    return any(t in query.lower() for t in ("tarea", "task", ...))
```

**Patrón:** Utility Pattern

### 4. **Capa de Configuración** (`core/config.py`)

**Responsabilidad:** Gestión de configuración centralizada

```python
class Config:
    # Odoo Configuration
    ODOO_URL = os.getenv("ODOO_URL")
    ODOO_DB = os.getenv("ODOO_DB")
    ODOO_LOGIN = os.getenv("ODOO_LOGIN")
    ODOO_API_KEY = os.getenv("ODOO_API_KEY")
    
    # Server Configuration
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", "8000"))
    
    @classmethod
    def validate(cls) -> List[str]:
        # Retorna variables faltantes
    
    @classmethod
    def is_valid(cls) -> bool:
        # True si configuración OK
    
    @classmethod
    def print_config(cls):
        # Imprime configuración (sin exponer secrets)
```

**Patrón:** Singleton Pattern, Configuration Object

## 🔄 Flujo de Ejecución

### Inicialización

```python
1. Cargar Config
2. Crear FastMCP instance
3. Registrar ASGI app
4. Iniciar servidor uvicorn
5. Esperar primer request
```

### Primer Request

```python
1. Request llega a app()
2. Detectar que tools no están cargados
3. Llamar init_tools_once()
   3.1. Validar configuración
   3.2. Crear OdooClient
   3.3. Cargar todos los tools (autoload)
   3.4. Marcar como cargado
4. Procesar request normalmente
```

### Request de Tool

```python
1. Cliente envía request MCP
2. FastMCP parsea request
3. Identificar tool solicitado
4. Ejecutar función del tool
   4.1. Tool usa OdooClient
   4.2. OdooClient hace llamada XML-RPC a Odoo
   4.3. Tool procesa respuesta
   4.4. Tool formatea con encode_content()
5. FastMCP serializa respuesta
6. Enviar respuesta al cliente
```

### Health Check

```python
1. Request a /health
2. Retornar {"ok": true} inmediatamente
3. No cargar tools (optimización)
```

## 🔌 Integración con Odoo

### XML-RPC Protocol

Odoo expone una API XML-RPC en dos endpoints:

1. **Authentication:** `/xmlrpc/2/common`
   - `authenticate()` - Login y obtención de UID

2. **Object Methods:** `/xmlrpc/2/object`
   - `execute_kw()` - Ejecutar métodos del modelo

### Ejemplo de Llamada

```python
# Autenticación
uid = common.authenticate(db, username, api_key, {})

# Búsqueda
ids = models.execute_kw(
    db, uid, api_key,
    'project.project',  # modelo
    'search',           # método
    [[['active', '=', True]]],  # domain
    {'limit': 10}       # options
)
```

## 🎨 Patrones de Diseño

### 1. **Plugin Pattern (Tools)**
Cada tool es un plugin que se carga dinámicamente.

**Ventaja:** Extensibilidad sin modificar core

### 2. **Repository Pattern (OdooClient)**
`OdooClient` abstrae el acceso a datos de Odoo.

**Ventaja:** Cambiar implementación (XML-RPC → REST) sin afectar tools

### 3. **Facade Pattern (Helpers)**
Funciones helper simplifican operaciones comunes.

**Ventaja:** Código de tools más limpio

### 4. **Lazy Loading (Tools)**
Tools se cargan solo en primer request real.

**Ventaja:** Inicio rápido, health checks no cargan Odoo

### 5. **Dependency Injection (deps)**
Los tools reciben dependencias vía `deps` dict.

**Ventaja:** Testing fácil (mock de OdooClient)

## 📦 Dependencias entre Módulos

```
server.py
  ↓
  ├─→ core/config.py
  ├─→ core/odoo_client.py
  │     ↓
  │     └─→ core/config.py
  ├─→ core/helpers.py
  │     ↓
  │     └─→ core/config.py
  └─→ tools/__init__.py
        ↓
        ├─→ tools/crm.py
        │     ↓
        │     └─→ core/ (config, odoo_client, helpers)
        ├─→ tools/projects.py
        │     ↓
        │     └─→ core/
        ├─→ tools/sales.py
        │     ↓
        │     └─→ core/
        ├─→ tools/tasks.py
        │     ↓
        │     └─→ core/
        ├─→ tools/users.py
        │     ↓
        │     └─→ core/
        └─→ tools/search.py
              ↓
              └─→ core/
```

**Principio aplicado:** Dependencias fluyen hacia abajo (no hay ciclos)

## 🧪 Testing Strategy

### Unit Tests

```python
# test_odoo_client.py
def test_search():
    client = OdooClient()
    # Mock XML-RPC calls
    result = client.search('res.users', [], 1)
    assert isinstance(result, list)

# test_helpers.py
def test_encode_content():
    result = encode_content({"foo": "bar"})
    assert result["content"][0]["type"] == "text"

# test_search_tool.py
def test_search_tool():
    mcp = Mock()
    deps = {"odoo": Mock()}
    register_search_tools(mcp, deps)
    # Verify tools registered
```

### Integration Tests

```python
# test_integration.py
def test_full_flow():
    # Start server
    # Send MCP request
    # Verify Odoo called
    # Verify response format
```

### Manual Testing

```bash
# Test tool via CLI
mcp call odoo search --query "proyectos"

# Test via Python
python -c "from tools.search import *; ..."
```

## 🔒 Seguridad

### Variables de Entorno
- API keys en `.env`, nunca en código
- `.env` en `.gitignore`
- Validación de variables requeridas

### XML-RPC
- Usa HTTPS en producción
- API key en lugar de contraseña
- Rate limiting recomendado

### MCP Protocol
- Autenticación delegada a MCP client
- Validación de inputs en tools

## 🚀 Escalabilidad

### Horizontal Scaling
- Servidor stateless (no sesiones en memoria)
- Múltiples instancias detrás de load balancer
- Odoo escala independientemente

### Caching
- Considerar caché de búsquedas frecuentes
- Redis para caché distribuido
- TTL corto para datos cambiantes

### Performance
- Connection pooling para XML-RPC
- Batch operations donde sea posible
- Índices en Odoo para búsquedas

## 📈 Métricas Importantes

- **Latencia tool:** Tiempo de ejecución de cada tool
- **Latencia Odoo:** Tiempo de respuesta XML-RPC
- **Tasa de error:** Fallos en llamadas Odoo
- **Tools más usados:** Estadísticas de uso

## 🔧 Extensibilidad

### Agregar Nuevo Tool

1. Crear `tools/mi_tool.py`:
```python
from core import encode_content

def register(mcp, deps):
    @mcp.tool(name="mi_tool", description="...")
    def mi_tool(param: str) -> dict:
        odoo = deps["odoo"]
        # Implementación
        result = odoo.search_read(...)
        return encode_content({"result": result})
```

2. Reiniciar servidor → Tool disponible automáticamente

### Agregar Nuevo Modelo Odoo

1. Extender `OdooClient` si necesario
2. Crear tool que use el modelo
3. Documentar en README

### Cambiar Backend (XML-RPC → REST)

1. Crear `core/odoo_rest_client.py`
2. Implementar misma interfaz que `OdooClient`
3. Cambiar en `server.py`: `deps["odoo"] = OdooRestClient()`
4. Tools siguen funcionando sin cambios

---

**Principios de diseño:**
- ✅ Modularidad (tools independientes)
- ✅ Extensibilidad (plugin system)
- ✅ Testabilidad (dependency injection)
- ✅ Mantenibilidad (separación de concerns)
- ✅ Performance (lazy loading)

**Última actualización:** 15 de diciembre de 2025
