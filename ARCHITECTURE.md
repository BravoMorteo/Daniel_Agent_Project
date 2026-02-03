# 🏗️ Arquitectura del Proyecto Daniel Agent

> 📖 **Documentación complementaria:**
> - [README.md](README.md) - Guía general del proyecto
> - [services/mcp-odoo/README_DETALLADO.md](services/mcp-odoo/README_DETALLADO.md) - Arquitectura detallada del servicio MCP-Odoo
> - [services/serverAvatar/README.md](services/serverAvatar/README.md) - Documentación del servicio ServerAvatar

---

## 📐 Visión General de la Arquitectura

Daniel Agent Project es un **sistema de IA conversacional con avatar virtual** que integra:
- 🤖 **Avatar IA animado** (HeyGen + LiveKit)
- 💬 **Conversación natural** (ElevenLabs ConvAI)
- 📊 **Integración ERP** (Odoo via MCP)
- 🌐 **Frontend moderno** (WebRTC + WebSocket)

**Arquitectura distribuida en 3 capas:** Presentación (Frontend), Aplicación (ServerAvatar), Integración Empresarial (MCP-Odoo).

## 🎯 Diagrama de Arquitectura Completa

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       CAPA 1: PRESENTACIÓN (Frontend)                      │
│                        Browser - JavaScript ES6+ Modules                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌──────────────┐ │
│  │   app.js    │   │audioHandler │   │videoHandler │   │  LiveKit     │ │
│  │ (orquesta)  │──►│ (micrófono) │   │  (canvas)   │   │  Handler     │ │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   └──────┬───────┘ │
│         │                  │                  │                  │         │
│         └──────────────────┴──────────────────┴──────────────────┘         │
│                                     │                                      │
│                            WebSocket + WebRTC                              │
│                                     │                                      │
└─────────────────────────────────────┼──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                  CAPA 2: APLICACIÓN (ServerAvatar)                         │
│                    Python 3.11+ - aiohttp ASGI Server                      │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                         server.py (main)                             │ │
│  │   • Inicialización app aiohttp                                       │ │
│  │   • Validación de configuración                                      │ │
│  │   • Registro de rutas HTTP + WebSocket                               │ │
│  └────────────────────────────┬─────────────────────────────────────────┘ │
│                               │                                            │
│    ┌──────────────────────────┼──────────────────────────┐                │
│    │                          │                          │                │
│  ┌─▼────────┐      ┌──────────▼────────┐      ┌────────▼─────────┐      │
│  │  core/   │      │    handlers/      │      │    services/     │      │
│  │          │      │                   │      │                  │      │
│  │ config   │◄─────┤ websocket_handler │─────►│ heygen_service   │      │
│  │          │      │ (orquestador)     │      │ elevenlabs_svc   │      │
│  └──────────┘      └───────────────────┘      └────────┬─────────┘      │
│                                                         │                 │
└─────────────────────────────────────────────────────────┼─────────────────┘
                                                          │
                                           API REST (HTTPS)
                                                          │
                        ┌─────────────────────────────────┼──────────┐
                        │                                 │          │
              ┌─────────▼──────────┐          ┌──────────▼────────────────┐
              │  HeyGen Streaming  │          │  ElevenLabs ConvAI        │
              │  • Avatar video    │          │  • Conversación IA        │
              │  • Sync labial     │          │  • TTS natural            │
              │  • LiveKit WebRTC  │          │  • MCP tool calling       │
              └────────────────────┘          └───────────┬───────────────┘
                                                          │
                                              MCP Protocol (SSE/HTTP)
                                                          │
                                                          ▼
