# 🔧 MCP-Odoo: Servidor Híbrido de Integración con Odoo ERP

**Versión:** 2.0.0  
**Actualizado:** Enero 2026  
**Estado:** ✅ Producción

---

## 📖 Tabla de Contenidos

1. [¿Qué es MCP-Odoo?](#qué-es-mcp-odoo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Tecnologías y Herramientas](#tecnologías-y-herramientas)
4. [Estructura de Archivos](#estructura-de-archivos)
5. [Flujo de Peticiones](#flujo-de-peticiones)
6. [Relación MCP + FastAPI](#relación-mcp--fastapi)
7. [Instalación y Configuración](#instalación-y-configuración)
8. [Herramientas MCP Disponibles](#herramientas-mcp-disponibles)
9. [API REST Endpoints](#api-rest-endpoints)
10. [Problemas Comunes y Soluciones](#problemas-comunes-y-soluciones)
11. [Desarrollo y Testing](#desarrollo-y-testing)

---

## 🎯 ¿Qué es MCP-Odoo?

MCP-Odoo es un **servidor híbrido** que combina dos protocolos en un solo servicio:

### 1️⃣ **Model Context Protocol (MCP)**
Permite que **LLMs** (Large Language Models) como Claude, GPT, etc. puedan:
- Ejecutar acciones en Odoo (crear leads, cotizaciones, buscar datos)
- Obtener información del ERP en tiempo real
- Realizar operaciones complejas mediante "herramientas"

### 2️⃣ **FastAPI REST**
Proporciona **endpoints HTTP tradicionales** para:
- Crear cotizaciones asíncronas desde aplicaciones externas
- Consultar el estado de tareas en progreso
- Recibir webhooks de servicios externos (ElevenLabs, Twilio)
- Enviar notificaciones por WhatsApp

### 🎭 ¿Por qué híbrido?

```
┌────────────────────────────────────────────────────────────┐
│                    UN SOLO SERVIDOR                        │
│                   Puerto 8000 Unificado                    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  /mcp/*      →  Para LLMs (Claude, GPT)                   │
│                 Protocolo especial MCP                     │
│                                                            │
│  /api/*      →  Para Apps Web/Mobile                      │
│                 REST tradicional HTTP/JSON                 │
│                                                            │
│  /health     →  Para Balanceadores de Carga               │
│  /docs       →  Swagger UI automático                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Ventaja**: Un solo proceso, un solo puerto, dos interfaces complementarias.

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Componentes

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENTES                                 │
├────────────────┬─────────────────────────────────────────────────┤
│  LLM (Claude)  │  Aplicaciones Web  │  ElevenLabs  │  Frontend  │
│  con MCP SDK   │  (Fetch/Axios)     │  (Webhook)   │  (AJAX)    │
└────────┬───────┴──────────┬──────────┴──────┬───────┴────┬───────┘
         │                  │                 │            │
         │ MCP Protocol     │ HTTP REST       │ HTTP POST  │ HTTP
         │ (SSE Stream)     │ (JSON)          │ (JSON)     │
         │                  │                 │            │
         └──────────────────┴─────────────────┴────────────┘
                            │
                            ▼
         ┌──────────────────────────────────────────────┐
         │      FastAPI App (Puerto 8000)               │
         │  ┌────────────────────────────────────────┐  │
         │  │  ASGI Application Layer                │  │
         │  │  • Router principal                    │  │
         │  │  • Middleware de validación            │  │
         │  │  • Background tasks                    │  │
         │  └────────────────┬───────────────────────┘  │
         │                   │                          │
         │  ┌────────────────┴────────────┐             │
         │  │                             │             │
         │  ▼                             ▼             │
         │  ┌──────────┐         ┌──────────────┐      │
         │  │   MCP    │         │   REST API   │      │
         │  │ Protocol │         │   Endpoints  │      │
         │  │          │         │              │      │
         │  │ /mcp/*   │         │ /api/*       │      │
         │  │ /mcp/sse │         │ /health      │      │
         │  └────┬─────┘         └──────┬───────┘      │
         │       │                      │              │
         └───────┼──────────────────────┼──────────────┘
                 │                      │
                 └──────────┬───────────┘
                            │
         ┌──────────────────▼───────────────────────┐
         │         CORE MODULES                     │
         │  ┌────────────┬──────────┬─────────────┐ │
         │  │ OdooClient │ TaskMgr  │ Logger      │ │
         │  │ (XML-RPC)  │(In-Mem)  │(Local+S3)   │ │
         │  └─────┬──────┴────┬─────┴──────┬──────┘ │
         │        │            │            │        │
         └────────┼────────────┼────────────┼────────┘
                  │            │            │
         ┌────────▼────────────▼────────────▼────────┐
         │            TOOLS (Herramientas)           │
         │  ┌──────┬───────┬───────┬──────┬───────┐ │
         │  │ CRM  │ Sales │Search │Users │WhatsApp│
         │  └──────┴───────┴───────┴──────┴───────┘ │
         └────────────────┬──────────────────────────┘
                          │
         ┌────────────────▼──────────────────────────┐
         │              SERVICIOS EXTERNOS           │
         │  ┌──────────┬───────────┬──────────────┐ │
         │  │  Odoo    │  AWS S3   │   Twilio     │ │
         │  │  ERP     │  (Logs)   │  (SMS/WA)    │ │
         │  └──────────┴───────────┴──────────────┘ │
         └───────────────────────────────────────────┘
```

### Capas del Sistema

#### 1. **Capa de Presentación** (Clientes)
- **LLMs**: Claude Desktop, IDEs con MCP
- **Aplicaciones Web**: Frontend JavaScript, React, Vue, etc.
- **Webhooks**: ElevenLabs, Twilio, servicios externos

#### 2. **Capa de Aplicación** (FastAPI + MCP)
- **FastAPI**: Framework web asíncrono Python
- **MCP Server**: Implementación del protocolo MCP
- **ASGI App**: Servidor de aplicación unificado

#### 3. **Capa de Lógica de Negocio** (Core)
- **OdooClient**: Cliente XML-RPC para comunicación con Odoo
- **TaskManager**: Gestión de tareas asíncronas en memoria
- **QuotationLogger**: Sistema de logs JSON local + S3
- **WhatsAppClient**: Cliente de Twilio para SMS/WhatsApp

#### 4. **Capa de Herramientas** (Tools)
- Módulos MCP que encapsulan operaciones específicas
- Cada tool expone funciones que los LLMs pueden llamar
- Reutilizables entre MCP y REST

#### 5. **Capa de Datos** (Servicios Externos)
- **Odoo ERP**: Base de datos y lógica de negocio
- **AWS S3**: Almacenamiento de logs para auditoría
- **Twilio**: Envío de mensajes SMS/WhatsApp

---

## 🛠️ Tecnologías y Herramientas

### Por qué usamos cada tecnología

| Tecnología | Versión | ¿Para qué sirve? | ¿Por qué la elegimos? |
|------------|---------|------------------|----------------------|
| **Python** | 3.11+ | Lenguaje de programación | - Excelente para integraciones<br>- Amplio ecosistema de librerías<br>- Tipado con type hints<br>- Async/await nativo |
| **FastAPI** | 0.115+ | Framework web asíncrono | - Alto rendimiento (basado en Starlette)<br>- Validación automática con Pydantic<br>- Documentación auto-generada (Swagger)<br>- Soporte nativo para async/await<br>- Inyección de dependencias |
| **FastMCP** | 2.14+ | Implementación del protocolo MCP | - Protocolo estándar para LLMs<br>- Fácil registro de herramientas<br>- Soporte para SSE (Server-Sent Events)<br>- Compatible con Claude Desktop |
| **Pydantic** | 2.7+ | Validación de datos | - Validación automática de tipos<br>- Serialización/deserialización JSON<br>- Mensajes de error claros<br>- Integración perfecta con FastAPI |
| **Uvicorn** | 0.30+ | Servidor ASGI | - Servidor web rápido y ligero<br>- Soporte para WebSockets<br>- Compatible con ASGI 3.0<br>- Hot-reload para desarrollo |
| **python-dotenv** | 1.0+ | Gestión de variables de entorno | - Configuración centralizada<br>- Fácil cambio entre entornos<br>- Seguridad (no commitar .env) |
| **Boto3** | 1.34+ | SDK de AWS | - Subida de logs a S3<br>- Almacenamiento persistente<br>- Auditoría y análisis histórico |
| **Twilio** | 9.0+ | Comunicación SMS/WhatsApp | - API confiable para mensajería<br>- Handoff a vendedores humanos<br>- Notificaciones en tiempo real |
| **Requests** | 2.32+ | Cliente HTTP | - Llamadas a APIs externas<br>- Simple y confiable<br>- Sesiones persistentes |

### Dependencias del Proyecto

```toml
[project]
name = "mcp-odoo"
version = "0.2.0"
requires-python = ">=3.10"
dependencies = [
  "mcp[cli]>=1.2.0",           # Core MCP protocol
  "fastmcp>=2.14.4",           # FastMCP implementation
  "uvicorn>=0.30.0",           # ASGI server
  "starlette>=0.37.0",         # Web framework base
  "fastapi>=0.115.0",          # Web framework
  "pydantic>=2.7.0",           # Data validation
  "python-dotenv>=1.0.0",      # Environment variables
  "requests>=2.32.5",          # HTTP client
  "boto3>=1.34.0",             # AWS S3 client
  "twilio>=9.0.0",             # SMS/WhatsApp client
]
```

---

## 📂 Estructura de Archivos

### Vista General

```
services/mcp-odoo/
├── server.py                 # 🚀 PUNTO DE ENTRADA
│                             # Crea FastAPI app, monta MCP, registra endpoints
│
├── core/                     # 🧠 LÓGICA CENTRAL
│   ├── __init__.py          # Exporta Config, OdooClient, helpers
│   ├── config.py            # Configuración y variables de entorno
│   ├── odoo_client.py       # Cliente XML-RPC para Odoo
│   ├── api.py               # Modelos Pydantic y lógica de API REST
│   ├── tasks.py             # TaskManager para procesos asíncronos
│   ├── logger.py            # QuotationLogger (local + S3)
│   ├── whatsapp.py          # Cliente de Twilio para WhatsApp
│   ├── helpers.py           # Funciones auxiliares reutilizables
│   └── README.md            # Documentación del core
│
├── tools/                    # 🔧 HERRAMIENTAS MCP
│   ├── __init__.py          # Auto-carga de herramientas
│   ├── crm.py               # Gestión de CRM (leads, oportunidades)
│   ├── sales.py             # Gestión de ventas (órdenes, productos)
│   ├── projects.py          # Búsqueda de proyectos
│   ├── tasks.py             # Búsqueda de tareas
│   ├── users.py             # Búsqueda de usuarios/vendedores
│   ├── search.py            # Búsqueda general en Odoo
│   ├── whatsapp.py          # Notificaciones de handoff
│   └── README.md            # Documentación de herramientas
│
├── docs/                     # 📚 DOCUMENTACIÓN
│   ├── S3_LOGS_SETUP.md     # Configuración de logs en S3
│   └── WHATSAPP_HANDOFF.md  # Sistema de handoff a vendedores
│
├── scripts/                  # 🐳 DEPLOYMENT
│   ├── Dockerfile           # Contenedor Docker
│   ├── Makefile             # Comandos útiles de desarrollo
│   ├── build.sh             # Script de build
│   └── README.md            # Documentación de deployment
│
├── pyproject.toml           # 📦 Configuración de dependencias
├── .env.example             # 🔐 Template de variables de entorno
├── .env                     # 🔒 Variables de entorno (NO COMMITEAR)
└── README.md                # 📖 Este archivo
```

### Detalle de Archivos Principales

#### 🚀 `server.py` - Punto de Entrada

**Responsabilidad**: Orquestador principal del servidor

```python
# Flujo de inicialización:
1. Importa FastAPI, FastMCP, y módulos core
2. Crea instancia de FastMCP
3. Inicializa herramientas una sola vez (init_tools_once)
4. Crea wrapper ASGI para compatibilidad con proxies
5. Crea app FastAPI
6. Monta MCP en /mcp
7. Registra endpoints REST en /api
8. Ejecuta servidor con uvicorn
```

**Funciones clave**:
- `init_tools_once()`: Carga cliente Odoo y registra todas las herramientas
- `mcp_app_wrapper()`: Wrapper ASGI que permite conexiones desde cualquier host
- `create_quotation_async()`: Endpoint REST para cotizaciones asíncronas
- `get_quotation_status()`: Endpoint REST para consultar estado
- `elevenlabs_handoff()`: Endpoint REST para handoff a vendedores

#### 🧠 Core Modules

##### `core/config.py` - Configuración

```python
class Config:
    # Variables de Odoo
    ODOO_URL = os.getenv("ODOO_URL")
    ODOO_DB = os.getenv("ODOO_DB")
    ODOO_LOGIN = os.getenv("ODOO_LOGIN")
    ODOO_API_KEY = os.getenv("ODOO_API_KEY")
    
    # Variables de servidor
    HOST = "0.0.0.0"
    PORT = 8000
    
    # Métodos
    validate()        # Valida variables requeridas
    print_config()    # Imprime configuración
```

**¿Por qué existe?**
- Centralizar toda la configuración
- Validar variables al inicio
- Facilitar cambios entre entornos
- No hardcodear valores sensibles

##### `core/odoo_client.py` - Cliente Odoo

```python
class OdooClient:
    def __init__()           # Inicializa conexión XML-RPC
    def authenticate()       # Autentica con Odoo
    def search(model, ...)   # Busca registros
    def read(model, ids, ...) # Lee datos de registros
    def create(model, vals)  # Crea nuevo registro
    def write(model, id, vals) # Actualiza registro
```

**¿Por qué XML-RPC?**
- API estándar de Odoo
- No requiere módulos personalizados en Odoo
- Compatible con todas las versiones
- Simple y confiable

##### `core/api.py` - Modelos y Lógica REST

```python
# Modelos Pydantic
class QuotationRequest(BaseModel)
class QuotationResponse(BaseModel)
class HandoffRequest(BaseModel)

# Funciones de procesamiento
process_quotation_background()  # Procesa cotización en background
```

**¿Por qué Pydantic?**
- Validación automática de tipos
- Documentación auto-generada
- Serialización JSON automática
- Mensajes de error claros

##### `core/tasks.py` - Gestor de Tareas Asíncronas

```python
class QuotationTask:
    tracking_id: str
    status: TaskStatus      # queued, processing, completed, failed
    input: dict             # Datos del request
    output: dict            # Resultado
    error: str              # Error si falló
    
class TaskManager:
    create_task()           # Crea nueva tarea
    get_task()              # Obtiene tarea por ID
    update_task()           # Actualiza estado
    cleanup_old_tasks()     # Limpia tareas antiguas
```

**¿Por qué en memoria?**
- Simplicidad (no requiere Redis/DB)
- Rápido acceso
- Suficiente para el caso de uso
- Las tareas se completan en segundos

##### `core/logger.py` - Sistema de Logs

```python
class QuotationLogger:
    log_quotation()         # Registra cotización (local + S3)
    log_sms_handoff()       # Registra handoff (local + S3)
    upload_to_s3()          # Sube archivo a S3
```

**¿Por qué logs en S3?**
- Auditoría persistente
- Análisis histórico
- Backup automático
- Búsqueda y reporting

##### `core/whatsapp.py` - Cliente WhatsApp

```python
class WhatsAppClient:
    is_configured()             # Verifica configuración
    send_handoff_notification() # Envía notificación
```

**¿Por qué Twilio?**
- API confiable y escalable
- Soporte para WhatsApp Business
- Webhooks para eventos
- SDKs bien documentados

#### 🔧 Tools (Herramientas MCP)

Cada archivo en `tools/` expone herramientas que los LLMs pueden usar:

```python
# Estructura estándar de un tool
def register(mcp: FastMCP, deps: dict):
    @mcp.tool()
    def nombre_herramienta(parametro: tipo) -> tipo:
        """Descripción que ve el LLM"""
        # Lógica de la herramienta
        return resultado
```

**Herramientas disponibles**:

| Archivo | Herramientas | ¿Qué hacen? |
|---------|--------------|-------------|
| `crm.py` | `dev_create_quotation`<br>`get_salesperson_with_least_opportunities` | Crear cotizaciones completas<br>Balanceo de carga de vendedores |
| `sales.py` | `dev_create_sale`<br>`dev_create_sale_line`<br>`dev_read_sale`<br>`dev_update_sale` | Crear órdenes de venta<br>Agregar productos<br>Leer/actualizar órdenes |
| `projects.py` | `list_projects` | Listar proyectos con filtros |
| `tasks.py` | `list_tasks`<br>`get_task` | Listar/buscar tareas<br>Obtener detalle de tarea |
| `users.py` | `list_users` | Listar usuarios/vendedores |
| `search.py` | `search`<br>`fetch` | Búsqueda general<br>Recuperar documento |
| `whatsapp.py` | `message_notification` | Enviar notificación a vendedor |

---

## 🔄 Flujo de Peticiones

### Flujo 1: LLM llama Herramienta MCP

**Escenario**: Claude Desktop quiere crear una cotización

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USUARIO: "Crea una cotización para Robot PUDU, cliente Acme"│
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 2. CLAUDE: Analiza el request                                   │
│    - Identifica: necesita crear cotización                      │
│    - Extrae: partner, producto, cantidades                      │
│    - Decide: usar dev_create_quotation                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 3. MCP CLIENT: Llama herramienta via MCP Protocol               │
│    POST /mcp/messages                                            │
│    Content-Type: application/json                                │
│    {                                                             │
│      "jsonrpc": "2.0",                                           │
│      "method": "tools/call",                                     │
│      "params": {                                                 │
│        "name": "dev_create_quotation",                           │
│        "arguments": {                                            │
│          "partner_name": "Acme Corp",                            │
│          "contact_name": "John Doe",                             │
│          ...                                                     │
│        }                                                         │
│      }                                                           │
│    }                                                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 4. FASTAPI: Recibe request en /mcp/messages                     │
│    - Valida JSON-RPC                                             │
│    - Enruta a MCP handler                                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 5. MCP SERVER: Busca herramienta registrada                     │
│    - Encuentra dev_create_quotation en tools/crm.py             │
│    - Valida parámetros con Pydantic                              │
│    - Ejecuta la función                                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 6. TOOL (dev_create_quotation):                                 │
│    a) Busca/crea partner en Odoo                                │
│    b) Crea lead                                                  │
│    c) Crea oportunidad                                           │
│    d) Crea orden de venta                                        │
│    e) Agrega líneas de productos                                 │
│    f) Registra en logs (local + S3)                              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 7. ODOO CLIENT: Múltiples llamadas XML-RPC                      │
│    - search_count('res.partner', [('name', '=', 'Acme')])       │
│    - create('res.partner', {...})                                │
│    - create('crm.lead', {...})                                   │
│    - create('sale.order', {...})                                 │
│    - create('sale.order.line', {...})                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 8. ODOO ERP: Procesa operaciones                                │
│    - Valida datos                                                │
│    - Aplica lógica de negocio                                    │
│    - Guarda en base de datos PostgreSQL                          │
│    - Retorna IDs creados                                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 9. TOOL: Recibe resultados                                      │
│    {                                                             │
│      "partner_id": 12345,                                        │
│      "lead_id": 67890,                                           │
│      "sale_order_id": 11111,                                     │
│      "sale_order_name": "S12345"                                 │
│    }                                                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 10. LOGGER: Registra cotización                                 │
│     - Crea archivo JSON local                                    │
│     - Sube a S3: s3://bucket/2026/01/quot_abc123.log            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 11. MCP SERVER: Retorna respuesta JSON-RPC                      │
│     {                                                            │
│       "jsonrpc": "2.0",                                          │
│       "result": {                                                │
│         "tracking_id": "quot_abc123",                            │
│         "status": "completed",                                   │
│         "output": {...}                                          │
│       }                                                          │
│     }                                                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 12. CLAUDE: Procesa respuesta                                   │
│     - Extrae información relevante                               │
│     - Genera respuesta para el usuario                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 13. USUARIO: "✅ Cotización S12345 creada para Acme Corp"       │
└─────────────────────────────────────────────────────────────────┘
```

**Tiempo total**: ~20-30 segundos

---

### Flujo 2: Aplicación Web llama API REST

**Escenario**: Frontend crea cotización asíncrona

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. FRONTEND: Usuario llena formulario y hace click en "Crear"   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 2. JAVASCRIPT: Envía request HTTP                                │
│    fetch('/api/quotation/async', {                               │
│      method: 'POST',                                             │
│      headers: {'Content-Type': 'application/json'},              │
│      body: JSON.stringify({                                      │
│        partner_name: "Acme Corp",                                │
│        contact_name: "John Doe",                                 │
│        ...                                                       │
│      })                                                          │
│    })                                                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 3. FASTAPI: Recibe request en /api/quotation/async              │
│    - Valida JSON con Pydantic (QuotationRequest)                │
│    - Si inválido: retorna 422 con errores                        │
│    - Si válido: continúa                                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 4. ENDPOINT create_quotation_async():                           │
│    a) Genera tracking_id único: quot_abc123                     │
│    b) Crea tarea en TaskManager (estado: queued)                │
│    c) Programa background task con FastAPI                       │
│    d) Retorna respuesta INMEDIATA (no espera)                    │
│    {                                                             │
│      "tracking_id": "quot_abc123",                               │
│      "status": "queued",                                         │
│      "estimated_time": "20-30 segundos",                         │
│      "status_url": "/api/quotation/status/quot_abc123"           │
│    }                                                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 5. FRONTEND: Recibe tracking_id                                 │
│    - Muestra mensaje: "Procesando... quot_abc123"               │
│    - Inicia polling cada 2 segundos:                             │
│      GET /api/quotation/status/quot_abc123                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                  ┌─────────────┴─────────────┐
                  │                           │
                  ▼ (Hilo Principal)          ▼ (Background Task)
                                              
┌─────────────────────────────┐   ┌───────────────────────────────┐
│ 6a. POLLING del Frontend    │   │ 6b. BACKGROUND TASK ejecuta   │
│     GET /status/quot_abc123 │   │     process_quotation_bg()    │
│                             │   │                               │
│     Respuesta inicial:      │   │  - Actualiza task: processing │
│     { status: "queued" }    │   │  - Ejecuta lógica completa:   │
│                             │   │    • Crea partner             │
│     Respuesta después:      │   │    • Crea lead                │
│     { status: "processing" }│   │    • Crea sale order          │
│                             │   │    • Agrega productos         │
│     Respuesta final:        │   │  - Registra en logs           │
│     {                       │   │  - Actualiza task: completed  │
│       status: "completed",  │   │  - Guarda output en task      │
│       output: {...}         │   │                               │
│     }                       │   │                               │
└─────────────────────────────┘   └───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│ 7. FRONTEND: Detecta status = "completed"                       │
│    - Detiene polling                                             │
│    - Muestra resultado:                                          │
│      "✅ Cotización S12345 creada exitosamente"                  │
│    - Muestra link: "Ver en Odoo"                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Ventajas del enfoque asíncrono**:
- ✅ Frontend no se bloquea esperando
- ✅ Usuario puede seguir navegando
- ✅ Reintentos automáticos si falla
- ✅ Logs completos del proceso

---

### Flujo 3: Webhook de ElevenLabs (Handoff)

**Escenario**: Cliente pide hablar con humano en ElevenLabs

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USUARIO: "Quiero hablar con un vendedor humano"              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 2. ELEVENLABS ConvAI: Detecta intención de handoff              │
│    - Analiza conversación                                        │
│    - Identifica request de atención humana                       │
│    - Trigger: webhook configurado                                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 3. ELEVENLABS: Envía webhook HTTP POST                          │
│    POST https://tu-servidor.com/api/elevenlabs/handoff          │
│    {                                                             │
│      "user_phone": "+5215512345678",                             │
│      "reason": "Cliente solicita información personalizada",     │
│      "user_name": "Juan Pérez",                                  │
│      "conversation_id": "conv_abc123",                           │
│      "additional_context": "Preguntó por robots"                 │
│    }                                                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 4. FASTAPI: Recibe en /api/elevenlabs/handoff                   │
│    - Valida con Pydantic (HandoffRequest)                        │
│    - Ejecuta elevenlabs_handoff()                                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 5. ENDPOINT elevenlabs_handoff():                               │
│    LÓGICA DE ASIGNACIÓN:                                         │
│    - ¿Hay lead_id en request?                                    │
│      → SÍ: usar vendedor del lead                                │
│    - ¿Hay sale_order_id?                                         │
│      → SÍ: usar vendedor de la orden                             │
│    - ¿No hay ninguno?                                            │
│      → Balanceo: vendedor con menos leads activos                │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 6. ODOO CLIENT: Consulta vendedor                               │
│    search_count('crm.lead', [                                    │
│      ('user_id', '=', vendedor_id),                              │
│      ('type', '=', 'opportunity'),                               │
│      ('active', '=', True)                                       │
│    ])                                                            │
│    # Retorna: vendedor con menos oportunidades activas          │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 7. HELPER get_user_whatsapp_number():                           │
│    - Lee campo mobile del usuario en Odoo                        │
│    - Valida formato                                              │
│    - Retorna: +5215587654321                                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 8. WHATSAPP CLIENT: Envía notificación via Twilio               │
│    client.messages.create(                                       │
│      from_='whatsapp:+14155238886',                              │
│      to='whatsapp:+5215587654321',                               │
│      body='''                                                    │
│        🔔 *Nuevo cliente solicita atención*                      │
│        👤 Juan Pérez                                             │
│        📱 +5215512345678                                         │
│        📝 Cliente solicita información personalizada             │
│        💬 Preguntó por robots                                    │
│      '''                                                         │
│    )                                                             │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 9. TWILIO: Entrega mensaje WhatsApp                             │
│    - Retorna message_sid: SM1234567890                           │
│    - Status: sent/delivered/read                                 │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 10. LOGGER: Registra handoff                                    │
│     - Crea log local: sms_1738264800_abc123.log                 │
│     - Sube a S3 para auditoría                                   │
│     {                                                            │
│       "handoff_id": "sms_...",                                   │
│       "user_phone": "+5215512345678",                            │
│       "assigned_user_id": 42,                                    │
│       "vendor_sms": "+5215587654321",                            │
│       "message_sid": "SM1234567890",                             │
│       "status": "success"                                        │
│     }                                                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 11. ENDPOINT: Retorna respuesta a ElevenLabs                    │
│     {                                                            │
│       "status": "ok",                                            │
│       "message": "Notificación enviada",                         │
│       "assigned_user_id": 42                                     │
│     }                                                            │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│ 12. VENDEDOR: Recibe WhatsApp                                   │
│     - Ve datos del cliente                                       │
│     - Puede contactar directamente                               │
│     - Atención personalizada                                     │
└─────────────────────────────────────────────────────────────────┘
```

**Tiempo total**: ~2-5 segundos

---

## 🔗 Relación MCP + FastAPI

### ¿Cómo conviven MCP y FastAPI en un solo servidor?

```python
# server.py - Versión simplificada

# 1. Crear servidor MCP
mcp = FastMCP("OdooMCP")

# 2. Registrar herramientas MCP
@mcp.tool()
def dev_create_quotation(...):
    # Lógica de la herramienta
    pass

# 3. Crear app FastAPI
app = FastAPI()

# 4. CLAVE: Montar MCP dentro de FastAPI
app.mount("/mcp", mcp.sse_app())

# 5. Agregar endpoints REST adicionales
@app.post("/api/quotation/async")
def create_quotation_async(...):
    # Endpoint REST que REUTILIZA las herramientas MCP
    pass

# 6. Un solo servidor, dos interfaces
uvicorn.run(app, port=8000)
```

### Tabla Comparativa

| Aspecto | MCP Protocol | FastAPI REST |
|---------|-------------|--------------|
| **Puerto** | 8000 | 8000 (mismo) |
| **Ruta base** | `/mcp/*` | `/api/*`, `/health`, `/docs` |
| **Clientes** | LLMs (Claude Desktop) | Apps web, mobile, webhooks |
| **Protocolo** | JSON-RPC + SSE | HTTP REST + JSON |
| **Autenticación** | No implementada | No implementada (opcional) |
| **Documentación** | Descripción en tools | Swagger UI auto-generado |
| **Uso típico** | Conversaciones con IA | Aplicaciones tradicionales |
| **Endpoint ejemplo** | `/mcp/sse` | `/api/quotation/async` |

### Compartir Código entre MCP y REST

Ambas interfaces **reutilizan** el mismo código:

```python
# tools/crm.py - Herramienta MCP
@mcp.tool()
def dev_create_quotation(partner_name: str, ...):
    """Herramienta que ve el LLM"""
    client = deps["odoo"]  # OdooClient compartido
    
    # Lógica compartida
    partner_id = _create_or_find_partner(client, partner_name)
    lead_id = _create_lead(client, partner_id, ...)
    sale_id = _create_sale_order(client, lead_id, ...)
    
    return {"sale_order_id": sale_id, ...}

# core/api.py - Endpoint REST
def process_quotation_background(tracking_id, data):
    """Background task que usa la MISMA lógica"""
    from tools.crm import DevOdooCRMClient
    
    client = DevOdooCRMClient()
    
    # REUTILIZA las mismas funciones privadas
    partner_id = _create_or_find_partner(client, data["partner_name"])
    lead_id = _create_lead(client, partner_id, ...)
    sale_id = _create_sale_order(client, lead_id, ...)
    
    # Actualiza task manager
    task_manager.update_task(tracking_id, {...})
```

**Ventajas**:
- ✅ No duplicar código
- ✅ Un solo lugar para bugs
- ✅ Consistencia garantizada
- ✅ Mantenimiento simplificado

### Flujo de Routing

```
Request entrante
     │
     ├─ Path empieza con /mcp → MCP Handler
     │                           │
     │                           ├─ /mcp/sse → SSE Stream
     │                           └─ /mcp/messages → JSON-RPC
     │
     ├─ Path empieza con /api → REST Handlers
     │                           │
     │                           ├─ /api/quotation/async
     │                           └─ /api/elevenlabs/handoff
     │
     ├─ /health → Health Check
     │
     └─ /docs → Swagger UI
```

---

## ⚙️ Instalación y Configuración

### Requisitos Previos

- **Python 3.10+** (recomendado 3.11)
- **Pip** o **uv** para gestión de paquetes
- **Acceso a Odoo ERP** (URL, credenciales, API key)
- **(Opcional) AWS S3** para logs persistentes
- **(Opcional) Twilio** para WhatsApp

### Paso 1: Clonar e Instalar

```bash
cd services/mcp-odoo

# Opción A: Con pip
pip install -e .

# Opción B: Con uv (más rápido)
uv pip install -e .
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar .env
nano .env
```

**Archivo `.env`**:

```bash
# ════════════════════════════════════════════════════════════
# ODOO CONFIGURATION (REQUERIDO)
# ════════════════════════════════════════════════════════════
ODOO_URL=https://tu-instancia.odoo.com
ODOO_DB=nombre_base_datos
ODOO_LOGIN=tu_email@empresa.com
ODOO_API_KEY=tu_api_key_de_odoo

# ════════════════════════════════════════════════════════════
# SERVER CONFIGURATION
# ════════════════════════════════════════════════════════════
PORT=8000
HOST=0.0.0.0

# ════════════════════════════════════════════════════════════
# AWS S3 LOGS (OPCIONAL)
# ════════════════════════════════════════════════════════════
S3_LOGS_BUCKET=tu-bucket-logs
AWS_REGION=us-west-2
AWS_ACCESS_KEY_ID=AKIAXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxx

# O usar IAM Role (recomendado en producción)
# AWS_ROLE_ARN=arn:aws:iam::123456:role/mcp-odoo-role

# ════════════════════════════════════════════════════════════
# TWILIO WHATSAPP (OPCIONAL)
# ════════════════════════════════════════════════════════════
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
VENDEDOR_WHATSAPP=whatsapp:+5215512345678
```

### Paso 3: Verificar Configuración

```bash
python -c "from core import Config; Config.validate(); Config.print_config()"
```

**Salida esperada**:
```
══════════════════════════════════════════════════════════════════
🔧 SERVIDOR MCP-ODOO
══════════════════════════════════════════════════════════════════
🌐 Odoo URL: https://tu-instancia.odoo.com
🗄️  Database: nombre_base_datos
👤 Login: tu_email@empresa.com
🔑 API Key: ✓ Configurada
🚀 Servidor en: http://0.0.0.0:8000
══════════════════════════════════════════════════════════════════
✅ Configuración válida
══════════════════════════════════════════════════════════════════
```

### Paso 4: Ejecutar Servidor

```bash
# Desarrollo (con auto-reload)
python server.py

# O con uvicorn directamente
uvicorn server:app --reload --port 8000
```

**Salida esperada**:
```
══════════════════════════════════════════════════════════════
MCP-ODOO Server Híbrido - MCP + REST API
══════════════════════════════════════════════════════════════
[Configuración...]

📡 Endpoints disponibles:
   • MCP Protocol:     http://0.0.0.0:8000/mcp
     ├─ SSE Stream:    http://0.0.0.0:8000/mcp/sse
     └─ Messages:      http://0.0.0.0:8000/mcp/messages
   • Async Quotation:  http://0.0.0.0:8000/api/quotation/async
   • Check Status:     http://0.0.0.0:8000/api/quotation/status/{id}
   • WhatsApp Handoff: http://0.0.0.0:8000/api/elevenlabs/handoff
   • Health Check:     http://0.0.0.0:8000/health
   • API Docs:         http://0.0.0.0:8000/docs
══════════════════════════════════════════════════════════════

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Paso 5: Probar Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

**Respuesta**:
```json
{
  "ok": true,
  "mcp_loaded": true
}
```

#### Documentación Interactiva
Abrir en navegador: http://localhost:8000/docs

---

## 🔧 Herramientas MCP Disponibles

### CRM Tools (`tools/crm.py`)

#### `dev_create_quotation`
Crea una cotización completa en Odoo (lead + oportunidad + orden de venta + productos)

**Parámetros**:
```python
partner_name: str          # Nombre del cliente
contact_name: str          # Nombre del contacto
email: str                 # Email del contacto
phone: str                 # Teléfono
lead_name: str             # Nombre del lead/oportunidad
product_id: int = 0        # ID del producto (0 = sin producto)
product_qty: float = 1     # Cantidad
product_price: float = -1  # Precio (-1 = usar pricelist)
products: List[dict] = None # Lista de productos (formato nuevo)
user_id: int = 0           # ID del vendedor (0 = balanceo)
description: str = None    # Descripción adicional
x_studio_producto: int = None # Campo custom de Odoo
```

**Retorna**:
```python
{
    "tracking_id": "quot_abc123def456",
    "status": "completed",
    "output": {
        "partner_id": 12345,
        "lead_id": 67890,
        "opportunity_id": 67890,
        "sale_order_id": 11111,
        "sale_order_name": "S12345",
        "user_id": 42
    }
}
```

**Ejemplo de uso (Claude)**:
```
Usuario: "Crea una cotización para Robot PUDU, cliente Almacenes Torres, 
          contacto Luis Fernández, email luis@almacenes.com, 
          teléfono +521234567890, 2 unidades"

Claude llamará:
dev_create_quotation(
    partner_name="Almacenes Torres",
    contact_name="Luis Fernández",
    email="luis@almacenes.com",
    phone="+521234567890",
    lead_name="Cotización Robot PUDU",
    product_id=26174,
    product_qty=2
)
```

#### `get_salesperson_with_least_opportunities`
Obtiene el vendedor con menos oportunidades activas (balanceo de carga)

**Retorna**: `int` (ID del vendedor)

---

### Sales Tools (`tools/sales.py`)

#### `dev_create_sale`
Crea una orden de venta vacía

**Parámetros**:
```python
partner_id: int            # ID del cliente
user_id: int = None        # ID del vendedor
date_order: str = None     # Fecha de orden (ISO format)
note: str = None           # Notas internas
payment_term_id: int = None # Término de pago
```

#### `dev_create_sale_line`
Agrega producto a una orden de venta

**Parámetros**:
```python
order_id: int              # ID de la orden
product_id: int            # ID del producto
product_uom_qty: float = 1 # Cantidad
price_unit: float = None   # Precio (None = pricelist)
name: str = None           # Descripción custom
```

#### `dev_read_sale`
Lee datos de una orden de venta

#### `dev_update_sale`
Actualiza una orden de venta existente

---

### Search Tools (`tools/search.py`)

#### `search`
Búsqueda general en proyectos y tareas de Odoo

**Parámetros**:
```python
query: str                 # Texto de búsqueda
limit: int = 10            # Máximo de resultados
```

**Retorna**:
```python
[
    {
        "id": "project:123",
        "title": "Nombre del Proyecto",
        "url": "https://odoo.com/web#id=123&model=project.project"
    },
    {
        "id": "task:456",
        "title": "Nombre de la Tarea",
        "url": "https://odoo.com/web#id=456&model=project.task"
    }
]
```

#### `fetch`
Recupera documento completo por ID

---

### User Tools (`tools/users.py`)

#### `list_users`
Lista usuarios/vendedores con filtros

**Parámetros**:
```python
q: str = None              # Búsqueda por nombre
active: bool = None        # Filtrar activos/inactivos
limit: int = 50            # Máximo de resultados
```

---

### Project Tools (`tools/projects.py`)

#### `list_projects`
Lista proyectos con filtros opcionales

---

### Task Tools (`tools/tasks.py`)

#### `list_tasks`
Lista tareas con filtros

**Parámetros**:
```python
q: str = None              # Búsqueda por nombre
project_id: int = None     # Filtrar por proyecto
assigned_to: int = None    # Filtrar por usuario asignado
assigned_to_name: str = None # Filtrar por nombre de usuario
stage_id: int = None       # Filtrar por etapa
limit: int = 50
```

#### `get_task`
Obtiene detalle completo de una tarea

---

### WhatsApp Tools (`tools/whatsapp.py`)

#### `message_notification`
Envía notificación de handoff a vendedor

**Parámetros**:
```python
user_phone: str            # Teléfono del cliente
reason: str                # Motivo del handoff
user_name: str = None      # Nombre del cliente
conversation_id: str = None # ID de conversación
lead_id: int = None        # ID del lead (opcional)
sale_order_id: int = None  # ID de orden (opcional)
additional_context: str = None # Contexto adicional
```

---

## 🌐 API REST Endpoints

### POST `/api/quotation/async`

Crea cotización de forma asíncrona

**Request**:
```json
{
  "partner_name": "Almacenes Torres",
  "contact_name": "Luis Fernández",
  "email": "luis@almacenes.com",
  "phone": "+521234567890",
  "lead_name": "Cotización Robot PUDU",
  "product_id": 26174,
  "product_qty": 2
}
```

**Response (Inmediata)**:
```json
{
  "tracking_id": "quot_abc123def456",
  "status": "queued",
  "message": "Cotización en proceso...",
  "estimated_time": "20-30 segundos",
  "status_url": "/api/quotation/status/quot_abc123def456"
}
```

---

### GET `/api/quotation/status/{tracking_id}`

Consulta estado de cotización asíncrona

**Response (Processing)**:
```json
{
  "tracking_id": "quot_abc123def456",
  "status": "processing",
  "input": {...},
  "output": null,
  "error": null,
  "created_at": "2026-01-30T10:00:00",
  "updated_at": "2026-01-30T10:00:15"
}
```

**Response (Completed)**:
```json
{
  "tracking_id": "quot_abc123def456",
  "status": "completed",
  "input": {...},
  "output": {
    "partner_id": 12345,
    "lead_id": 67890,
    "sale_order_id": 11111,
    "sale_order_name": "S12345"
  },
  "error": null,
  "created_at": "2026-01-30T10:00:00",
  "updated_at": "2026-01-30T10:00:25"
}
```

---

### POST `/api/elevenlabs/handoff`

Handoff a vendedor humano desde ElevenLabs

**Request**:
```json
{
  "user_phone": "+5215512345678",
  "reason": "Cliente solicita información personalizada",
  "user_name": "Juan Pérez",
  "conversation_id": "conv_abc123",
  "additional_context": "Preguntó por robots para restaurante"
}
```

**Response**:
```json
{
  "status": "ok",
  "message": "Notificación SMS enviada al vendedor",
  "message_sid": "SM1234567890",
  "assigned_user_id": 42,
  "selected_number": "+5215587654321"
}
```

---

### GET `/health`

Health check para balanceadores de carga

**Response**:
```json
{
  "ok": true,
  "mcp_loaded": true
}
```

---

### GET `/docs`

Documentación interactiva Swagger UI

Abrir en navegador: http://localhost:8000/docs

---

## ⚠️ Problemas Comunes y Soluciones

### Problema 1: "Missing environment variables"

**Error**:
```
[WARN] Missing environment variables: ODOO_URL, ODOO_API_KEY
[INFO] Server will start but Odoo operations will fail.
```

**Causa**: Faltan variables en `.env`

**Solución**:
```bash
# Verifica que .env existe
ls -la .env

# Edita .env y agrega las variables faltantes
nano .env

# Verifica configuración
python -c "from core import Config; Config.print_config()"
```

---

### Problema 2: "Authentication failed" con Odoo

**Error**:
```
xmlrpc.client.Fault: Access Denied
```

**Causas posibles**:
1. **API Key incorrecta**: Verifica que la API key sea válida
2. **Login incorrecto**: El email debe coincidir con el de Odoo
3. **Permisos insuficientes**: El usuario necesita permisos de administrador

**Solución**:
```bash
# Probar autenticación manualmente
python -c "
from core import OdooClient
client = OdooClient()
print('✅ Autenticación exitosa' if client.uid else '❌ Falló')
"
```

**Obtener API Key en Odoo**:
1. Ir a Settings → Users & Companies → Users
2. Seleccionar tu usuario
3. Tab "Preferences"
4. Sección "Security" → Generar nueva API Key

---

### Problema 3: "Connection refused" al conectar

**Error**:
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Causa**: El servidor no está ejecutándose

**Solución**:
```bash
# Verifica si el puerto está en uso
lsof -i :8000

# Si no hay nada, ejecuta el servidor
python server.py

# Si hay algo, mata el proceso y reinicia
kill <PID>
python server.py
```

---

### Problema 4: Logs no se suben a S3

**Error**:
```
[WARN] S3 upload failed: NoCredentialsError
```

**Causas posibles**:
1. **Credenciales AWS faltantes**
2. **Bucket no existe**
3. **Permisos IAM incorrectos**

**Solución**:
```bash
# Verificar configuración AWS
aws s3 ls s3://tu-bucket-logs/

# Si falla, configurar credenciales
aws configure
# AWS Access Key ID: AKIAXXXXXXXX
# AWS Secret Access Key: xxxxxxxxxxxxxxxx
# Default region: us-west-2
# Default output format: json

# Verificar permisos del bucket
# El usuario/role necesita: s3:PutObject, s3:GetObject
```

Ver documentación completa: [docs/S3_LOGS_SETUP.md](docs/S3_LOGS_SETUP.md)

---

### Problema 5: WhatsApp no envía mensajes

**Error**:
```
TwilioRestException: 21211 - Invalid 'To' Phone Number
```

**Causas posibles**:
1. **Número en formato incorrecto**: Debe ser `+[código país][número]`
2. **Sandbox no configurado**: En desarrollo, usar sandbox de Twilio
3. **Credenciales incorrectas**

**Solución**:
```bash
# Verificar formato de número
# ✅ Correcto: +5215512345678
# ❌ Incorrecto: 5512345678, +52 55 1234 5678

# Probar envío manual
curl -X POST http://localhost:8000/api/elevenlabs/handoff \
  -H "Content-Type: application/json" \
  -d '{
    "user_phone": "+5215512345678",
    "reason": "Test"
  }'
```

**Configurar Sandbox Twilio** (desarrollo):
1. Ir a [Twilio Console → WhatsApp Sandbox](https://www.twilio.com/console/sms/whatsapp/sandbox)
2. Enviar mensaje desde WhatsApp al número de sandbox: `join <código>`
3. Agregar números adicionales siguiendo instrucciones

Ver documentación completa: [docs/WHATSAPP_HANDOFF.md](docs/WHATSAPP_HANDOFF.md)

---

### Problema 6: "Port already in use"

**Error**:
```
OSError: [Errno 98] Address already in use
```

**Causa**: El puerto 8000 ya está ocupado

**Solución**:
```bash
# Opción 1: Cambiar puerto
export PORT=8001
python server.py

# Opción 2: Matar proceso que usa el puerto
lsof -ti:8000 | xargs kill -9
python server.py
```

---

### Problema 7: Background tasks no se ejecutan

**Síntoma**: `/api/quotation/async` retorna tracking_id pero el estado siempre queda en "queued"

**Causa**: FastAPI background tasks requieren que el servidor esté corriendo

**Solución**:
```bash
# Verificar que el servidor NO use --workers > 1
# Background tasks no funcionan bien con múltiples workers

# ❌ Incorrecto
uvicorn server:app --workers 4

# ✅ Correcto
uvicorn server:app --workers 1
# o simplemente
python server.py
```

---

## 🧪 Desarrollo y Testing

### Testing Manual con cURL

#### Crear cotización asíncrona
```bash
curl -X POST http://localhost:8000/api/quotation/async \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "Test Cliente",
    "contact_name": "Juan Pérez",
    "email": "juan@test.com",
    "phone": "+5215512345678",
    "lead_name": "Test Cotización",
    "product_id": 26174,
    "product_qty": 1
  }'
```

#### Consultar estado
```bash
curl http://localhost:8000/api/quotation/status/quot_abc123def456
```

#### Health check
```bash
curl http://localhost:8000/health
```

---

### Testing con Cliente MCP (Claude Desktop)

1. **Instalar Claude Desktop** (si no lo tienes)

2. **Configurar MCP en Claude**:

Editar archivo de configuración:
- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uvicorn",
      "args": [
        "server:app",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "cwd": "/ruta/a/services/mcp-odoo"
    }
  }
}
```

3. **Reiniciar Claude Desktop**

4. **Probar herramientas**:
```
Tú: "Crea una cotización para Robot PUDU, cliente Test Corp, 
     contacto María García, email maria@test.com, 
     teléfono +521234567890"

Claude: [usará dev_create_quotation automáticamente]
```

---

### Logs y Debugging

#### Ver logs en tiempo real
```bash
# Terminal 1: Ejecutar servidor
python server.py

# Terminal 2: Ver logs locales
tail -f /tmp/mcp_odoo_logs/*.log | python -m json.tool
```

#### Ver logs en S3
```bash
# Listar logs del mes
aws s3 ls s3://tu-bucket/mcp-odoo-logs/2026/01/

# Descargar log específico
aws s3 cp s3://tu-bucket/mcp-odoo-logs/2026/01/quot_abc123.log .

# Ver contenido
cat quot_abc123.log | python -m json.tool
```

---

### Desarrollo con Docker

```bash
cd services/mcp-odoo

# Build imagen
docker build -t mcp-odoo:latest .

# Ejecutar contenedor
docker run --rm -it \
  -p 8000:8000 \
  --env-file .env \
  mcp-odoo:latest

# O usar docker-compose
docker-compose up
```

---

## 📊 Métricas y Monitoreo

### Endpoints de Monitoreo

#### Health Check
```bash
curl http://localhost:8000/health
```

**Usar para**:
- Balanceadores de carga (ALB, nginx)
- Healthchecks en Docker/Kubernetes
- Monitoreo con Datadog, New Relic, etc.

---

### Logs Estructurados

Todos los logs siguen formato JSON consistente:

```json
{
  "tracking_id": "quot_abc123",
  "timestamp": "2026-01-30T10:00:00",
  "date": "2026-01-30",
  "time": "10:00:00",
  "status": "completed",
  "input": {...},
  "output": {...},
  "error": null,
  "updated_at": "2026-01-30T10:00:25"
}
```

**Usar para**:
- Análisis con `jq`: `cat *.log | jq '.status' | sort | uniq -c`
- Ingestión en Elasticsearch
- Dashboard con Grafana
- Alertas con Prometheus

---

## 🚀 Deployment en Producción

### Opción 1: Servidor Tradicional

```bash
# Instalar gunicorn
pip install gunicorn

# Ejecutar con gunicorn
gunicorn server:app \
  --bind 0.0.0.0:8000 \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-logfile - \
  --error-logfile -
```

**Nota**: Solo 1 worker para background tasks

---

### Opción 2: Docker

Ver [scripts/README.md](scripts/README.md) para detalles completos.

```bash
cd scripts/
./build.sh
docker run -p 8000:8000 --env-file ../.env mcp-odoo:latest
```

---

### Opción 3: AWS App Runner

1. **Push imagen a ECR**
2. **Crear servicio en App Runner**
3. **Configurar variables de entorno**
4. **Configurar health check**: `/health`
5. **Deploy automático en git push**

---

### Variables de Producción

**Recomendaciones**:

```bash
# .env.production

# Usar IAM Role en lugar de Access Keys
AWS_ROLE_ARN=arn:aws:iam::123456:role/mcp-odoo-role

# Usar Secrets Manager para credenciales sensibles
ODOO_API_KEY={{resolve:secretsmanager:odoo-api-key}}
TWILIO_AUTH_TOKEN={{resolve:secretsmanager:twilio-auth-token}}

# Habilitar logging
LOG_LEVEL=INFO

# CORS si es necesario
CORS_ORIGINS=https://tu-frontend.com
```

---

## 📚 Documentación Adicional

- **[S3_LOGS_SETUP.md](docs/S3_LOGS_SETUP.md)** - Configuración detallada de logs en S3
- **[WHATSAPP_HANDOFF.md](docs/WHATSAPP_HANDOFF.md)** - Sistema de handoff a vendedores
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Diagramas de arquitectura completos
- **[scripts/README.md](scripts/README.md)** - Guía de deployment con Docker

---

## 🤝 Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea rama feature: `git checkout -b feature/nueva-herramienta`
3. Commit cambios: `git commit -m 'Add: nueva herramienta MCP'`
4. Push: `git push origin feature/nueva-herramienta`
5. Abre Pull Request

---

## 📄 Licencia

Proyecto privado y confidencial.

---

## 👤 Autor

**BravoMorteo**

---

## 📧 Soporte

Para dudas o problemas:
1. Revisa esta documentación
2. Revisa [Problemas Comunes](#problemas-comunes-y-soluciones)
3. Contacta al equipo de desarrollo

---

**Última actualización**: Enero 30, 2026  
**Versión**: 2.0.0  
**Estado**: ✅ Producción
