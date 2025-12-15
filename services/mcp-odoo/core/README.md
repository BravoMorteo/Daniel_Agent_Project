# Core

Módulos fundamentales del servidor MCP-Odoo: configuración, cliente Odoo y utilidades.

## 📁 Contenido

### `config.py`
Gestión centralizada de configuración y variables de entorno.

**Clase:** `Config`

**Variables principales:**
- `ODOO_URL` - URL de la instancia Odoo
- `ODOO_DB` - Nombre de la base de datos
- `ODOO_LOGIN` - Email de usuario Odoo
- `ODOO_API_KEY` - API Key de Odoo
- `PORT` - Puerto del servidor (default: 8000)
- `MCP_NAME` - Nombre del servidor MCP

**Ejemplo:**
```python
from core import Config

# Acceder a configuración
print(Config.ODOO_URL)
print(Config.ODOO_DB)

# Verificar configuración
Config.print_config()
```

### `odoo_client.py`
Cliente XML-RPC para interactuar con Odoo ERP.

**Clase:** `OdooClient`

**Métodos principales:**
- `search(model, domain, limit)` - Buscar IDs de registros
- `search_read(model, domain, fields, limit)` - Buscar y leer en una operación
- `read(model, ids, fields)` - Leer campos de registros específicos
- `create(model, values)` - Crear nuevo registro
- `write(model, ids, values)` - Actualizar registros
- `unlink(model, ids)` - Eliminar registros

**Ejemplo:**
```python
from core import OdooClient

odoo = OdooClient()

# Buscar proyectos activos
project_ids = odoo.search('project.project', [['active', '=', True]], 10)

# Buscar y leer en una llamada
projects = odoo.search_read(
    'project.project',
    [['active', '=', True]],
    ['id', 'name', 'user_id'],
    10
)
```

### `helpers.py`
Funciones de utilidad compartidas.

**Funciones:**

#### `encode_content(obj) -> dict`
Formatea objetos en el formato de respuesta MCP.

```python
from core import encode_content

result = {"projects": [...]}
return encode_content(result)
# {"content": [{"type": "text", "text": "{...}"}]}
```

#### `odoo_form_url(model, rec_id, base_url=None) -> str`
Genera URL del formulario de Odoo para un registro.

```python
url = odoo_form_url("project.project", 123)
# "https://odoo.com/web#id=123&model=project.project&view_type=form"
```

#### `wants_projects(query) -> bool`
Detecta si la query busca proyectos.

```python
wants_projects("buscar proyectos activos")  # True
wants_projects("listar tareas")  # False
```

#### `wants_tasks(query) -> bool`
Detecta si la query busca tareas.

```python
wants_tasks("tareas pendientes")  # True
wants_tasks("proyectos")  # False
```

## 🔄 Arquitectura

```
Tools (projects.py, tasks.py, etc.)
        ↓
    OdooClient
        ↓
    XML-RPC
        ↓
    Odoo ERP

    Helpers
     ↑
Tools utilizan helpers para formatear respuestas
```

## 📝 Uso

```python
from core import OdooClient, encode_content, odoo_form_url

# Crear cliente
odoo = OdooClient()

# Buscar
projects = odoo.search_read('project.project', [], ['id', 'name'], 5)

# Formatear respuesta
response = encode_content({"projects": projects})

# Generar URL
url = odoo_form_url('project.project', projects[0]['id'])
```

## 🔧 Configuración

`OdooClient` usa `config.py` para obtener:
- `ODOO_URL` - URL del servidor Odoo
- `ODOO_DB` - Nombre de la base de datos
- `ODOO_LOGIN` - Usuario/email
- `ODOO_API_KEY` - API key para autenticación
