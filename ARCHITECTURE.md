# 🏗️ Arquitectura del Proyecto Daniel Agent

Documentación completa de la arquitectura del sistema de IA conversacional con avatar e integración ERP.

## 📐 Visión General de la Arquitectura

Daniel Agent Project es un sistema multi-capa distribuido que integra tecnologías de IA conversacional, avatares virtuales y sistemas empresariales ERP en una solución cohesiva.

## 🎯 Diagrama de Arquitectura Completa

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            CAPA DE PRESENTACIÓN                            │
│                          (Frontend - Navegador Web)                        │
│                                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  UI Handler  │  │ Audio Handler│  │ Video Handler│  │ WS Handler   │ │
│  │  (app.js)    │  │ (micrófono)  │  │ (canvas)     │  │ (WebSocket)  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │                  │         │
│         └──────────────────┴──────────────────┴──────────────────┘         │
│                                     │                                      │
└─────────────────────────────────────┼──────────────────────────────────────┘
                                      │
                     HTTP/WebSocket   │   WebRTC/LiveKit
                                      │
┌─────────────────────────────────────┼──────────────────────────────────────┐
│                        CAPA DE APLICACIÓN                                  │
│                     (ServerAvatar - Python/aiohttp)                        │
│                                     │                                      │
│  ┌──────────────────────────────────┼──────────────────────────────────┐  │
│  │                           server.py (Main)                           │  │
│  │  • Inicialización ASGI                                               │  │
│  │  • Validación de configuración                                       │  │
│  │  • Registro de rutas HTTP/WS                                         │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                      │
│         ┌───────────────────────────┼───────────────────────────┐          │
│         │                           │                           │          │
│  ┌──────▼──────┐           ┌────────▼────────┐         ┌───────▼────────┐ │
│  │   CORE/     │           │   HANDLERS/     │         │   SERVICES/    │ │
│  │             │           │                 │         │                │ │
│  │ • config.py │           │ • http_handler  │         │ • heygen_svc   │ │
│  │   (Config)  │◄──────────│ • websocket_    │────────►│ • elevenlabs_  │ │
│  │             │           │   handler       │         │   service      │ │
│  │             │           │   (orquesta)    │         │                │ │
│  └─────────────┘           └─────────────────┘         └────────┬───────┘ │
│                                                                  │         │
└──────────────────────────────────────────────────────────────────┼─────────┘
                                                                   │
                                     API Calls                     │
                         ┌────────────────┴────────────────┐       │
                         │                                 │       │
         ┌───────────────▼──────────────┐   ┌──────────────▼───────▼─────────┐
         │   HeyGen Streaming Avatar    │   │   ElevenLabs ConvAI            │
         │   • Genera video de avatar   │   │   • Procesa conversación       │
         │   • Sincronización labial    │   │   • Genera respuestas IA       │
         │   • LiveKit WebRTC           │   │   • Text-to-Speech natural     │
         └──────────────────────────────┘   └────────────────────────────────┘


┌────────────────────────────────────────────────────────────────────────────┐
│                      CAPA DE INTEGRACIÓN EMPRESARIAL                       │
│                        (MCP-Odoo - Python/FastMCP)                         │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                           server.py (ASGI)                          │  │
│  │  • Inicialización FastMCP                                           │  │
│  │  • Registro de tools                                                │  │
│  │  • Health check endpoint                                            │  │
│  └──────────────────────────────────┬──────────────────────────────────┘  │
│                                     │                                     │
│         ┌───────────────────────────┼───────────────────────────┐         │
│         │                           │                           │         │
│  ┌──────▼──────┐           ┌────────▼────────┐         ┌───────▼───────┐ │
│  │   CORE/     │           │    TOOLS/       │         │   SCRIPTS/    │ │
│  │             │           │   (Plugins)     │         │               │ │
│  │ • config.py │           │                 │         │ • Dockerfile  │ │
│  │ • odoo_     │◄──────────┤ • crm.py        │         │ • Makefile    │ │
│  │   client.py │           │ • projects.py   │         │ • build.sh    │ │
│  │ • helpers.py│           │ • sales.py      │         │               │ │
│  │             │           │ • tasks.py      │         └───────────────┘ │
│  │             │           │ • users.py      │                           │
│  │             │           │ • search.py     │                           │
│  └─────────────┘           └─────────┬───────┘                           │
│                                      │                                    │
└──────────────────────────────────────┼────────────────────────────────────┘
                                       │
                                  XML-RPC API
                                       │
                         ┌─────────────▼──────────────┐
                         │       Odoo ERP             │
                         │   • CRM                    │
                         │   • Ventas                 │
                         │   • Proyectos              │
                         │   • Tareas                 │
                         │   • Base de datos          │
                         └────────────────────────────┘
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