┌────────────────────────────────────────────────────────────────────────────┐
│               CAPA 3: INTEGRACIÓN EMPRESARIAL (MCP-Odoo)                   │
│                  Python 3.11+ - FastAPI + FastMCP Server                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    server.py (FastMCP + FastAPI)                     │ │
│  │   • MCP Protocol handler (/mcp/*)                                    │ │
│  │   • REST API endpoints (/api/*)                                      │ │
│  │   • Auto-carga de herramientas MCP                                   │ │
│  │   • TaskManager para operaciones async                               │ │
│  └────────────────────────────┬─────────────────────────────────────────┘ │
│                               │                                            │
│    ┌──────────────────────────┼──────────────────────────┐                │
│    │                          │                          │                │
│  ┌─▼────────┐      ┌──────────▼────────┐      ┌────────▼─────────┐      │
│  │  core/   │      │     tools/        │      │    scripts/      │      │
│  │          │      │  (MCP Plugins)    │      │                  │      │
│  │ config   │      │                   │      │  • Dockerfile    │      │
│  │ odoo_    │◄─────┤ • crm.py          │      │  • Makefile      │      │
│  │ client   │      │ • sales.py        │      │  • build.sh      │      │
│  │ tasks    │      │ • projects.py     │      └──────────────────┘      │
│  │ logger   │      │ • tasks.py        │                                 │
│  │ whatsapp │      │ • users.py        │                                 │
│  │ api      │      │ • search.py       │                                 │
│  │ helpers  │      │ • whatsapp.py     │                                 │
│  └──────────┘      └───────────────────┘                                 │
│                                                                            │
└─────────────────────────────────────────────────────────┬──────────────────┘
                                                          │
                                           XML-RPC API (HTTPS)
                                                          │
                                    ┌─────────────────────▼───────────────┐
                                    │         Odoo ERP                    │
                                    │   • CRM (Leads, Oportunidades)      │
                                    │   • Ventas (Cotizaciones, Órdenes)  │
                                    │   • Proyectos y Tareas              │
                                    │   • Usuarios y Vendedores           │
                                    │   • Database PostgreSQL             │
                                    └─────────────────────────────────────┘

                    ┌──────────────────────────────────────────┐
                    │         AWS S3 (Opcional)                │
                    │   • Logs JSON de cotizaciones            │
                    │   • Tracking de operaciones              │
                    │   • Bucket: ilagentslogs                 │
                    └──────────────────────────────────────────┘
```

## 🎯 Arquitectura por Capas

### 1️⃣ Capa de Presentación (Frontend)

**Responsabilidad:** Interfaz de usuario y experiencia del usuario

**Tecnologías:**
- HTML5, CSS3, JavaScript (ES6+)
- WebRTC / LiveKit (streaming video)
- WebSocket (comunicación bidireccional)
- Canvas API (rendering de video)

**Componentes:**
- `app.js` - Orquestador principal de la aplicación
- `config.js` - Configuración centralizada
- `audioHandler.js` - Captura y procesamiento de audio
- `videoHandler.js` - Rendering y control de video
- `websocketHandler.js` - Comunicación con servidor
- `livekitHandler.js` - Integración LiveKit/WebRTC
- `utils.js` - Funciones de utilidad

**Flujo:**
```
Usuario habla → audioHandler captura → 
websocketHandler envía → ServerAvatar procesa →
websocketHandler recibe → videoHandler muestra avatar
```

**Patrones aplicados:**
- Module Pattern (ES6 modules)
- Observer Pattern (eventos de audio/video)
- Facade Pattern (simplificación de APIs)

---

### 2️⃣ Capa de Aplicación (ServerAvatar)

**Responsabilidad:** Orquestación de servicios de IA y avatar

**Tecnologías:**
- Python 3.11+
- aiohttp (servidor ASGI asíncrono)
- WebSocket (protocolo bidireccional)
- python-dotenv (gestión de configuración)

**Arquitectura Modular:**

#### `server.py` - Punto de Entrada
```python
app = create_app()
- Validar configuración
- Registrar rutas HTTP y WebSocket
- Inicializar servicios
```

#### `core/config.py` - Configuración
```python
class Config:
    - Cargar variables de entorno
    - Validar configuración requerida
    - Exponer constantes
```

#### `handlers/` - Manejadores de Request
```python
http_handlers.py
    - Servir páginas HTML estáticas
    
websocket_handler.py
    - Orquestar flujo de conversación
    - Coordinar HeyGen + ElevenLabs
    - Gestionar ciclo de vida de sesión
```

#### `services/` - Integraciones Externas
```python
heygen_service.py
    - Crear sesión de avatar
    - Enviar texto para animación
    - Gestionar streaming LiveKit
    
elevenlabs_service.py
    - Conectar con ConvAI
    - Relay de conversación
    - Procesar respuestas IA
```

#### `utils/` - Utilidades
```python
Logger
    - Logging consistente
    - Emojis para categorización
    - Múltiples niveles (info, warn, error)
```

**Flujo de Datos:**
```
Frontend (WS)
    ↓
websocket_handler
    ↓ (orquesta)
    ├→ heygen_service → HeyGen API → LiveKit
    └→ elevenlabs_service → ElevenLabs API
```

**Patrones aplicados:**
- Service Layer Pattern
- Handler Pattern
- Facade Pattern
- Dependency Injection (services inyectados en handlers)
- Singleton Pattern (Config)

---

### 3️⃣ Capa de Integración Empresarial (MCP-Odoo)

**Responsabilidad:** Exposición de funcionalidades ERP via protocolo híbrido MCP + REST API

**Tecnologías:**
- Python 3.11+
- FastMCP 0.2.14+ (protocolo MCP para LLMs)
- FastAPI 0.115+ (REST API para web apps)
- Uvicorn 0.30+ (servidor ASGI)
- Boto3 1.34+ (logs S3)
- Twilio 9.0+ (WhatsApp)
- XML-RPC (protocolo Odoo)

**Arquitectura Híbrida - Dos Protocolos en Un Servidor:**

#### `server.py` - Servidor Híbrido MCP + FastAPI
```python
# Protocolo MCP para LLMs (Claude, GPT)
mcp = FastMCP("mcp-odoo")
mcp_app_wrapper = mcp.get_asgi_app()

# REST API para aplicaciones web
app = FastAPI()
app.mount("/mcp", mcp_app_wrapper)  # MCP en /mcp/*
# Endpoints REST en /api/*

# Inicialización
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_tools_once()  # Lazy load de tools
    yield

# Un solo servidor, dos protocolos:
# - LLMs usan /mcp/sse (MCP Protocol)
# - Web Apps usan /api/* (REST JSON)
```

#### `core/config.py` - Configuración Dual
```python
class Config:
    # Odoo Producción (solo lectura)
    ODOO_URL, ODOO_DB, ODOO_LOGIN, ODOO_API_KEY
    
    # Odoo Desarrollo (escritura)
    DEV_ODOO_URL, DEV_ODOO_DB, DEV_ODOO_LOGIN, DEV_ODOO_API_KEY
    
    # AWS S3 (logging)
    S3_LOGS_BUCKET, AWS_REGION
    
    # Twilio WhatsApp
    TWILIO_*, VENDEDOR_WHATSAPP
```

#### `core/odoo_client.py` - Cliente XML-RPC
```python
class OdooClient:
    - authenticate() → Conexión Odoo
    - search(model, domain, limit)
    - search_read(model, domain, fields)
    - read(model, ids, fields)
    - create(model, values)
    - write(model, ids, values)
    - unlink(model, ids)
```

#### `core/api.py` - Modelos Pydantic REST
```python
CreateQuotationRequest
    - partner_name, contact_name, email, phone
    - lead_name, product_id, product_qty
    - Validación automática

QuotationStatusResponse
    - tracking_id, status (queued/processing/completed/failed)
    - output (sale_order_id, lead_id, etc)
```

#### `core/tasks.py` - TaskManager Async
```python
class TaskManager:
    - create_task() → tracking_id
    - get_status(tracking_id) → status + output
    - Background execution con asyncio
    - Estado en memoria (puede migrar a Redis)
```

#### `core/logger.py` - Logging con S3
```python
- log_local() → JSON a /tmp/mcp_odoo_logs/
- upload_to_s3() → Subida automática
- Estructura: tracking_id, timestamp, status, input, output
```

#### `core/whatsapp.py` - Cliente Twilio
```python
- send_handoff_notification()
- Asigna vendedor con menos leads (balanceo)
- Envía SMS WhatsApp con contexto
```

#### `core/helpers.py` - Utilidades MCP
```python
- encode_content() → Formato MCP estándar
- odoo_form_url() → URLs formularios Odoo
- Helpers de formateo
```

#### `tools/` - Herramientas MCP (Plugin System)
```python
crm.py          → dev_create_quotation (async)
sales.py        → dev_create_sale, dev_create_sale_line, get_sale
projects.py     → list_projects, fetch (full doc)
tasks.py        → list_tasks, get_task
users.py        → list_users
search.py       → mcp_search (projects + tasks)
whatsapp.py     → message_notification (handoff)
```

**Autoload de Tools:**
```python
# tools/__init__.py - Carga automática
async def init_tools_once():
    for file in Path(__file__).parent.glob("*.py"):
        if file.stem not in ["__init__"]:
            module = import_module(f"tools.{file.stem}")
            if hasattr(module, 'register'):
                await module.register(mcp, deps)
```

**Flujo MCP (LLM → Odoo):**
```
Claude Desktop
    ↓ (MCP Protocol via SSE)
server.py (/mcp/sse)
    ↓
tools/crm.py (dev_create_quotation)
    ↓
core/odoo_client.py (XML-RPC)
    ↓
Odoo ERP (crear lead + orden)
    ↓
Retorna S12345 → Claude
```

**Flujo REST (Web App → Odoo):**
```
Frontend JavaScript
    ↓ (POST /api/quotation/async)
server.py (FastAPI endpoint)
    ↓
core/tasks.py (TaskManager)
    ↓ (background async)
tools/crm.py (lógica reutilizada)
    ↓
core/odoo_client.py (XML-RPC)
    ↓
core/logger.py → S3
    ↓
Frontend consulta: GET /api/quotation/status/{tracking_id}
```

**Patrones aplicados:**
- Hybrid Protocol Pattern (MCP + REST en un servidor)
- Plugin Pattern (tools autoload)
- Repository Pattern (OdooClient)
- Facade Pattern (helpers)
- Async Task Pattern (TaskManager)
- Lazy Loading (tools cargados en lifespan)
- Dependency Injection (deps dict)
- Observer Pattern (task status tracking)

> 📖 **Documentación completa**: Ver [services/mcp-odoo/README_DETALLADO.md](services/mcp-odoo/README_DETALLADO.md)

---

### 4️⃣ Capa de Recursos (Resources)

**Responsabilidad:** Configuración y datos compartidos

**Contenido actualizado:**
```
resources/
├── elevenLabs/
│   └── prompt.txt      # Prompt del agente conversacional IA
└── odoo/
    └── data.py         # Datos de configuración y análisis Odoo
```

**Propósito:**
- `prompt.txt` → Personalidad y comportamiento del avatar IA
- `data.py` → Configuración de ambientes Odoo, mapeos de productos
- Datos centralizados y versionados

---

## 🔄 Flujos de Datos Principales

### Flujo 1: Conversación con Avatar

```
1. Usuario habla al micrófono
   ↓
2. Frontend captura audio (audioHandler)
   ↓
3. WebSocket envía audio a ServerAvatar
   ↓
4. WebSocketHandler coordina:
   a) Envía audio a ElevenLabs ConvAI
   b) ElevenLabs procesa y genera respuesta (texto)
   c) Texto se envía a HeyGen para animación
   ↓
5. HeyGen genera video con avatar animado
   ↓
6. Video se transmite via LiveKit/WebRTC
   ↓
7. Frontend muestra video en canvas
```

### Flujo 2: Consulta a Odoo via MCP

```
1. Usuario pregunta: "¿Qué proyectos tengo activos?"
   ↓
2. ElevenLabs ConvAI detecta intención → Necesita datos Odoo
   ↓
3. ConvAI invoca tool MCP: list_projects(active=True)
   ↓ (MCP Protocol via SSE)
4. MCP-Odoo server recibe request en /mcp/sse
   ↓
5. Router ejecuta tools/projects.py → list_projects()
   ↓
6. OdooClient realiza XML-RPC: search_read('project.project', ...)
   ↓
7. Odoo ERP devuelve lista de proyectos [{id, name, ...}, ...]
   ↓
8. Helper formatea en MCP content format
   ↓
9. Respuesta MCP retorna a ElevenLabs ConvAI
   ↓
10. ConvAI genera texto natural: "Tienes 3 proyectos activos: ..."
    ↓
11. Texto se envía a HeyGen para animar avatar
    ↓
12. Usuario ve y escucha respuesta con datos reales de Odoo
```

### Flujo 3: Crear Cotización desde Web App (REST API)

```
1. Frontend envía POST /api/quotation/async
   Body: {partner_name, email, phone, product_id, ...}
   ↓
2. FastAPI valida con Pydantic (CreateQuotationRequest)
   ↓
3. TaskManager crea tarea async → tracking_id
   ↓
4. Respuesta inmediata: {tracking_id: "quot_abc123", status: "queued"}
   ↓
5. Frontend comienza polling: GET /api/quotation/status/quot_abc123
   ↓
6. Background task ejecuta:
   a) Buscar/crear partner en Odoo
   b) Asignar vendedor (balanceo de carga)
   c) Crear lead en CRM
   d) Convertir a oportunidad
   e) Crear cotización (sale.order)
   f) Agregar líneas de productos
   ↓
7. Logger guarda JSON local + sube a S3
   ↓
8. Task completa, status → "completed"
   ↓
9. Frontend obtiene resultado: {status: "completed", output: {sale_order_id, ...}}
   ↓
10. Frontend muestra: "Cotización S12345 creada exitosamente"
```

### Flujo 4: Handoff a Vendedor Humano (Webhook)

```
1. ElevenLabs ConvAI detecta: "Quiero hablar con un vendedor"
   ↓
2. ConvAI invoca tool: message_notification(user_phone, reason)
   ↓
3. MCP-Odoo procesa en tools/whatsapp.py
   ↓
4. Si hay lead_id o sale_order_id → busca vendedor asignado
   Si no → asigna vendedor con menos leads (balanceo)
   ↓
5. Obtiene teléfono del vendedor de Odoo (res.users → mobile)
   ↓
6. Twilio Client envía WhatsApp:
   "🔔 Cliente +521234567890 solicita atención
    Motivo: Dudas sobre cotización
    Conversación ID: conv_xyz"
   ↓
7. Vendedor recibe notificación en WhatsApp
   ↓
8. Vendedor contacta al cliente directamente
```

### Flujo 5: Inicialización del Sistema

```
1. Iniciar MCP-Odoo Server (puerto 8000)
   ├→ Cargar core/config.py
   ├→ Validar variables de entorno (Odoo, S3, Twilio)
   ├→ Conectar a Odoo via XML-RPC (autenticación)
   ├→ Inicializar FastAPI app + FastMCP wrapper
   ├→ Lazy init tools (en primer request o lifespan)
   ├→ Health check: GET /health → {"ok": true}
   └→ Escuchar en 0.0.0.0:8000
      • MCP Protocol: /mcp/sse
      • REST API: /api/*
      • Docs: /docs (Swagger UI)

2. Iniciar ServerAvatar (puerto 8080)
   ├→ Cargar core/config.py
   ├→ Validar API keys (HeyGen, ElevenLabs)
   ├→ Inicializar aiohttp Application
   ├→ Registrar handlers:
   │   • HTTP: index.html, assets
   │   • WebSocket: /ws (conversación)
   ├→ Inicializar servicios (lazy):
   │   • HeyGenService
   │   • ElevenLabsService
   └→ Escuchar en 0.0.0.0:8080

3. Abrir Frontend (Browser)
   ├→ Cargar index_livekit.html o index_public.html
   ├→ Importar módulos ES6:
   │   • app.js → config, utils, handlers
   ├→ Conectar WebSocket a ws://localhost:8080/ws
   ├→ Solicitar permisos de micrófono
   ├→ Inicializar LiveKit Client (para WebRTC)
   ├→ Mostrar UI: "Ready to start conversation"
   └→ Esperar interacción del usuario
```

## 📊 Dependencias entre Componentes

### Dependencias Frontend
```
app.js
  ├→ config.js
  ├→ utils.js
  ├→ audioHandler.js
  ├→ videoHandler.js
  ├→ websocketHandler.js
  └→ livekitHandler.js
```

### Dependencias ServerAvatar
```
server.py
  ├→ core/config.py
  └→ handlers/
      ├→ http_handlers.py
      └→ websocket_handler.py
          ├→ services/heygen_service.py
          │   └→ core/config.py, utils/
          └→ services/elevenlabs_service.py
              └→ core/config.py, utils/
```

### Dependencias MCP-Odoo
```
server.py (FastMCP + FastAPI)
  ├→ core/config.py (env vars)
  ├→ core/api.py (Pydantic models)
  ├→ core/tasks.py (TaskManager)
  └→ tools/ (lazy init en lifespan)
      ├→ __init__.py (auto-discovery)
      ├→ crm.py ──────┐
      ├→ sales.py ────┤
      ├→ projects.py ─┤
      ├→ tasks.py ────┤
      ├→ users.py ────┼→ core/odoo_client.py (XML-RPC)
      ├→ search.py ───┤   core/helpers.py (formateo MCP)
      └→ whatsapp.py ─┘   core/logger.py (S3 logs)
                          core/whatsapp.py (Twilio)
                          core/config.py
```

## 🔒 Seguridad

### Gestión de Secretos
- **Todas las API keys en `.env`** (nunca en código)
- **Archivos `.env` en `.gitignore`** (no se versionan)
- **No hay secrets hardcoded** en ningún archivo
- **Validación al inicio**: falla si faltan vars críticas
- **Logging seguro**: no expone API keys en logs

### Validación
- **Pydantic models** validan requests REST (tipo, formato, campos)
- **Error handling** en todas las API calls externas
- **Timeouts** configurados en requests HTTP
- **Logging de errores** sin exponer información sensible

### Comunicación Segura
- **WebSocket** sobre HTTP/HTTPS según entorno
- **LiveKit** con autenticación token-based
- **XML-RPC sobre HTTPS** (Odoo cloud)
- **API keys en headers** Authorization (no en URLs)
- **Twilio** con Account SID + Auth Token seguros

### Ambientes Separados
- **Odoo Producción** (ODOO_*): solo lectura, consultas
- **Odoo Desarrollo** (DEV_ODOO_*): escritura, testing
- Previene modificaciones accidentales en producción

---

## ⚡ Performance y Escalabilidad

### Optimizaciones Actuales
- ✅ **Async/await en Python** (aiohttp, FastAPI) - operaciones no bloqueantes
- ✅ **Lazy loading de tools MCP** - cargan solo cuando se necesitan
- ✅ **WebSocket** para comunicación bidireccional eficiente
- ✅ **WebRTC/LiveKit** para streaming de video optimizado
- ✅ **Caching de configuración** en memoria (Config singleton)
- ✅ **TaskManager async** - cotizaciones en background sin bloquear
- ✅ **Logs async a S3** - no bloquea operaciones principales

### Métricas Actuales
- **Latencia WebSocket**: ~50-100ms
- **Tiempo creación cotización**: 3-5 segundos (async)
- **Tamaño logs JSON**: ~2-5KB por operación
- **Concurrencia**: ~10-20 requests simultáneos (single instance)

### Escalabilidad Futura (Roadmap)

**Corto Plazo:**
- [ ] **Connection pooling Odoo** - reutilizar conexiones XML-RPC
- [ ] **Redis para TaskManager** - estado persistente y compartido
- [ ] **Rate limiting** - proteger APIs de sobrecarga
- [ ] **Health checks avanzados** - monitoreo de dependencias

**Mediano Plazo:**
- [ ] **Load balancer** (Nginx/HAProxy) - múltiples instancias ServerAvatar
- [ ] **Horizontal scaling** - múltiples workers MCP-Odoo
- [ ] **Message queue** (RabbitMQ/SQS) - desacoplar procesamiento
- [ ] **CDN** para assets estáticos del frontend

**Largo Plazo:**
- [ ] **Kubernetes deployment** - orquestación de containers
- [ ] **Database caching** (Redis) - reducir calls a Odoo
- [ ] **Microservices split** - separar concerns por servicio
- [ ] **Multi-region deployment** - latencia global reducida

---

## 🧪 Testing Strategy

### Estructura de Testing Actual

**Niveles Implementados:**
```
Manual Testing (Actual)
  ├→ Health checks (/health endpoints)
  ├→ Swagger UI testing (/docs en MCP-Odoo)
  ├→ Frontend integration testing (navegador)
  └→ Odoo connection testing (XML-RPC)
```

### Niveles de Testing Recomendados

**Unit Tests (Pendiente):**
```python
# tests/unit/
test_config.py
  - test_load_env_vars()
  - test_validation_missing_vars()
  - test_odoo_url_format()

test_odoo_client.py (con mocks)
  - test_authenticate()
  - test_search_with_domain()
  - test_create_record()
  - Mock XML-RPC calls

test_services.py (con mocks)
  - test_heygen_session_creation()
  - test_elevenlabs_connection()
  - Mock API responses
```

**Integration Tests:**
```python
# tests/integration/
test_websocket_handler.py
  - test_websocket_connection()
  - test_message_relay()
  - test_session_lifecycle()

test_mcp_tools.py (con Odoo dev)
  - test_list_projects()
  - test_create_quotation()
  - test_search_functionality()
  - Usar ambiente DEV_ODOO_*
```

**End-to-End Tests:**
```python
# tests/e2e/
test_full_conversation_flow.py
  - Usuario habla → Avatar responde
  - Consulta Odoo → Respuesta correcta
  - Crear cotización → Verificar en Odoo

test_rest_api_flow.py
  - POST /api/quotation/async
  - GET /api/quotation/status/{id}
  - Verificar log en S3
```

### Comandos de Testing

```bash
# Unit tests (rápidos, sin deps externas)
pytest tests/unit/ -v

# Integration tests (requiere Odoo dev)
pytest tests/integration/ -v --odoo-env=dev

# E2E tests (requiere todo el stack)
pytest tests/e2e/ -v --slow

# Coverage report
pytest --cov=services --cov-report=html
```

### Testing en CI/CD (Pendiente)

```yaml
# .github/workflows/test.yml
- Unit tests en cada push
- Integration tests en PRs
- E2E tests antes de deploy
- Coverage report automático
```

---

## 📈 Métricas y Monitoring

### Métricas Clave a Monitorear

**Performance:**
- ⏱️ Latencia WebSocket (objetivo: <100ms)
- 🚀 Tiempo respuesta APIs externas (HeyGen, ElevenLabs, Odoo)
- 📊 Tiempo creación cotización async (objetivo: <5s)
- 💾 Uso memoria/CPU por servicio

**Disponibilidad:**
- ✅ Tasa éxito/error por endpoint
- 🔌 Conexiones WebSocket activas
- 🔄 Health check status (cada 30s)
- 📡 Uptime por servicio

**Negocio:**
- 💼 Cotizaciones creadas por hora/día
- 📞 Handoffs a vendedores (conversiones)
- 👥 Sesiones de conversación activas
- 📝 Logs generados y subidos a S3

### Logging Actual

**Sistema de Logs Implementado:**
```python
# ServerAvatar - utils/logger.py
Logger.info("✅ WebSocket connection established")
Logger.warn("⚠️ API key missing, using default")
Logger.error("❌ Failed to connect to HeyGen API")

# MCP-Odoo - core/logger.py
- JSON estructurado por operación
- Local: /tmp/mcp_odoo_logs/YYYY-MM-DD_tracking_id.log
- S3: s3://ilagentslogs/mcp-odoo-logs/YYYY/MM/
```

**Formato Log JSON:**
```json
{
  "tracking_id": "quot_abc123",
  "timestamp": "2026-01-30T10:15:30.123456",
  "status": "completed",
  "input": {...},
  "output": {
    "sale_order_id": 12345,
    "sale_order_name": "S12345"
  },
  "error": null,
  "duration_seconds": 4.5
}
```

### Monitoring Futuro (Recomendado)

**Stack Sugerido:**
```
Prometheus + Grafana
  ├→ Métricas de sistema (CPU, RAM, network)
  ├→ Métricas custom (cotizaciones/hora)
  ├→ Dashboards visuales
  └→ Alertas configurables

ELK Stack (Elasticsearch, Logstash, Kibana)
  ├→ Logs centralizados
  ├→ Búsqueda full-text
  ├→ Análisis de patrones
  └→ Visualización de errores

Sentry
  ├→ Error tracking
  ├→ Stack traces
  ├→ Alertas tiempo real
  └→ Performance monitoring
```

**Alertas Críticas:**
- 🚨 Error rate > 5% en 5 minutos → Slack/Email
- 🚨 Health check fail 3 veces consecutivas → PagerDuty
- 🚨 Latencia > 500ms sostenida → Warning
- 🚨 Memoria > 90% → Scale up automático

---

## 🔮 Evolución Futura del Proyecto

### Fase 1: Fundación (Completada) ✅

**Q4 2025 - Enero 2026**
- [x] Avatar IA funcional con HeyGen + LiveKit
- [x] Conversación natural con ElevenLabs ConvAI
- [x] Integración Odoo via MCP + REST API híbrido
- [x] Frontend modular con WebSocket + WebRTC
- [x] Sistema de logging con S3
- [x] Handoff automático a vendedores (WhatsApp)
- [x] Documentación completa del proyecto

**Logros:**
- ✅ Arquitectura de 3 capas bien definida
- ✅ Protocolo híbrido MCP + FastAPI funcionando
- ✅ Cotizaciones asíncronas con tracking
- ✅ Deployment con Docker

---

### Fase 2: Estabilización (Corto Plazo)

**Febrero - Abril 2026**

**Testing y Calidad:**
- [ ] Suite completa de tests (unit, integration, e2e)
- [ ] Coverage > 80% en código crítico
- [ ] CI/CD pipeline con GitHub Actions
- [ ] Pre-commit hooks (linting, formatting)

**DevOps:**
- [ ] Docker Compose completo (3 servicios + Nginx)
- [ ] Monitoring con Prometheus + Grafana
- [ ] Alertas automáticas (Slack/Email)
- [ ] Backup automático de logs S3

**Performance:**
- [ ] Redis para TaskManager (estado persistente)
- [ ] Connection pooling Odoo
- [ ] Rate limiting en APIs
- [ ] Optimización de queries Odoo

**Documentación:**
- [ ] Video tutorials (setup, uso, troubleshooting)
- [ ] API documentation interactiva (Swagger mejorado)
- [ ] Runbooks de operación
- [ ] Postman collections

---

### Fase 3: Expansión (Mediano Plazo)

**Mayo - Septiembre 2026**

**Features Nuevos:**
- [ ] **Multi-idioma** (ES, EN, PT)
  - Prompts dinámicos por idioma
  - TTS en múltiples idiomas
  - UI traducida

- [ ] **Dashboard Administrativo**
  - Estadísticas de conversaciones
  - Métricas de cotizaciones
  - Gestión de configuración
  - Visualización de logs

- [ ] **Analytics Avanzado**
  - Reportes de uso
  - Funnels de conversión
  - Análisis de sentimiento
  - KPIs de negocio

- [ ] **Autenticación y Permisos**
  - Login de usuarios
  - Roles (admin, vendedor, usuario)
  - Multi-tenancy básico
  - Sesiones seguras (JWT)

**Integraciones:**
- [ ] Slack notifications
- [ ] Zapier/Make integration
- [ ] Calendar scheduling (Calendly)
- [ ] Payment processing (Stripe)

---

### Fase 4: Escalamiento (Largo Plazo)

**Q4 2026 - 2027**

**Microservicios:**
- [ ] Separar MCP-Odoo en múltiples servicios:
  - CRM Service (leads, oportunidades)
  - Sales Service (cotizaciones, órdenes)
  - Notification Service (WhatsApp, Email, SMS)
  - Analytics Service (reporting, BI)

**Arquitectura Cloud-Native:**
- [ ] **Kubernetes deployment**
  - Auto-scaling horizontal
  - Load balancing automático
  - Self-healing containers
  - Rolling updates

- [ ] **Message Queue**
  - RabbitMQ/AWS SQS para eventos
  - Event-driven architecture
  - Desacoplamiento de servicios

- [ ] **Multi-Region**
  - Deploy en múltiples regiones AWS/GCP
  - CDN global (CloudFlare)
  - Latencia < 100ms worldwide

**IA Personalizada:**
- [ ] Fine-tuning de modelos por cliente
- [ ] Memoria conversacional (RAG)
- [ ] Predicción de intenciones
- [ ] Recomendaciones inteligentes

**Escalabilidad Masiva:**
- [ ] Soporte para 1000+ usuarios concurrentes
- [ ] Database sharding (PostgreSQL)
- [ ] Caching distribuido (Redis Cluster)
- [ ] Queue workers escalables

---

### Fase 5: Innovación (Visión 2027+)

**Características Futuristas:**
- [ ] **Avatares 3D Personalizados**
  - Crear avatar basado en foto del vendedor
  - Customización de apariencia
  - Gestos y expresiones avanzadas

- [ ] **Voice Cloning**
  - Voz del vendedor real clonada
  - Personalidad consistente
  - Emociones auténticas

- [ ] **AR/VR Integration**
  - Avatar en realidad aumentada
  - Experiencia inmersiva
  - Demos de productos en 3D

- [ ] **Omnichannel**
  - WhatsApp Business API
  - Instagram/Facebook Messenger
  - Telegram, SMS, Email
  - Unified inbox

- [ ] **AI-Powered Insights**
  - Predicción de cierre de ventas
  - Análisis de conversaciones (NLP)
  - Alertas proactivas
  - Coaching automático para vendedores

---

---

## 📚 Referencias Técnicas y Recursos

### Documentación de APIs Externas

**HeyGen (Avatar Streaming):**
- 🔗 Official Docs: https://docs.heygen.com/
- 📖 Streaming Avatar API: https://docs.heygen.com/reference/create-streaming-avatar
- 💡 LiveKit Integration: https://docs.heygen.com/docs/livekit-setup
- 🎥 Video Tutorials: https://www.heygen.com/resources

**ElevenLabs (Conversational AI):**
- 🔗 Official Docs: https://elevenlabs.io/docs/
- 📖 Conversational AI: https://elevenlabs.io/docs/conversational-ai
- 🎙️ Text-to-Speech: https://elevenlabs.io/docs/api-reference/text-to-speech
- 🔧 WebSocket API: https://elevenlabs.io/docs/api-reference/websockets

**LiveKit (WebRTC):**
- 🔗 Official Docs: https://docs.livekit.io/
- 📖 JavaScript SDK: https://docs.livekit.io/client-sdks/javascript/
- 🌐 Server API: https://docs.livekit.io/server/api/
- 🎥 Streaming: https://docs.livekit.io/guides/publish-stream/

**Odoo (ERP):**
- 🔗 Official Docs: https://www.odoo.com/documentation/17.0/
- 📖 External API (XML-RPC): https://www.odoo.com/documentation/17.0/developer/reference/external_api.html
- 🔧 Web Services: https://www.odoo.com/documentation/17.0/developer/reference/backend/web_services.html
- 💾 ORM API: https://www.odoo.com/documentation/17.0/developer/reference/backend/orm.html

### Frameworks y Librerías Python

**FastAPI:**
- 🔗 Docs: https://fastapi.tiangolo.com/
- 📖 Tutorial: https://fastapi.tiangolo.com/tutorial/
- 🚀 Deployment: https://fastapi.tiangolo.com/deployment/

**FastMCP:**
- 🔗 GitHub: https://github.com/jlowin/fastmcp
- 📖 MCP Protocol: https://modelcontextprotocol.io/
- 💡 Examples: https://github.com/modelcontextprotocol/servers

**aiohttp:**
- 🔗 Docs: https://docs.aiohttp.org/
- 📖 Server Tutorial: https://docs.aiohttp.org/en/stable/web.html
- 🔌 WebSocket: https://docs.aiohttp.org/en/stable/web_quickstart.html#websockets

**Pydantic:**
- 🔗 Docs: https://docs.pydantic.dev/
- 📖 Models: https://docs.pydantic.dev/latest/concepts/models/
- ✅ Validation: https://docs.pydantic.dev/latest/concepts/validation/

### Frontend Technologies

**WebRTC:**
- 🔗 MDN Web Docs: https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API
- 📖 Getting Started: https://webrtc.org/getting-started/overview
- 💡 Samples: https://webrtc.github.io/samples/

**WebSocket:**
- 🔗 MDN Web Docs: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- 📖 Protocol Spec: https://datatracker.ietf.org/doc/html/rfc6455
- 💡 Examples: https://javascript.info/websocket

**ES6 Modules:**
- 🔗 MDN Web Docs: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules
- 📖 Import/Export: https://javascript.info/modules-intro

### DevOps y Deployment

**Docker:**
- 🔗 Docs: https://docs.docker.com/
- 📖 Best Practices: https://docs.docker.com/develop/dev-best-practices/
- 🐳 Compose: https://docs.docker.com/compose/

**AWS S3:**
- 🔗 Docs: https://docs.aws.amazon.com/s3/
- 📖 Boto3 (Python SDK): https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- 💾 Best Practices: https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html

**Twilio:**
- 🔗 Docs: https://www.twilio.com/docs
- 📱 WhatsApp API: https://www.twilio.com/docs/whatsapp
- 🐍 Python SDK: https://www.twilio.com/docs/libraries/python

### Recursos de Aprendizaje

**Arquitectura de Software:**
- 📚 Clean Architecture (Robert C. Martin)
- 📚 Designing Data-Intensive Applications (Martin Kleppmann)
- 📚 Building Microservices (Sam Newman)

**Python Async:**
- 📖 Real Python - Async IO: https://realpython.com/async-io-python/
- 📖 Python Asyncio Docs: https://docs.python.org/3/library/asyncio.html

**WebRTC Development:**
- 📖 WebRTC for the Curious: https://webrtcforthecurious.com/
- 🎥 WebRTC Course: https://www.udemy.com/topic/webrtc/

---

## 🤝 Contribución al Proyecto

### Guía de Contribución

**Setup de Desarrollo:**
```bash
# 1. Clonar repo
git clone https://github.com/BravoMorteo/Daniel_Agent_Project.git
cd Daniel_Agent_Project

# 2. Crear rama de feature
git checkout -b feature/nueva-funcionalidad

# 3. Setup servicios
cd services/mcp-odoo && pip install -e . && cd ../..
cd services/serverAvatar && pip install -e . && cd ../..

# 4. Configurar .env (ver README.md)

# 5. Hacer cambios y commit
git add .
git commit -m "feat: descripción del cambio"

# 6. Push y crear PR
git push origin feature/nueva-funcionalidad
```

**Convenciones de Código:**
- Python: PEP 8 + type hints
- JavaScript: ESLint + ES6 modules
- Commits: Conventional Commits format
- Documentación: Markdown con emojis

**Proceso de Review:**
1. Tests pasan (cuando estén implementados)
2. Documentación actualizada
3. Sin errores de linting
4. Review de 1+ maintainer
5. Merge a `develop` → luego a `main`

---

## 📞 Contacto y Soporte

**Repositorio:**
- 🔗 GitHub: https://github.com/BravoMorteo/Daniel_Agent_Project

**Documentación:**
- 📖 README Principal: [README.md](README.md)
- 📖 MCP-Odoo Detallado: [services/mcp-odoo/README_DETALLADO.md](services/mcp-odoo/README_DETALLADO.md)
- 📖 ServerAvatar: [services/serverAvatar/README.md](services/serverAvatar/README.md)

**Issues y Bugs:**
- 🐛 Reportar issue: GitHub Issues
- 💡 Sugerencias: GitHub Discussions
- 🔧 Troubleshooting: Ver sección "Problemas Comunes" en READMEs

---

**Última actualización:** 30 de enero de 2026  
**Versión:** 3.0  
**Estado:** ✅ Producción Activa  
**Autor:** BravoMorteo / Daniel Agent Project Team

---

## 🎯 Resumen Ejecutivo

**Daniel Agent Project** es una solución completa de IA conversacional que combina:
- 🤖 Avatar virtual animado con sincronización labial
- 💬 Conversación natural potenciada por IA
- 📊 Integración profunda con Odoo ERP
- 🔄 Arquitectura moderna asíncrona y escalable

**Valor de negocio:**
- ⏰ Atención 24/7 sin intervención humana
- 📈 Automatización de cotizaciones (3-5 segundos)
- 🎯 Handoff inteligente a vendedores cuando necesario
- 📊 Datos centralizados y auditables (S3 logs)

**Stack tecnológico:**
- Frontend: JavaScript ES6, WebRTC, WebSocket
- Backend: Python 3.11+, FastAPI, aiohttp
- Integraciones: HeyGen, ElevenLabs, Odoo, AWS S3, Twilio
- Protocolos: MCP, REST, XML-RPC, WebSocket, WebRTC

**Estado actual:**
- ✅ Sistema funcional en producción
- ✅ Documentación completa
- ✅ Deployment con Docker
- 🚀 Roadmap ambicioso para 2026-2027
