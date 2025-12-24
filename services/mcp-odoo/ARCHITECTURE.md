# 🏗️ Arquitectura MCP-Odoo - Servidor Híbrido# 🏗️ Arquitectura MCP-Odoo# Arquitectura MCP-Odoo



**Versión:** 2.0 (Implementación Híbrida)  

**Fecha:** Diciembre 2025  

**Estado:** ✅ Producción## Visión General## 🏗️ Visión General



---



## 📋 Visión GeneralServidor **híbrido** que combina:MCP-Odoo implementa una arquitectura modular de 3 capas para exponer funcionalidades de Odoo ERP a través del protocolo MCP.



MCP-Odoo implementa una **arquitectura híbrida** que combina dos protocolos en un solo servidor:1. **FastAPI** - API REST asíncrona para operaciones de escritura



1. **MCP Protocol (SSE + JSON-RPC)** → Para Claude Desktop y LLMs con soporte MCP2. **MCP Protocol** - Herramientas síncronas para búsqueda y lectura## 📐 Diagrama de Arquitectura

2. **REST API (HTTP)** → Para ElevenLabs, webhooks externos y aplicaciones estándar



### 🎯 Ventaja Clave: UN SOLO PROCESO

- ✅ Un solo servidor FastAPI en puerto 8000## Diagrama de Arquitectura```

- ✅ Código compartido (OdooClient, TaskManager, Logger)

- ✅ Estado compartido (TaskManager in-memory)┌────────────────────────────────────────────────────────┐

- ✅ Escalamiento simple (multiplica réplicas del mismo proceso)

- ✅ Un solo Dockerfile, un solo deploy```│           CLIENTE MCP                                  │



---┌──────────────────────────────────────────────────────┐│  (Claude Desktop, CLI, Custom Client)                  │



## 📐 Diagrama de Arquitectura Completo│              CLIENTES                                │└──────────────────────┬─────────────────────────────────┘



```│  • Claude Desktop (MCP)                              │                       │

                    INTERNET / CLIENTES

                           ││  • Frontend Web (REST API)                           │                  MCP Protocol

        ┌──────────────────┼──────────────────┐

        │                  │                  ││  • CLI/Scripts (REST API)                            │                       │

   ┌────▼──────┐    ┌─────▼──────┐    ┌─────▼─────┐

   │ Claude    │    │ ElevenLabs │    │  Otros    │└───────────────────┬──────────────────────────────────┘┌──────────────────────▼─────────────────────────────────┐

   │ Desktop   │    │  Webhooks  │    │  Clientes │

   └────┬──────┘    └─────┬──────┘    └─────┬─────┘                    ││                  SERVER.PY (Main)                      │

        │                 │                  │

        │ MCP Protocol    │ REST API         │ REST API        ┌───────────┴──────────┐│  - Inicialización ASGI                                 │

        │ (SSE+JSON-RPC)  │ (POST/GET)       │ (POST/GET)

        │                 │                  │        │                      ││  - Health check endpoint                               │

        ▼                 ▼                  ▼

┌────────────────────────────────────────────────────────┐   MCP Protocol           REST API│  - Carga lazy de tools                                 │

│           Puerto 8000 (UN SOLO PROCESO)                │

│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │        │                      │└──────────────────────┬─────────────────────────────────┘

│  ┃        FastAPI App (Servidor Principal)         ┃  │

│  ┗━━━━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │┌───────▼──────┐      ┌────────▼────────┐                       │

│                        │                               │

│       ┌────────────────┼────────────────┐              ││   FastMCP    │      │    FastAPI      │       ┌───────────────┴──────────────┐

│       │                │                │              │

│  ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐        ││   (Sync)     │      │    (Async)      │       │                              │