**Responsabilidad:** Exposición de funcionalidades ERP via MCP

**Tecnologías:**
- Python 3.11+
- FastMCP (framework MCP)
- XML-RPC (protocolo Odoo)
- uvicorn (servidor ASGI)

**Arquitectura Modular:**

#### `server.py` - Servidor MCP
```python
mcp = FastMCP(Config.MCP_NAME)
    - Inicializar ASGI
    - Cargar tools de forma lazy
    - Health check endpoint
```

#### `core/config.py` - Configuración
```python
class Config:
    - Credenciales Odoo
    - Validación de conexión
    - Constantes del servidor
```

#### `core/odoo_client.py` - Cliente Odoo
```python
class OdooClient:
    - Autenticación XML-RPC
    - CRUD operations:
        • search()
        • search_read()
        • read()
        • create()
        • write()
        • unlink()
```

#### `core/helpers.py` - Utilidades
```python
- encode_content() → Formato MCP
- odoo_form_url() → URLs de formularios
- wants_projects() → Detección de intención
- wants_tasks() → Detección de intención
```

#### `tools/` - Herramientas MCP (Plugin System)
```python
crm.py          → Gestión de CRM
projects.py     → Gestión de proyectos
sales.py        → Gestión de ventas
tasks.py        → Gestión de tareas
users.py        → Gestión de usuarios
search.py       → Búsqueda genérica
```

**Autoload de Tools:**
```python
# tools/__init__.py
for file in os.listdir(tools_dir):
    if file.endswith('.py') and file != '__init__.py':
        module = importlib.import_module(f'tools.{name}')
        if hasattr(module, 'register'):
            module.register(mcp, deps)
```

**Flujo de Datos:**
```
Cliente MCP (Claude Desktop)
    ↓
server.py
    ↓
tools/*.py
    ↓
core/odoo_client.py
    ↓
XML-RPC
    ↓
Odoo ERP
```

**Patrones aplicados:**
- Plugin Pattern (tools autoload)
- Repository Pattern (OdooClient)
- Facade Pattern (helpers)
- Lazy Loading (tools cargados en primer request)
- Dependency Injection (deps dict)

---

### 4️⃣ Capa de Recursos (Resources)

**Responsabilidad:** Configuración y datos compartidos

**Contenido:**
```
resources/
├── elevenLabs/
│   └── prompt.txt      # Prompt del agente conversacional
└── odoo/
    └── data.py         # Configuración y datos Odoo
```

**Propósito:**
- Centralizar configuraciones de prompts
- Datos de prueba y fixtures
- Configuraciones compartidas

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

### Flujo 2: Consulta a Odoo

```
1. Usuario pregunta sobre proyectos
   ↓
2. ElevenLabs ConvAI detecta intención
   ↓
3. ConvAI invoca tool MCP (via protocolo)
   ↓
4. MCP-Odoo server recibe request
   ↓
5. Tools router procesa y ejecuta search.py
   ↓
6. OdooClient realiza XML-RPC call a Odoo
   ↓
7. Odoo devuelve datos
   ↓
8. Helper formatea respuesta en formato MCP
   ↓
9. Respuesta retorna a ConvAI
   ↓
10. ConvAI genera texto natural con los datos
    ↓
11. Texto se envía a HeyGen para animar avatar
    ↓
12. Usuario ve y escucha respuesta
```

### Flujo 3: Inicialización del Sistema

