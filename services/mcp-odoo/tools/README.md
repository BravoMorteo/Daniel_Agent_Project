# Tools

Herramientas MCP modulares para interactuar con Odoo.

## 📁 Contenido

Cada archivo define un conjunto de tools relacionados:

### `crm.py`
Tools para gestión de CRM.
- Leads
- Oportunidades
- Contactos

### `projects.py`
Tools para gestión de proyectos.
- CRUD de proyectos
- Listado de proyectos
- Detalles de proyectos

### `sales.py`
Tools para gestión de ventas.
- Pedidos de venta
- Productos
- Clientes
- Cotizaciones

### `tasks.py`
Tools para gestión de tareas.
- CRUD de tareas
- Asignaciones
- Estados
- Deadlines

### `users.py`
Tools para gestión de usuarios.
- Consulta de usuarios
- Permisos
- Equipos

### `search.py`
Tools de búsqueda genérica.
- `search` - Busca proyectos/tareas por query
- `fetch` - Recupera documento completo por ID

### `whatsapp.py`
Tool para notificaciones WhatsApp.
- `whatsapp_handoff` - Envía notificación al vendedor cuando un cliente solicita atención humana

## 🔄 Sistema de Autoload

### `__init__.py`
Implementa carga automática de tools:

```python
def load_all(mcp, deps):
    # Descubre todos los módulos en tools/
    # Para cada módulo:
    #   1. Importa el módulo
    #   2. Busca función register() o register_<nombre>_tools()
    #   3. Llama a la función con (mcp, deps)
```

**Ventaja:** Agregar nuevo tool = crear archivo, automáticamente disponible

## 📝 Estructura de un Tool

Cada archivo debe seguir este patrón:

```python
"""
Descripción del módulo de tools
"""

from core import encode_content, odoo_form_url


def register(mcp, deps):
    """
    Registra los tools en MCP.
    
    Args:
        mcp: Instancia de FastMCP
        deps: Diccionario con dependencias {'odoo': OdooClient}
    """
    
    @mcp.tool(
        name="nombre_tool",
        description="Descripción clara de qué hace el tool"
    )
    def mi_tool(param1: str, param2: int = 10) -> dict:
        """
        Docstring del tool (aparece en documentación MCP).
        
        Args:
            param1: Descripción del parámetro
            param2: Otro parámetro con valor por defecto
            
        Returns:
            Dict en formato MCP content
        """
        # Obtener cliente Odoo
        odoo = deps["odoo"]
        
        # Lógica del tool
        results = odoo.search_read(...)
        
        # Formatear y retornar
        return encode_content({"results": results})
```

## 🎯 Ejemplo Completo

```python
# tools/mi_modulo.py

from typing import Dict, Any, List
from core import encode_content, odoo_form_url


def register(mcp, deps):
    """Registra tools de mi módulo"""
    
    @mcp.tool(
        name="buscar_usuarios",
        description="Busca usuarios de Odoo por nombre"
    )
    def buscar_usuarios(nombre: str, limite: int = 10) -> Dict[str, Any]:
        """
        Busca usuarios que coincidan con el nombre.
        
        Args:
            nombre: Nombre o parte del nombre a buscar
            limite: Máximo de resultados
            
        Returns:
            Lista de usuarios encontrados
        """
        odoo = deps["odoo"]
        
        # Buscar
        domain = [['name', 'ilike', nombre]]
        usuarios = odoo.search_read(
            'res.users',
            domain,
            ['id', 'name', 'login', 'email'],
            limite
        )
        
        # Formatear
        results = []
        for u in usuarios:
            results.append({
                'id': u['id'],
                'name': u['name'],
                'email': u.get('email', ''),
                'url': odoo_form_url('res.users', u['id'])
            })
        
        return encode_content({'usuarios': results})
```

## 🔧 Uso desde Cliente MCP

```json
{
  "tool": "buscar_usuarios",
  "arguments": {
    "nombre": "admin",
    "limite": 5
  }
}
```

**Respuesta:**
```json
{
  "content": [{
    "type": "text",
    "text": "{\"usuarios\": [{\"id\": 2, \"name\": \"Administrator\", ...}]}"
  }]
}
```

## 📚 Mejores Prácticas

1. **Nombrar tools descriptivamente:** `crear_proyecto` en lugar de `cp`
2. **Documentar parámetros:** Usar docstrings completos
3. **Validar inputs:** Verificar parámetros antes de usar
4. **Manejar errores:** Try/catch y retornar errores formatados
5. **Usar helpers:** `encode_content()`, `odoo_form_url()`
6. **Type hints:** Definir tipos de parámetros y retorno

## 🐛 Debug

Ver qué tools se registraron:
```bash
# Los logs mostrarán:
[INFO] Loading tools from tools/ directory...
[INFO] Registering tools from: tools.crm
[INFO] Registering tools from: tools.projects
[INFO] MCP tools registered successfully.
```

## 🔄 Hot Reload

Para recargar tools durante desarrollo:
1. Modificar archivo en `tools/`
2. Reiniciar servidor
3. Tools actualizados automáticamente