│  │  /mcp/*  │    │  /api/*  │    │ /health  │        │

│  │  (MCP)   │    │  (REST)  │    │ (Check)  │        ││              │      │                 │┌──────▼──────────┐         ┌────────▼────────┐

│  └────┬─────┘    └────┬─────┘    └──────────┘        │

│       │               │                                ││ • search     │      │ • /quotation/   ││  CORE/CONFIG.PY │         │    TOOLS/       │

│       │  /mcp/sse     │  /api/quotation/async         │

│       │  /mcp/messages│  /api/quotation/status/{id}   ││ • fetch      │      │   async         ││                 │         │   (Autoload)    │

│       │               │                                │

│       └───────┬───────┴──────────┐                    ││ • list_*     │      │ • /quotation/   ││ - Env vars      │         │                 │

│               │                  │                    │

│     ┌─────────▼──────────────────▼─────────┐         ││ • get_*      │      │   status/{id}   ││ - Validación    │         │ ┌─────────────┐ │

│     │     COMPONENTES COMPARTIDOS          │         │

│     │  ┌──────────────────────────────┐    │         │└───────┬──────┘      └────────┬────────┘│ - Constantes    │         │ │   crm.py    │ │

│     │  │   core/odoo_client.py        │    │         │

│     │  │   - XML-RPC client           │    │         │        │                      │└─────────────────┘         │ ├─────────────┤ │

│     │  │   - Partner/Lead/Sale ops    │    │         │

│     │  └──────────────────────────────┘    │         │        └──────────┬───────────┘                            │ │ projects.py │ │

│     │  ┌──────────────────────────────┐    │         │

│     │  │   core/task_manager.py       │    │         │                   │                            │ ├─────────────┤ │

│     │  │   - In-memory tracking       │    │         │

│     │  │   - Task lifecycle           │    │         │        ┌──────────▼──────────┐                            │ │  sales.py   │ │

│     │  └──────────────────────────────┘    │         │

│     │  ┌──────────────────────────────┐    │         │        │   server.py         │                            │ ├─────────────┤ │

│     │  │   core/logger.py             │    │         │

│     │  │   - JSON logs                │    │         │        │   (Main Entry)      │                            │ │  tasks.py   │ │

│     │  │   - S3 upload                │    │         │

│     │  └──────────────────────────────┘    │         │        └──────────┬──────────┘                            │ ├─────────────┤ │

│     │  ┌──────────────────────────────┐    │         │

│     │  │   Background Threads         │    │         │                   │                            │ │  users.py   │ │

│     │  │   - process_quotation()      │    │         │

│     │  └──────────────────────────────┘    │         │     ┌─────────────┼─────────────┐                            │ ├─────────────┤ │

│     └──────────────┬───────────────────────┘         │

└────────────────────┼─────────────────────────────────┘     │             │             │                            │ │ search.py   │ │

                     │

         ┌───────────┼───────────┐┌────▼─────┐  ┌───▼──────┐  ┌──▼──────┐                            │ └──────┬──────┘ │

         │           │           │

         ▼           ▼           ▼│  Tools/  │  │  Core/   │  │  Core/  │                            └────────┼────────┘

    ┌────────┐  ┌───────┐  ┌──────────┐

    │  Odoo  │  │  S3   │  │  Logs    ││          │  │  API     │  │  Logger │                                     │

    │XML-RPC │  │Bucket │  │  /tmp/   │

    └────────┘  └───────┘  └──────────┘│ • crm    │  │          │  │         │                    ┌────────────────┴──────────────┐

```

│ • sales  │  │ Background│  │ JSON → │                    │                               │

---

│ • tasks  │  │ Tasks    │  │  S3    │          ┌─────────▼─────────┐       ┌───────────▼──────────┐

## 🔄 Flujo de Datos Detallado

│ • search │  │          │  │         │          │     CORE/          │       │   CORE/helpers.py   │

### Flujo 1: Claude Desktop (MCP Protocol)

└────┬─────┘  └───┬──────┘  └──┬──────┘          │                    │       │                     │

```

1. Conexión SSE:     │            │            │          │ ┌────────────────┐ │       │ - encode_content() │

   Claude → GET /mcp/sse

   ← SSE stream establecido, session_id     └────────────┼────────────┘          │ │ odoo_client.py │ │       │ - odoo_form_url()  │



2. Listar Tools:                  │          │ │                │ │       │ - wants_*()        │

   Claude → POST /mcp/messages

           {"method": "tools/list"}        ┌─────────▼──────────┐          │ │ - search()     │ │       └────────────────────┘

   ← Lista de tools disponibles

        │  Core/OdooClient   │          │ │ - search_read()│ │

3. Llamar Tool (Crear cotización):

   Claude → POST /mcp/messages        │                    │          │ │ - read()       │ │

           {"method": "tools/call",

            "params": {        │  XML-RPC Methods:  │          │ │ - create()     │ │

              "name": "dev_create_quotation",

              "arguments": {        │  • search()        │          │ │ - write()      │ │

                "partner_name": "Cliente",

                "email": "cliente@example.com",        │  • search_read()   │          │ │ - unlink()     │ │

                ...

              }        │  • create()        │          │ └───────┬────────┘ │

            }}

           │  • write()         │          └─────────┼──────────┘

   Server → tools/crm.py::dev_create_quotation()

           ├─ Genera tracking_id        │  • unlink()        │                    │

           ├─ task_manager.create_task()

           ├─ Lanza thread en background        └─────────┬──────────┘                XML-RPC

           └─ Responde inmediatamente

                     │                    │

   ← {"tracking_id": "quot_abc123", "status": "queued"}

              XML-RPC          ┌─────────▼──────────┐

4. Background Processing:

   Thread → process_quotation_background()                  │          │    Odoo ERP        │

           ├─ odoo_client.get_or_create_partner()

           ├─ odoo_client.create_lead()        ┌─────────▼──────────┐          │  (External API)    │

           ├─ odoo_client.convert_to_opportunity()

           ├─ odoo_client.create_sale_order()        │   ODOO ERP         │          └────────────────────┘

           ├─ odoo_client.add_product_line()

           ├─ quotation_logger.log_quotation()        │                    │```

           └─ task_manager.complete_task()

        │ • Dev (escritura)  │

5. Consultar Estado (Opcional):

   Claude → POST /mcp/messages        │ • Prod (lectura)   │## 🎯 Capas de la Arquitectura

           {"method": "tools/call",

            "params": {"name": "dev_get_quotation_status", ...}}        └────────────────────┘

   

   ← {"status": "completed", "result": {...}}```### 1. **Capa de Aplicación** (`server.py`)

```



### Flujo 2: ElevenLabs (REST API)

## Flujo: Cotización Asíncrona**Responsabilidad:** Inicialización y orquestación del servidor MCP

```

1. Crear Cotización:

   ElevenLabs → POST /api/quotation/async

               Content-Type: application/json```mermaid#### Funciones principales:

               {

                 "partner_name": "Cliente desde ElevenLabs",sequenceDiagram- `app()` - Aplicación ASGI principal

                 "email": "cliente@example.com",

                 "phone": "+52 55 1234 5678",    participant C as Cliente- `mcp_app()` - Wrapper para compatibilidad de hosts

                 "lead_name": "Cotización voz",

                 "product_id": 26174,    participant API as FastAPI- `init_tools_once()` - Carga idempotente de tools

                 "product_qty": 1

               }    participant TM as TaskManager

   

   Server → create_quotation_async()    participant L as Logger**Características:**

           ├─ Valida request (Pydantic)

           ├─ Genera tracking_id    participant O as Odoo- Health check endpoint (`/health`)

           ├─ task_manager.create_task()

           ├─ Lanza thread en background    participant S3 as AWS S3- Carga lazy de tools (solo en primer request)

           └─ Responde inmediatamente

   - Manejo de errores global

   ← 202 Accepted

     {    C->>+API: POST /api/quotation/async

       "tracking_id": "quot_xyz789",

       "status": "queued",    API->>API: Generar tracking_id**Patrón:** Application Controller Pattern

       "message": "Cotización en proceso",

       "estimated_time": "20-30 segundos",    API->>L: log_quotation(tracking_id, input)

       "status_url": "/api/quotation/status/quot_xyz789"

     }    L->>L: Crear log local (started)### 2. **Capa de Tools** (`tools/`)



2. Background Processing:    L->>S3: Subir log inicial

   [MISMO PROCESO QUE MCP - Código compartido]

    API-->>C: {tracking_id, status: queued}**Responsabilidad:** Definir herramientas MCP que exponen funcionalidad Odoo

3. Consultar Estado:

   ElevenLabs → GET /api/quotation/status/quot_xyz789    

   

   ← 200 OK    API->>+TM: Encolar background task#### Estructura de un Tool Module

     {

       "tracking_id": "quot_xyz789",    TM->>O: 1. Verificar/crear partner

       "status": "completed",

       "created_at": "2025-12-22T15:30:00",    TM->>O: 2. Asignar vendedor (balanceo)Cada archivo debe exponer:

       "elapsed_time": "18.5s",

       "result": {    TM->>O: 3. Crear lead```python

         "sale_order_id": 18695,

         "sale_order_name": "S15434",    TM->>O: 4. Convertir a oportunidaddef register(mcp, deps):

         "partner_id": 124259,

         "lead_id": 27415,    TM->>O: 5. Crear sale order    @mcp.tool(name="tool_name", description="...")

         ...

       }    TM->>-L: update_quotation_log(output)    def tool_function(arg: type) -> dict:

     }

```    L->>L: Actualizar log (completed)        odoo = deps["odoo"]



---    L->>S3: Subir log final        # Implementación



## 🏗️ Estructura de Módulos            return result



### 📄 server.py (Main Entry Point)    C->>API: GET /status/{tracking_id}```



```python    API-->>C: {status: completed, result}

"""

Servidor híbrido FastAPI + FastMCP```#### Tools Disponibles

Un solo proceso que sirve ambos protocolos

"""



from fastapi import FastAPI## Módulos Principales##### `search.py`

from mcp.server.fastmcp import FastMCP

- `search()` - Búsqueda multi-modelo (proyectos/tareas)

# 1. Crear instancia MCP

mcp = FastMCP("mcp-odoo")### 1. `server.py` - Entry Point- `fetch()` - Recuperación de documento completo



# 2. Cargar tools (lazy loading)

def init_tools_once():

    if not _tools_loaded:**Responsabilidad:** Inicialización y orquestación##### `crm.py`

        # Carga dinámica de tools/crm.py, sales.py, etc.

        load_tools(mcp)- Tools de gestión de CRM



# 3. Crear app FastAPI (BASE)```python- Operaciones con leads, oportunidades, contactos

app = FastAPI(

    title="MCP-Odoo Hybrid Server",# Combina FastMCP y FastAPI

    version="2.0.0",

    description="Servidor híbrido MCP + REST"mcp = FastMCP("mcp-odoo")##### `projects.py`

)

api_app = FastAPI()  # Importado de core.api- Tools de gestión de proyectos

# 4. Montar MCP como sub-aplicación

init_tools_once()- CRUD de proyectos

app.mount("/mcp", mcp.sse_app())

# FastMCP crea automáticamente:# Mount API en /api

#   /mcp/sse      → GET (SSE stream)

#   /mcp/messages → POST (JSON-RPC)app.mount("/api", api_app)##### `sales.py`



# 5. Endpoints REST```- Tools de gestión de ventas

@app.get("/health")

async def health_check():- Pedidos, productos, clientes

    """Health check para AWS App Runner"""

    return {**Endpoints:**

        "status": "ok",

        "mcp_tools_loaded": _tools_loaded- `/mcp` - Protocolo MCP##### `tasks.py`

    }

- `/api/quotation/async` - Crear cotización- Tools de gestión de tareas

@app.post("/api/quotation/async", status_code=202)

async def create_quotation_async(request: QuotationRequest):- `/api/quotation/status/{id}` - Consultar estado- CRUD de tareas, asignaciones

    """Crear cotización asíncrona (para ElevenLabs)"""

    tracking_id = f"quot_{uuid.uuid4().hex[:12]}"- `/api/health` - Health check

    task_manager.create_task(tracking_id, request.dict())

    - `/docs` - Swagger UI##### `users.py`

    # Lanzar en background

    thread = threading.Thread(- Tools de gestión de usuarios

        target=process_quotation_background,

        args=(tracking_id, request)### 2. `core/config.py` - Configuración- Consulta de usuarios y permisos

    )

    thread.start()

    

    return {**Variables de entorno:**#### Autoload System

        "tracking_id": tracking_id,

        "status": "queued",

        "status_url": f"/api/quotation/status/{tracking_id}"

    }```python`tools/__init__.py` implementa carga automática:



@app.get("/api/quotation/status/{tracking_id}")# Odoo

async def get_quotation_status(tracking_id: str):

    """Consultar estado de cotización"""ODOO_URL, ODOO_DB, ODOO_LOGIN, ODOO_API_KEY```python

    task = task_manager.get_task(tracking_id)

    if not task:DEV_ODOO_URL, DEV_ODOO_DB, DEV_ODOO_LOGIN, DEV_ODOO_API_KEYdef load_all(mcp, deps):

        raise HTTPException(404, "Tracking ID no encontrado")

    return task.to_dict()    # Descubre todos los módulos en tools/



# 6. Iniciar servidor# S3 Logs    # Llama a register() de cada uno

if __name__ == "__main__":

    uvicorn.run(S3_LOGS_BUCKET, AWS_REGION, AWS_ROLE_ARN    # Maneja errores gracefully

        "server:app",

        host="0.0.0.0",MCP_LOG_DIR, LOG_RETENTION_DAYS```

        port=8000,

        log_level="info"

    )

```# Server**Ventaja:** Agregar un nuevo tool = crear archivo, automáticamente disponible



**Características:**PORT=8000

- ✅ Un solo archivo de entrada

- ✅ FastAPI como base principal```**Patrón:** Plugin Pattern, Dynamic Loading

- ✅ MCP montado en `/mcp`

- ✅ REST endpoints en `/api`

- ✅ Health check en `/health`

- ✅ Carga lazy de tools### 3. `core/odoo_client.py` - Cliente Odoo### 3. **Capa de Core** (`core/`)

- ✅ ~140 líneas (simple y mantenible)



---

**Clase:** `OdooClient`**Responsabilidad:** Abstracciones y utilidades fundamentales

### 📂 core/ (Componentes Compartidos)



#### core/config.py

```python**Métodos CRUD:**#### `odoo_client.py`

"""

Configuración centralizada```pythonCliente XML-RPC para Odoo:

Variables de entorno validadas

"""search(model, domain)          # Buscar IDs



import ossearch_read(model, domain, fields)  # Buscar y leer```python

from dotenv import load_dotenv

read(model, ids, fields)       # Leer registrosclass OdooClient:

load_dotenv()

create(model, values)          # Crear registro    def __init__(self):

class Config:

    # Odoowrite(model, ids, values)      # Actualizar        # Conecta usando variables de entorno

    ODOO_URL = os.getenv("ODOO_URL")

    ODOO_DB = os.getenv("ODOO_DB")unlink(model, ids)             # Eliminar        self.url = Config.ODOO_URL

    ODOO_USERNAME = os.getenv("ODOO_USERNAME")

    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")```        self.db = Config.ODOO_DB

    

    # AWS S3        # ...

    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")

    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")**Protocolo:** XML-RPC sobre HTTPS    

    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

    S3_BUCKET = os.getenv("S3_BUCKET", "ilagentslogs")    def search(self, model, domain, limit):

    

    # MCP### 4. `core/api.py` - FastAPI Endpoints        # Búsqueda de IDs

    MCP_NAME = os.getenv("MCP_NAME", "mcp-odoo")

        

    @classmethod

    def validate(cls):**Endpoints asíncronos:**    def search_read(self, model, domain, fields, limit):

        """Valida que todas las variables requeridas existan"""

        required = [        # Búsqueda + lectura en una llamada

            "ODOO_URL", "ODOO_DB", 

            "ODOO_USERNAME", "ODOO_PASSWORD"```python    

        ]

        missing = [k for k in required if not getattr(cls, k)]POST /api/quotation/async    def read(self, model, ids, fields):

        if missing:

            raise ValueError(f"Variables faltantes: {missing}")  → Crea quotation en background        # Lectura de campos



config = Config()  → Retorna tracking_id inmediatamente    

config.validate()

```    def create(self, model, values):



#### core/odoo_client.pyGET /api/quotation/status/{tracking_id}        # Creación de registros

```python

"""  → Consulta estado de la cotización    

Cliente XML-RPC para Odoo

Operaciones CRUD en Partner, Lead, Sale Order  → Estados: queued, processing, completed, failed    def write(self, model, ids, values):

"""

```        # Actualización

import xmlrpc.client

    

class OdooClient:

    def __init__(self):**Background Task Flow:**    def unlink(self, model, ids):

        self.url = config.ODOO_URL

        self.db = config.ODOO_DB1. Validar datos con Pydantic        # Eliminación

        self.username = config.ODOO_USERNAME

        self.password = config.ODOO_PASSWORD2. Generar tracking_id único```

        

        # Autenticación3. Registrar en logger (status: started)

        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")

        self.uid = common.authenticate(4. Encolar en TaskManager**Patrón:** Repository Pattern, Facade Pattern

            self.db, self.username, self.password, {}

        )5. Retornar tracking_id al cliente

        

        # Cliente de modelos6. Procesar en background:#### `helpers.py`

        self.models = xmlrpc.client.ServerProxy(

            f"{self.url}/xmlrpc/2/object"   - Partner → Vendedor → Lead → Opportunity → Sale OrderFunciones de utilidad:

        )

    7. Actualizar logger (status: completed/failed)

    def execute(self, model, method, *args, **kwargs):

        """Ejecuta método en modelo Odoo"""```python

        return self.models.execute_kw(

            self.db, self.uid, self.password,### 5. `core/tasks.py` - Task Managerdef encode_content(obj) -> dict:

            model, method, args, kwargs

        )    # Formatea respuestas MCP

    

    def get_or_create_partner(self, name, email, phone):**Clase:** `TaskManager`    return {"content": [{"type": "text", "text": json.dumps(obj)}]}

        """Busca o crea un partner"""

        # Buscar por email

        partner_ids = self.execute(

            'res.partner', 'search',**Funcionalidad:**def odoo_form_url(model, rec_id) -> str:

            [['email', '=', email]]

        )- Almacena estado de tareas en memoria    # Genera URL del formulario Odoo

        

        if partner_ids:- Proporciona métodos para consultar estado    return f"{Config.ODOO_URL}/web#id={rec_id}&model={model}&view_type=form"

            return partner_ids[0]

        - Thread-safe con lock

        # Crear nuevo

        return self.execute(def wants_projects(query) -> bool:

            'res.partner', 'create',

            {**Estados:**    # Detecta si query busca proyectos

                'name': name,

                'email': email,- `queued` - En cola    return any(t in query.lower() for t in ("proyecto", "project", ...))

                'phone': phone,

                'customer_rank': 1- `processing` - Ejecutándose

            }

        )- `completed` - Finalizadodef wants_tasks(query) -> bool:

    

    def create_lead(self, name, partner_id, description=None):- `failed` - Error    # Detecta si query busca tareas

        """Crea un lead/oportunidad"""

        return self.execute(    return any(t in query.lower() for t in ("tarea", "task", ...))

            'crm.lead', 'create',

            {### 6. `core/logger.py` - Sistema de Logging```

                'name': name,

                'partner_id': partner_id,

                'type': 'lead',

                'description': description**Clase:** `QuotationLogger`**Patrón:** Utility Pattern

            }

        )

    

    def convert_to_opportunity(self, lead_id):**Funcionalidad:**### 4. **Capa de Configuración** (`core/config.py`)

        """Convierte lead a oportunidad"""

        self.execute(```python

            'crm.lead', 'write',

            [lead_id], {'type': 'opportunity'}log_quotation(tracking_id, input_data, status="started")**Responsabilidad:** Gestión de configuración centralizada

        )

        return lead_id  → Crea log JSON local

    

    def create_sale_order(self, partner_id, user_id=None):  → Sube a S3```python

        """Crea orden de venta"""

        values = {class Config:

            'partner_id': partner_id,

            'state': 'draft'update_quotation_log(tracking_id, output_data, status="completed")    # Odoo Configuration

        }

        if user_id:  → Actualiza log existente    ODOO_URL = os.getenv("ODOO_URL")

            values['user_id'] = user_id

          → Vuelve a subir a S3    ODOO_DB = os.getenv("ODOO_DB")

        return self.execute('sale.order', 'create', values)

    ```    ODOO_LOGIN = os.getenv("ODOO_LOGIN")

    def add_product_line(self, order_id, product_id, qty, price):

        """Agrega línea de producto a orden"""    ODOO_API_KEY = os.getenv("ODOO_API_KEY")

        return self.execute(

            'sale.order.line', 'create',**Estructura del log:**    

            {

                'order_id': order_id,```json    # Server Configuration

                'product_id': product_id,

                'product_uom_qty': qty,{    HOST = "0.0.0.0"

                'price_unit': price

            }  "tracking_id": "quot_xxx",    PORT = int(os.getenv("PORT", "8000"))

        )

```  "timestamp": "2025-12-22T10:48:40.405304",    



#### core/task_manager.py  "date": "2025-12-22",    @classmethod

```python

"""  "status": "completed|failed|started",    def validate(cls) -> List[str]:

Gestor de tareas in-memory

Tracking de cotizaciones en proceso  "input": { ... },        # Retorna variables faltantes

"""

  "output": { ... },    

from datetime import datetime

from typing import Dict, Optional  "error": null,    @classmethod

from dataclasses import dataclass, field

  "updated_at": "2025-12-22T10:48:55.806648"    def is_valid(cls) -> bool:

@dataclass

class QuotationTask:}        # True si configuración OK

    tracking_id: str

    status: str  # queued, processing, completed, failed```    

    created_at: datetime

    params: dict    @classmethod

    progress: str = "Iniciando..."

    result: Optional[dict] = None**Storage:**    def print_config(cls):

    error: Optional[str] = None

    completed_at: Optional[datetime] = None- Local: `/tmp/mcp_odoo_logs/YYYY-MM-DD_tracking_id.log`        # Imprime configuración (sin exponer secrets)

    

    def to_dict(self):- S3: `s3://bucket/mcp-odoo-logs/YYYY/MM/YYYY-MM-DD_tracking_id.log````

        """Serializa tarea para respuesta API"""

        return {

            "tracking_id": self.tracking_id,

            "status": self.status,### 7. `tools/` - MCP Tools**Patrón:** Singleton Pattern, Configuration Object

            "created_at": self.created_at.isoformat(),

            "progress": self.progress,

            "result": self.result,

            "error": self.error,**Módulos:**## 🔄 Flujo de Ejecución

            "elapsed_time": self._elapsed_time(),

            "completed_at": self.completed_at.isoformat() - `crm.py` - Gestión de CRM (dev env)

                            if self.completed_at else None

        }- `sales.py` - Gestión de ventas (dev env)### Inicialización

    

    def _elapsed_time(self):- `projects.py` - Listado de proyectos

        """Calcula tiempo transcurrido"""

        end = self.completed_at or datetime.now()- `tasks.py` - Listado de tareas```python

        delta = end - self.created_at

        return f"{delta.total_seconds():.2f}s"- `users.py` - Listado de usuarios1. Cargar Config



class TaskManager:- `search.py` - Búsqueda unificada2. Crear FastMCP instance

    """Gestor de tareas en memoria"""

    3. Registrar ASGI app

    def __init__(self):

        self._tasks: Dict[str, QuotationTask] = {}**Patrón de registro:**4. Iniciar servidor uvicorn

    

    def create_task(self, tracking_id: str, params: dict):```python5. Esperar primer request

        """Crea nueva tarea"""

        task = QuotationTask(def register(mcp, deps):```

            tracking_id=tracking_id,

            status="queued",    odoo = deps["odoo"]

            created_at=datetime.now(),

            params=params    ### Primer Request

        )

        self._tasks[tracking_id] = task    @mcp.tool(name="tool_name")

        return task

        def tool_function(param: str) -> dict:```python

    def get_task(self, tracking_id: str) -> Optional[QuotationTask]:

        """Obtiene tarea por ID"""        result = odoo.search_read(...)1. Request llega a app()

        return self._tasks.get(tracking_id)

            return {"results": result}2. Detectar que tools no están cargados

    def update_task(self, tracking_id: str, **kwargs):

        """Actualiza campos de tarea"""```3. Llamar init_tools_once()

        task = self._tasks.get(tracking_id)

        if task:   3.1. Validar configuración

            for key, value in kwargs.items():

                setattr(task, key, value)**Autoload:** `tools/__init__.py` carga todos los módulos automáticamente   3.2. Crear OdooClient

    

    def complete_task(self, tracking_id: str, result: dict):   3.3. Cargar todos los tools (autoload)

        """Marca tarea como completada"""

        self.update_task(## Patrones de Diseño   3.4. Marcar como cargado

            tracking_id,

            status="completed",4. Procesar request normalmente

            result=result,

            completed_at=datetime.now()### 1. Singleton Pattern```

        )

    - `quotation_logger` - Instancia única del logger

    def fail_task(self, tracking_id: str, error: str):

        """Marca tarea como fallida"""- `task_manager` - Instancia única del task manager### Request de Tool

        self.update_task(

            tracking_id,

            status="failed",

            error=error,### 2. Repository Pattern```python

            completed_at=datetime.now()

        )- `OdooClient` - Abstrae acceso a Odoo1. Cliente envía request MCP



# Instancia global (compartida por MCP y REST)- Separa lógica de negocio de acceso a datos2. FastMCP parsea request

task_manager = TaskManager()

```3. Identificar tool solicitado



#### core/logger.py### 3. Background Tasks Pattern4. Ejecutar función del tool

```python

"""- FastAPI `BackgroundTasks`   4.1. Tool usa OdooClient

Logger de cotizaciones con upload a S3

JSON logs persistentes- Desacopla request/response del procesamiento largo   4.2. OdooClient hace llamada XML-RPC a Odoo

"""

   4.3. Tool procesa respuesta

import json

import os### 4. Strategy Pattern   4.4. Tool formatea con encode_content()

from datetime import datetime

import boto3- Múltiples métodos de autenticación S3:5. FastMCP serializa respuesta



class QuotationLogger:  - Access Keys6. Enviar respuesta al cliente

    def __init__(self):

        self.log_dir = os.getenv("LOG_DIR", "/tmp/mcp_odoo_logs")  - IAM Role```

        os.makedirs(self.log_dir, exist_ok=True)

          - AssumeRole

        # Cliente S3

        self.s3 = boto3.client(### Health Check

            's3',

            aws_access_key_id=config.AWS_ACCESS_KEY_ID,### 5. Lazy Loading

            aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,

            region_name=config.AWS_REGION- Tools se cargan solo cuando se necesitan```python

        )

        self.bucket = config.S3_BUCKET- `init_tools_once()` es idempotente1. Request a /health

    

    def log_quotation(self, tracking_id, input_data, status="started"):2. Retornar {"ok": true} inmediatamente

        """Crea log inicial de cotización"""

        log_data = {## Decisiones de Arquitectura3. No cargar tools (optimización)

            "tracking_id": tracking_id,

            "timestamp": datetime.now().isoformat(),```

            "status": status,

            "input": input_data,### ¿Por qué FastAPI + FastMCP?

            "output": None

        }## 🔌 Integración con Odoo

        

        # Guardar local**FastAPI:**

        log_file = self._get_log_path(tracking_id)

        with open(log_file, 'w') as f:- ✅ Async/await nativo### XML-RPC Protocol

            json.dump(log_data, f, indent=2)

        - ✅ Background tasks

        return log_file

    - ✅ Pydantic validationOdoo expone una API XML-RPC en dos endpoints:

    def update_quotation_log(self, tracking_id, output_data, 

                             status="completed"):- ✅ OpenAPI/Swagger automático

        """Actualiza log con resultado"""

        log_file = self._get_log_path(tracking_id)- ✅ Alto performance1. **Authentication:** `/xmlrpc/2/common`

        

        # Leer log existente   - `authenticate()` - Login y obtención de UID

        with open(log_file, 'r') as f:

            log_data = json.load(f)**FastMCP:**

        

        # Actualizar- ✅ Implementación oficial de MCP2. **Object Methods:** `/xmlrpc/2/object`

        log_data.update({

            "status": status,- ✅ Decoradores simples   - `execute_kw()` - Ejecutar métodos del modelo

            "output": output_data,

            "completed_at": datetime.now().isoformat()- ✅ Type hints

        })

        - ✅ Compatible con Claude Desktop### Ejemplo de Llamada

        # Guardar local

        with open(log_file, 'w') as f:

            json.dump(log_data, f, indent=2)

        ### ¿Por qué dos ambientes Odoo?```python

        # Upload a S3

        self._upload_to_s3(log_file, tracking_id)# Autenticación

        

        return log_file**Producción (solo lectura):**uid = common.authenticate(db, username, api_key, {})

    

    def _get_log_path(self, tracking_id):- Búsqueda de datos

        """Genera path de archivo de log"""

        date_str = datetime.now().strftime("%Y-%m-%d")- Consultas de información# Búsqueda

        return os.path.join(

            self.log_dir, - Sin riesgo de modificar datos realesids = models.execute_kw(

            f"{date_str}_{tracking_id}.log"

        )    db, uid, api_key,

    

    def _upload_to_s3(self, log_file, tracking_id):**Desarrollo (escritura):**    'project.project',  # modelo

        """Sube log a S3"""

        try:- Crear leads, partners, cotizaciones    'search',           # método

            now = datetime.now()

            s3_key = f"mcp-odoo-logs/{now.year}/{now.month:02d}/{tracking_id}.log"- Testing seguro    [[['active', '=', True]]],  # domain

            

            self.s3.upload_file(- No afecta datos de producción    {'limit': 10}       # options

                log_file,

                self.bucket,)

                s3_key

            )### ¿Por qué logs en S3?```

            print(f"✅ Log uploaded to s3://{self.bucket}/{s3_key}")

        except Exception as e:

            print(f"❌ S3 upload failed: {e}")

**Ventajas:**## 🎨 Patrones de Diseño

# Instancia global

quotation_logger = QuotationLogger()- ✅ Almacenamiento permanente

```

- ✅ Auditoría completa### 1. **Plugin Pattern (Tools)**

#### core/api.py

```python- ✅ Análisis con Athena/SQLCada tool es un plugin que se carga dinámicamente.

"""

Modelos Pydantic y función de procesamiento background- ✅ Backup automático

Compartido por MCP y REST

"""- ✅ Lifecycle policies**Ventaja:** Extensibilidad sin modificar core



from pydantic import BaseModel, EmailStr- ✅ Acceso desde cualquier lugar

from typing import Optional

### 2. **Repository Pattern (OdooClient)**

class QuotationRequest(BaseModel):

    """Request para crear cotización"""## Flujos de Datos`OdooClient` abstrae el acceso a datos de Odoo.

    partner_name: str

    contact_name: str

    email: EmailStr

    phone: str### Flujo de Lectura (MCP Tools)**Ventaja:** Cambiar implementación (XML-RPC → REST) sin afectar tools

    lead_name: str

    product_id: int = 0

    product_qty: float = 1

    product_price: float = -1```### 3. **Facade Pattern (Helpers)**

    user_id: int = 0

Cliente → MCP Tool → OdooClient → Odoo Prod → ResponseFunciones helper simplifican operaciones comunes.

class QuotationResponse(BaseModel):

    """Response de cotización creada"""   ↓

    tracking_id: str

    status: strRespuesta inmediata (síncrono)**Ventaja:** Código de tools más limpio

    message: str

    estimated_time: str = "20-30 segundos"```

    status_url: Optional[str] = None

    check_status_with: Optional[str] = None### 4. **Lazy Loading (Tools)**



def process_quotation_background(tracking_id: str, ### Flujo de Escritura (FastAPI)Tools se cargan solo en primer request real.

                                 request: QuotationRequest):

    """

    Procesa cotización en background

    FUNCIÓN COMPARTIDA por MCP y REST```**Ventaja:** Inicio rápido, health checks no cargan Odoo

    """

    try:Cliente → FastAPI Endpoint → TaskManager

        # 1. Actualizar estado

        task_manager.update_task(   ↓                              ↓### 5. **Dependency Injection (deps)**

            tracking_id,

            status="processing",Tracking ID              Background TaskLos tools reciben dependencias vía `deps` dict.

            progress="Conectando a Odoo..."

        )   ↓                              ↓

        

        # 2. Log inicialResponse                  OdooClient → Odoo Dev**Ventaja:** Testing fácil (mock de OdooClient)

        quotation_logger.log_quotation(

            tracking_id,                                   ↓

            request.dict(),

            status="processing"                           Logger → S3## 📦 Dependencias entre Módulos

        )

        ```

        # 3. Cliente Odoo

        odoo = OdooClient()```

        

        # 4. Crear/buscar partner## Seguridadserver.py

        task_manager.update_task(

            tracking_id,   ↓

            progress="Creando partner..."

        )### Autenticación Odoo  ├─→ core/config.py

        partner_id = odoo.get_or_create_partner(

            request.partner_name,- API Key en headers  ├─→ core/odoo_client.py

            request.email,

            request.phone- XML-RPC sobre HTTPS  │     ↓

        )

        - Credenciales en `.env` (no en código)  │     └─→ core/config.py

        # 5. Crear lead

        task_manager.update_task(  ├─→ core/helpers.py

            tracking_id,

            progress="Creando lead..."### Autenticación S3  │     ↓

        )

        lead_id = odoo.create_lead(- IAM Role (recomendado producción)  │     └─→ core/config.py

            request.lead_name,

            partner_id- Access Keys (desarrollo)  └─→ tools/__init__.py

        )

        - AssumeRole (multi-cuenta)        ↓

        # 6. Convertir a oportunidad

        task_manager.update_task(        ├─→ tools/crm.py

            tracking_id,

            progress="Convirtiendo a oportunidad..."### Validación        │     ↓

        )

        opp_id = odoo.convert_to_opportunity(lead_id)- Pydantic models en FastAPI        │     └─→ core/ (config, odoo_client, helpers)

        

        # 7. Crear orden de venta- Type hints en MCP tools        ├─→ tools/projects.py

        task_manager.update_task(

            tracking_id,- Validación de env vars al inicio        │     ↓

            progress="Creando orden de venta..."

        )        │     └─→ core/

        sale_order_id = odoo.create_sale_order(

            partner_id,## Performance        ├─→ tools/sales.py

            request.user_id if request.user_id > 0 else None

        )        │     ↓

        

        # 8. Agregar producto### Optimizaciones        │     └─→ core/

        if request.product_id > 0:

            task_manager.update_task(- **Async I/O:** FastAPI + uvicorn        ├─→ tools/tasks.py

                tracking_id,

                progress="Agregando producto..."- **Background tasks:** No bloquea requests        │     ↓

            )

            - **Lazy loading:** Tools solo cuando se usan        │     └─→ core/

            # Obtener precio si no se proporcionó

            price = request.product_price- **Connection pooling:** XML-RPC reutiliza conexiones        ├─→ tools/users.py

            if price < 0:

                product = odoo.execute(        │     ↓

                    'product.product', 'read',

                    [request.product_id],### Escalabilidad        │     └─→ core/

                    ['list_price']

                )[0]- **Stateless:** Task manager puede moverse a Redis        └─→ tools/search.py

                price = product['list_price']

            - **Horizontal:** Múltiples workers de uvicorn              ↓

            line_id = odoo.add_product_line(

                sale_order_id,- **Logs distribuidos:** S3 centralizado              └─→ core/

                request.product_id,

                request.product_qty,```

                price

            )## Monitoreo

        

        # 9. Obtener nombre de orden**Principio aplicado:** Dependencias fluyen hacia abajo (no hay ciclos)

        sale_order = odoo.execute(

            'sale.order', 'read',### Logs del servidor

            [sale_order_id],

            ['name']```bash## 🧪 Testing Strategy

        )[0]

        tail -f /tmp/mcp_server.log

        # 10. Resultado final

        result = {```### Unit Tests

            "partner_id": partner_id,

            "partner_name": request.partner_name,

            "lead_id": lead_id,

            "lead_name": request.lead_name,### Logs de cotizaciones```python

            "opportunity_id": opp_id,

            "sale_order_id": sale_order_id,```bash# test_odoo_client.py

            "sale_order_name": sale_order['name'],

            "environment": "development" if "dev" in config.ODOO_URL else "production"ls -lh /tmp/mcp_odoo_logs/def test_search():

        }

        cat /tmp/mcp_odoo_logs/2025-12-22_quot_xxx.log | python -m json.tool    client = OdooClient()

        # 11. Completar tarea

        task_manager.complete_task(tracking_id, result)```    # Mock XML-RPC calls

        

        # 12. Log final    result = client.search('res.users', [], 1)

        quotation_logger.update_quotation_log(

            tracking_id,### Health check    assert isinstance(result, list)

            result,

            status="completed"```bash

        )

        curl http://localhost:8000/api/health# test_helpers.py

        print(f"✅ Cotización {tracking_id} completada: {sale_order['name']}")

        ```def test_encode_content():

    except Exception as e:

        # Error handling    result = encode_content({"foo": "bar"})

        error_msg = str(e)

        print(f"❌ Error en {tracking_id}: {error_msg}")### Métricas (futuro)    assert result["content"][0]["type"] == "text"

        

        task_manager.fail_task(tracking_id, error_msg)- Prometheus + Grafana

        

        quotation_logger.update_quotation_log(- Tiempo de procesamiento por cotización# test_search_tool.py

            tracking_id,

            {"error": error_msg},- Rate de éxito/fallodef test_search_tool():

            status="failed"

        )- Uso de recursos    mcp = Mock()

```

    deps = {"odoo": Mock()}

---

## Testing    register_search_tools(mcp, deps)

### 📂 tools/ (MCP Tools)

    # Verify tools registered

#### tools/crm.py

```python### Unit Tests```

"""

MCP tools para CRM (Leads, Oportunidades, Cotizaciones)```bash

"""

pytest tests/### Integration Tests

from core.api import (

    QuotationRequest, ```

    process_quotation_background,

    task_manager```python

)

import uuid### Integration Tests# test_integration.py

import threading

```bashdef test_full_flow():

def dev_create_quotation(

    partner_name: str,./examples/test_s3_logs.sh    # Start server

    contact_name: str,

    email: str,```    # Send MCP request

    phone: str,

    lead_name: str,    # Verify Odoo called

    product_id: int = 0,

    product_qty: float = 1,### Manual Testing    # Verify response format

    product_price: float = -1,

    user_id: int = 0```bash```

) -> dict:

    """# Swagger UI

    Crea una cotización completa de forma ASÍNCRONA.

    Retorna tracking_id inmediatamente.open http://localhost:8000/docs### Manual Testing

    

    @param partner_name: Nombre de la empresa cliente

    @param contact_name: Nombre del contacto

    @param email: Email del contacto# CLI```bash

    @param phone: Teléfono del contacto

    @param lead_name: Descripción de la cotizacióncurl -X POST http://localhost:8000/api/quotation/async \# Test tool via CLI

    @param product_id: ID del producto (opcional)

    @param product_qty: Cantidad (default: 1)  -H "Content-Type: application/json" \mcp call odoo search --query "proyectos"

    @param product_price: Precio unitario (default: -1 = usar precio de lista)

    @param user_id: ID del vendedor (default: 0 = asignación automática)  -d '{"partner_name": "Test", ...}'

    """

    ```# Test via Python

    # 1. Generar tracking_id

    tracking_id = f"quot_{uuid.uuid4().hex[:12]}"python -c "from tools.search import *; ..."

    

    # 2. Crear request object## Deployment```

    request = QuotationRequest(

        partner_name=partner_name,

        contact_name=contact_name,

        email=email,### Local## 🔒 Seguridad

        phone=phone,

        lead_name=lead_name,```bash

        product_id=product_id,

        product_qty=product_qty,python -u server.py > /tmp/mcp_server.log 2>&1 &### Variables de Entorno

        product_price=product_price,

        user_id=user_id```- API keys en `.env`, nunca en código

    )

    - `.env` en `.gitignore`

    # 3. Crear tarea

    task_manager.create_task(tracking_id, request.dict())### Docker- Validación de variables requeridas

    

    # 4. Lanzar procesamiento en background```bash

    thread = threading.Thread(

        target=process_quotation_background,docker build -t mcp-odoo .### XML-RPC

        args=(tracking_id, request)

    )docker run -p 8000:8000 --env-file .env mcp-odoo- Usa HTTPS en producción

    thread.start()

    ```- API key en lugar de contraseña

    # 5. Respuesta inmediata

    return {- Rate limiting recomendado

        "tracking_id": tracking_id,

        "status": "queued",### Producción

        "message": "Cotización en proceso. Usa dev_get_quotation_status() para consultar el estado.",

        "estimated_time": "20-30 segundos",- EC2 con IAM Role para S3### MCP Protocol

        "check_status_with": f"dev_get_quotation_status(tracking_id='{tracking_id}')"

    }- Nginx como reverse proxy- Autenticación delegada a MCP client



def dev_get_quotation_status(tracking_id: str) -> dict:- Systemd para auto-restart- Validación de inputs en tools

    """

    Consulta el estado de una cotización asíncrona.- CloudWatch para logs

    

    @param tracking_id: ID de tracking retornado por dev_create_quotation()## 🚀 Escalabilidad

    """

    task = task_manager.get_task(tracking_id)## Mejoras Futuras

    

    if not task:### Horizontal Scaling

        return {

            "error": "Tracking ID no encontrado",### Short-term- Servidor stateless (no sesiones en memoria)

            "tracking_id": tracking_id

        }- [ ] Task manager con Redis (persistencia)- Múltiples instancias detrás de load balancer

    

    return task.to_dict()- [ ] Rate limiting- Odoo escala independientemente

```

- [ ] Retry logic para Odoo

---

- [ ] Cache de búsquedas frecuentes### Caching

## 🔗 Endpoints Disponibles

- Considerar caché de búsquedas frecuentes

### MCP Protocol (Claude Desktop)

### Long-term- Redis para caché distribuido

**Conexión SSE:**

```- [ ] WebSocket para updates en tiempo real- TTL corto para datos cambiantes

GET /mcp/sse

```- [ ] Queue system (Celery/RQ)



**JSON-RPC:**- [ ] GraphQL API### Performance

```

POST /mcp/messages- [ ] Multi-tenancy- Connection pooling para XML-RPC

Content-Type: application/json

- Batch operations donde sea posible

{

  "jsonrpc": "2.0",## Referencias- Índices en Odoo para búsquedas

  "id": 1,

  "method": "tools/list"  // o "tools/call"

}

```- **FastAPI:** https://fastapi.tiangolo.com/## 📈 Métricas Importantes



**Tools Disponibles:**- **FastMCP:** https://github.com/jlowin/fastmcp

- `dev_create_quotation` - Crear cotización async

- `dev_get_quotation_status` - Consultar estado- **Odoo API:** https://www.odoo.com/documentation/- **Latencia tool:** Tiempo de ejecución de cada tool

- `list_projects` - Listar proyectos Odoo

- `list_tasks` - Listar tareas- **boto3:** https://boto3.amazonaws.com/v1/documentation/- **Latencia Odoo:** Tiempo de respuesta XML-RPC

- `list_sales` - Listar órdenes de venta

- `search` - Búsqueda semántica- **Tasa de error:** Fallos en llamadas Odoo



### REST API (ElevenLabs / Webhooks)---- **Tools más usados:** Estadísticas de uso



**Health Check:**

```

GET /health**Ver también:**## 🔧 Extensibilidad



Response:- [README.md](README.md) - Inicio rápido

{

  "status": "ok",- [docs/LOGGING.md](docs/LOGGING.md) - Sistema de logs### Agregar Nuevo Tool

  "mcp_tools_loaded": true

}- [docs/S3_LOGS_SETUP.md](docs/S3_LOGS_SETUP.md) - Setup S3

```

1. Crear `tools/mi_tool.py`:

**Crear Cotización:**```python

```from core import encode_content

POST /api/quotation/async

Content-Type: application/jsondef register(mcp, deps):

    @mcp.tool(name="mi_tool", description="...")

{    def mi_tool(param: str) -> dict:

  "partner_name": "Cliente Ejemplo",        odoo = deps["odoo"]

  "contact_name": "Juan Pérez",        # Implementación

  "email": "juan@ejemplo.com",        result = odoo.search_read(...)

  "phone": "+52 55 1234 5678",        return encode_content({"result": result})

  "lead_name": "Cotización Robot PUDU",```

  "product_id": 26174,

  "product_qty": 12. Reiniciar servidor → Tool disponible automáticamente

}

### Agregar Nuevo Modelo Odoo

Response: 202 Accepted

{1. Extender `OdooClient` si necesario

  "tracking_id": "quot_abc123def456",2. Crear tool que use el modelo

  "status": "queued",3. Documentar en README

  "message": "Cotización en proceso",

  "estimated_time": "20-30 segundos",### Cambiar Backend (XML-RPC → REST)

  "status_url": "/api/quotation/status/quot_abc123def456"

}1. Crear `core/odoo_rest_client.py`

```2. Implementar misma interfaz que `OdooClient`

3. Cambiar en `server.py`: `deps["odoo"] = OdooRestClient()`

**Consultar Estado:**4. Tools siguen funcionando sin cambios

```

GET /api/quotation/status/quot_abc123def456---



Response: 200 OK**Principios de diseño:**

{- ✅ Modularidad (tools independientes)

  "tracking_id": "quot_abc123def456",- ✅ Extensibilidad (plugin system)

  "status": "completed",- ✅ Testabilidad (dependency injection)

  "created_at": "2025-12-22T15:30:00.123456",- ✅ Mantenibilidad (separación de concerns)

  "elapsed_time": "18.5s",- ✅ Performance (lazy loading)

  "progress": "Completado",

  "result": {**Última actualización:** 15 de diciembre de 2025

    "partner_id": 124258,
    "partner_name": "Cliente Ejemplo",
    "lead_id": 27414,
    "lead_name": "Cotización Robot PUDU",
    "opportunity_id": 27414,
    "sale_order_id": 18694,
    "sale_order_name": "S15433",
    "environment": "development"
  },
  "error": null,
  "completed_at": "2025-12-22T15:30:18.623456"
}
```

---

## 🚀 Despliegue

### Local (Desarrollo)

```bash
# 1. Clonar repo
git clone <repo>
cd services/mcp-odoo

# 2. Crear venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 3. Instalar deps
pip install -r requirements.txt

# 4. Configurar .env
cp .env.example .env
# Editar .env con tus credenciales

# 5. Ejecutar servidor
python server.py

# 6. Verificar
curl http://localhost:8000/health
```

### AWS App Runner (Producción)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copiar archivos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -f http://localhost:8000/health || exit 1

# Comando
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Variables de Entorno en App Runner:**
```
ODOO_URL=https://robotnik-dev.odoo.com
ODOO_DB=robotnik-dev
ODOO_USERNAME=tu_usuario
ODOO_PASSWORD=tu_password
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxx
AWS_REGION=us-east-1
S3_BUCKET=ilagentslogs
MCP_NAME=mcp-odoo-prod
```

**Health Check:**
- Path: `/health`
- Interval: 10s
- Timeout: 5s
- Healthy threshold: 2

---

## 📊 Configuración de Clientes

### Claude Desktop (Local)

`.vscode/mcp.json`:
```json
{
  "servers": {
    "mcp-local": {
      "url": "http://localhost:8000/mcp/sse",
      "type": "http"
    }
  },
  "inputs": []
}
```

### Claude Desktop (Remoto - Opcional)

```json
{
  "servers": {
    "mcp-prod": {
      "url": "https://gnenhisgbxhq2ppuwi7mtqsmfm.us-east-1.awsapprunner.com/mcp/sse",
      "type": "http"
    }
  }
}
```

### ElevenLabs

```python
# En configuración de ElevenLabs agent:

WEBHOOK_URL = "https://gnenhisgbxhq2ppuwi7mtqsmfm.us-east-1.awsapprunner.com/api/quotation/async"

# Cuando el usuario solicite cotización:
import requests

response = requests.post(
    WEBHOOK_URL,
    json={
        "partner_name": "Cliente desde ElevenLabs",
        "contact_name": "María González",
        "email": "maria@ejemplo.com",
        "phone": "+52 55 9876 5432",
        "lead_name": "Cotización voz AI",
        "product_id": 26174,
        "product_qty": 2
    }
)

tracking_id = response.json()["tracking_id"]

# Consultar estado después de 30 segundos
import time
time.sleep(30)

status_response = requests.get(
    f"{WEBHOOK_URL.replace('/async', '')}/status/{tracking_id}"
)

if status_response.json()["status"] == "completed":
    result = status_response.json()["result"]
    print(f"Cotización creada: {result['sale_order_name']}")
```

---

## 🎯 Ventajas de la Arquitectura Híbrida

### 1. **Simplicidad Operacional**
- ✅ Un solo proceso para mantener
- ✅ Un solo puerto (8000)
- ✅ Un solo Dockerfile
- ✅ Un solo deploy en AWS App Runner

### 2. **Eficiencia de Recursos**
- ✅ Código compartido (sin duplicación)
- ✅ Estado compartido (TaskManager in-memory)
- ✅ Logs centralizados (un solo flujo a S3)
- ✅ 50% menos recursos vs dos servidores separados

### 3. **Flexibilidad Total**
- ✅ Sirve a Claude Desktop via MCP
- ✅ Sirve a ElevenLabs via REST
- ✅ Puede servir a cualquier otro cliente HTTP
- ✅ Documentación automática (Swagger en `/docs`)

### 4. **Escalabilidad**
- ✅ Escala horizontalmente (N réplicas del mismo proceso)
- ✅ Load balancer distribuye automáticamente
- ✅ Sin necesidad de sincronizar estado entre procesos (in-memory)
- ✅ 33% mejor latencia vs arquitectura distribuida

### 5. **Mantenibilidad**
- ✅ Un solo codebase
- ✅ Una sola fuente de verdad
- ✅ Cambios afectan a ambos protocolos automáticamente
- ✅ Testing simplificado

---

## 📝 Comparación con Alternativas

| Criterio | Solo REST | Solo MCP | Dos Servidores | **Híbrido** |
|----------|-----------|----------|----------------|-------------|
| Claude Desktop | ❌ | ✅ | ✅ | ✅ |
| ElevenLabs | ✅ | ❌ | ✅ | ✅ |
| Mantenimiento | ✅ Fácil | ✅ Fácil | ❌ Complejo | ✅ Fácil |
| Un solo puerto | ✅ | ✅ | ❌ | ✅ |
| Código compartido | N/A | N/A | ❌ Duplicado | ✅ Compartido |
| Estado compartido | N/A | N/A | ❌ Separado | ✅ Compartido |
| Escalabilidad | ✅ | ✅ | ⚠️ Complejo | ✅ Simple |
| Despliegue | ✅ | ✅ | ❌ Complejo | ✅ Simple |
| Documentación | ✅ | ❌ | ⚠️ Dos docs | ✅ Unificada |
| **TOTAL** | 5/9 | 5/9 | 3/9 | **9/9** ✅ |

---

## 🔍 URLs de Producción

### Para ElevenLabs (Webhooks)

```
Base URL: https://gnenhisgbxhq2ppuwi7mtqsmfm.us-east-1.awsapprunner.com

✅ Crear cotización:
   POST /api/quotation/async

✅ Consultar estado:
   GET /api/quotation/status/{tracking_id}

✅ Health check:
   GET /health
```

**NOTA:** ElevenLabs usa REST, **NO** necesitas agregar `/mcp/sse`.

### Para Claude Desktop (Remoto - Opcional)

```
URL MCP (SSE):
https://gnenhisgbxhq2ppuwi7mtqsmfm.us-east-1.awsapprunner.com/mcp/sse
```

**NOTA:** Solo si quieres conectar Claude Desktop al servidor en la nube en lugar del local.

---

## 📚 Documentación Adicional

Para análisis detallado de las decisiones arquitectónicas, ver:
- `docs/ARQUITECTURA_HIBRIDA_ANALISIS.md` - Análisis completo de alternativas

---

## 🏁 Conclusión

Esta arquitectura híbrida representa la **mejor solución** para el caso de uso actual:

✅ **Único servidor** → Simplicidad operacional  
✅ **Dos protocolos** → Flexibilidad total  
✅ **FastAPI base** → Moderno, rápido, async nativo  
✅ **Código compartido** → Sin duplicación  
✅ **Estado compartido** → TaskManager in-memory  
✅ **Escalable** → Réplicas del mismo proceso  
✅ **Desplegable** → Un Dockerfile, un comando  

**Esta es la arquitectura óptima para servir tanto a Claude Desktop (MCP) como a ElevenLabs (REST) desde un solo servidor.** ✨