```
1. Iniciar ServerAvatar
   ├→ Cargar core/config.py
   ├→ Validar variables de entorno
   ├→ Inicializar servicios (HeyGen, ElevenLabs)
   ├→ Registrar handlers (HTTP, WebSocket)
   └→ Escuchar en puerto 8080

2. Iniciar MCP-Odoo (opcional)
   ├→ Cargar core/config.py
   ├→ Validar credenciales Odoo
   ├→ Conectar a Odoo (XML-RPC)
   ├→ Cargar tools (autoload)
   └→ Escuchar en puerto 8000

3. Abrir Frontend
   ├→ Cargar HTML/CSS/JS
   ├→ Conectar WebSocket a ServerAvatar
   ├→ Inicializar LiveKit
   ├→ Solicitar permisos de micrófono
   └→ Listo para interactuar
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
server.py
  ├→ core/config.py
  ├→ core/odoo_client.py
  │   └→ core/config.py
  └→ tools/
      ├→ crm.py ──┐
      ├→ projects.py ─┤
      ├→ sales.py ────┤
      ├→ tasks.py ────┤
      ├→ users.py ────┼→ core/odoo_client.py
      └→ search.py ───┤   core/helpers.py
                      │   core/config.py
                      └→ (todos usan deps dict)
```

## 🔒 Seguridad

### Gestión de Secretos
- Todas las API keys en archivos `.env`
- Archivos `.env` en `.gitignore`
- No hay hardcoded secrets
- `Config.print_config()` oculta claves sensibles

### Validación
- Validación de configuración al inicio
- Manejo de errores en API calls
- Timeouts en requests externos
- Logging de errores (sin exponer secrets)

### Comunicación
- WebSocket sobre HTTP/HTTPS
- LiveKit con autenticación
- XML-RPC sobre HTTPS (Odoo)
- API keys en headers (no en URLs)

## ⚡ Performance y Escalabilidad

### Optimizaciones Actuales
- **Async/await** en Python (aiohttp)
- **Lazy loading** de tools MCP
- **WebSocket** para comunicación eficiente
- **WebRTC** para streaming optimizado
- **Caching** de configuración

### Escalabilidad Futura
- [ ] Load balancer para ServerAvatar
- [ ] Redis para caché distribuido
- [ ] Message queue (RabbitMQ/Kafka)
- [ ] Kubernetes para orquestación
- [ ] CDN para assets estáticos
- [ ] Database connection pooling

## 🧪 Testing Strategy

### Niveles de Testing
```
Unit Tests
  ├→ core/config.py (validación)
  ├→ core/odoo_client.py (mocks XML-RPC)
  ├→ services/heygen_service.py (mocks API)
  └→ services/elevenlabs_service.py (mocks API)

Integration Tests
  ├→ handlers/websocket_handler.py
  └→ tools/*.py (con Odoo de prueba)

End-to-End Tests
  └→ Flujo completo usuario → avatar → Odoo
```

## 📈 Métricas y Monitoring

### Métricas Clave
- Latencia de WebSocket
- Tiempo de respuesta de APIs externas
- Tasa de errores por servicio
- Uso de memoria/CPU
- Conexiones activas

### Logging
- Logger centralizado con emojis
- Niveles: INFO, WARN, ERROR
- Contexto en cada log
- No exponer secrets en logs

## 🔮 Evolución Futura

### Fase 1 (Actual) ✅
- [x] Avatar IA funcional
- [x] Conversación con ElevenLabs
- [x] Integración Odoo básica
- [x] Frontend modular

### Fase 2 (Corto Plazo)
- [ ] Tests automatizados
- [ ] CI/CD pipeline
- [ ] Docker compose completo
- [ ] Monitoring y alertas

### Fase 3 (Mediano Plazo)
- [ ] Multi-idioma
- [ ] Dashboard administrativo
- [ ] Analytics y reportes
- [ ] Autenticación de usuarios

### Fase 4 (Largo Plazo)
- [ ] Microservicios
- [ ] Escalado horizontal
- [ ] Multi-tenancy
- [ ] IA personalizada por usuario

---

## 📚 Referencias Técnicas

- **HeyGen API:** https://docs.heygen.com/
- **ElevenLabs API:** https://elevenlabs.io/docs/
- **LiveKit:** https://docs.livekit.io/
- **FastMCP:** https://github.com/jlowin/fastmcp
- **Odoo XML-RPC:** https://www.odoo.com/documentation/17.0/developer/reference/external_api.html
- **aiohttp:** https://docs.aiohttp.org/

---

**Última actualización:** 15 de diciembre de 2025  
**Versión:** 2.0  
**Autor:** Daniel Agent Project Team
