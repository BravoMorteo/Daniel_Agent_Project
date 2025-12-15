# 🤖 Daniel Agent Project# Daniel Agent Project



Proyecto integral de IA conversacional con avatar virtual y integración empresarial con Odoo ERP.Proyecto de integración de avatar IA con servicios de voz y CRM Odoo.



## 🎯 Descripción General## 📁 Estructura del Proyecto



**Daniel Agent Project** es una solución completa que combina:```

- 🎭 **Avatar IA en tiempo real** con HeyGen Streaming AvatarDaniel_Agent_Project/

- 🗣️ **Conversación IA avanzada** con ElevenLabs ConvAI├── frontend/               # Interfaz de usuario

- 💼 **Integración ERP** con Odoo a través de Model Context Protocol (MCP)│   ├── index_livekit.html # Aplicación web principal

- 🌐 **Frontend modular** con WebRTC y LiveKit│   ├── css/               # Estilos

│   ├── js/                # Componentes JavaScript modulares

## 📁 Estructura del Proyecto│   └── assets/            # Recursos estáticos

│

```├── services/              # Servicios backend

Daniel_Agent_Project/│   ├── mcp-odoo/         # Servidor MCP para integración con Odoo

├── frontend/                    # 🌐 Interfaz web del usuario│   └── serverAvatar/     # Servidor de streaming de avatar (HeyGen)

│   ├── index_livekit.html      # Página principal con avatar│

│   ├── index_public.html       # Página pública└── .gitignore            # Configuración de Git

│   ├── css/                    # Estilos modulares

│   ├── js/                     # JavaScript modular```

│   │   ├── app.js             # Aplicación principal

│   │   ├── config.js          # Configuración## 🚀 Componentes Principales

│   │   ├── audioHandler.js    # Manejo de audio

│   │   ├── videoHandler.js    # Manejo de video### Frontend

│   │   ├── livekitHandler.js  # LiveKit WebRTCInterfaz web que integra:

│   │   ├── websocketHandler.js # Comunicación WS- **HeyGen Avatar**: Avatar IA animado

│   │   └── utils.js           # Utilidades- **ElevenLabs**: Síntesis de voz

│   └── README.md- **LiveKit**: Streaming de video en tiempo real

│

├── services/                    # 🔧 Servicios backendVer [frontend/README.md](frontend/README.md) para más detalles.

│   ├── serverAvatar/           # 🎭 Servidor de avatar

│   │   ├── server.py          # Punto de entrada### Services

│   │   ├── core/              # Configuración

│   │   │   └── config.py#### MCP-Odoo

│   │   ├── handlers/          # HTTP y WebSocketServidor de Model Context Protocol para integración con Odoo ERP:

│   │   │   ├── http_handlers.py- Gestión de CRM

│   │   │   └── websocket_handler.py- Gestión de ventas

│   │   ├── services/          # Integraciones API- Gestión de proyectos y tareas

│   │   │   ├── heygen_service.py- Gestión de usuarios

│   │   │   └── elevenlabs_service.py

│   │   ├── utils/             # Utilidades (Logger)Ver [services/mcp-odoo/README.md](services/mcp-odoo/README.md) para más detalles.

│   │   ├── README.md

│   │   └── ARCHITECTURE.md#### ServerAvatar

│   │Servidor de streaming de avatar con HeyGen:

│   └── mcp-odoo/              # 💼 Servidor MCP para Odoo- Integración con HeyGen Streaming API

│       ├── server.py          # Punto de entrada- WebSocket para comunicación en tiempo real

│       ├── core/              # Core modules- Proxy de streaming de video

│       │   ├── config.py      # Configuración

│       │   ├── odoo_client.py # Cliente XML-RPCVer [services/serverAvatar/README.md](services/serverAvatar/README.md) para más detalles.

│       │   └── helpers.py     # Utilidades

│       ├── tools/             # Tools MCP## 🔧 Configuración

│       │   ├── crm.py         # Gestión CRM

│       │   ├── projects.py    # Gestión proyectos### Requisitos

│       │   ├── sales.py       # Gestión ventas- Python 3.11+

│       │   ├── tasks.py       # Gestión tareas- Node.js (para frontend, si es necesario)

│       │   ├── users.py       # Gestión usuarios- Navegador web moderno con soporte para WebRTC

│       │   └── search.py      # Búsqueda general

│       ├── scripts/           # Deployment### Variables de Entorno

│       │   ├── DockerfileCada servicio requiere su propio archivo `.env`. Ver la documentación de cada servicio para más detalles.

│       │   ├── Makefile

│       │   └── build.sh## 📝 Desarrollo

│       ├── README.md

│       └── ARCHITECTURE.md### Frontend

│El frontend está organizado en componentes modulares reutilizables:

├── resources/                  # 📦 Recursos compartidos- `config.js`: Configuración centralizada

│   ├── elevenLabs/- `utils.js`: Utilidades y helpers

│   │   └── prompt.txt         # Prompt del agente IA- `videoHandler.js`: Manejo de video

│   └── odoo/- `audioHandler.js`: Manejo de audio

│       └── data.py            # Datos y configuración Odoo- `livekitHandler.js`: Integración con LiveKit

│- `websocketHandler.js`: Comunicación WebSocket

├── README.md                   # 📖 Este archivo- `app.js`: Aplicación principal

├── ARCHITECTURE.md             # 🏗️ Arquitectura completa

├── .gitignore                  # Git ignore rules### Gitignore

└── REFACTORIZACION_COMPLETA.md # Historial de refactorizaciónEl proyecto cuenta con un `.gitignore` centralizado que:

```- Respeta las exclusiones de `mcp-odoo`

- Omite librerías externas de `serverAvatar`

## 🚀 Componentes Principales- Excluye archivos sensibles y temporales



### 1. Frontend 🌐## 📄 Licencia



**Tecnologías:** HTML5, JavaScript (ES6+), CSS3, WebRTC, LiveKitEste proyecto es privado.



**Funcionalidad:**## 👤 Autor

- Interfaz de usuario para interactuar con el avatar

- Captura de audio del micrófonoBravoMorteo

- Reproducción de video del avatar en tiempo real
- Comunicación WebSocket bidireccional

**Inicio rápido:**
```bash
cd frontend
# Abrir index_livekit.html en navegador
# O servir con un servidor HTTP
python -m http.server 8080
```

Ver [frontend/README.md](frontend/README.md) para más detalles.

---

### 2. ServerAvatar 🎭

**Tecnologías:** Python 3.11+, aiohttp, HeyGen API, ElevenLabs API, LiveKit

**Funcionalidad:**
- Servidor híbrido que orquesta avatar y conversación
- Integración con HeyGen Streaming Avatar
- Relay de conversación con ElevenLabs ConvAI
- WebSocket para comunicación en tiempo real

**Inicio rápido:**
```bash
cd services/serverAvatar

# Configurar .env
cat > .env << EOF
HEYGEN_API_KEY=tu_api_key
HEYGEN_AVATAR_ID=tu_avatar_id
ELEVENLABS_API_KEY=tu_api_key
ELEVENLABS_AGENT_ID=tu_agent_id
EOF

# Instalar dependencias
pip install aiohttp python-dotenv

# Ejecutar
python server.py
```

Ver [services/serverAvatar/README.md](services/serverAvatar/README.md) para más detalles.

---

### 3. MCP-Odoo 💼

**Tecnologías:** Python 3.11+, FastMCP, Odoo XML-RPC

**Funcionalidad:**
- Servidor Model Context Protocol para Odoo ERP
- Gestión de CRM (leads, oportunidades, contactos)
- Gestión de ventas (pedidos, productos, clientes)
- Gestión de proyectos y tareas
- Búsqueda y recuperación de datos

**Inicio rápido:**
```bash
cd services/mcp-odoo

# Configurar .env
cat > .env << EOF
ODOO_URL=https://tu-odoo.com
ODOO_DB=tu_db
ODOO_LOGIN=tu_email
ODOO_API_KEY=tu_key
EOF

# Instalar dependencias
pip install -e .

# Ejecutar
python server.py
```

Ver [services/mcp-odoo/README.md](services/mcp-odoo/README.md) para más detalles.

---

## 🔄 Flujo de Trabajo Completo

```
┌─────────────────────────────────────────────────────────────┐
│                        USUARIO                              │
│                    (Navegador Web)                          │
└────────────┬───────────────────────────────┬────────────────┘
             │                               │
        HTTP/WS                         WebRTC/LiveKit
             │                               │
┌────────────▼────────────┐    ┌────────────▼────────────────┐
│   Frontend (HTML/JS)    │    │   HeyGen Avatar Service     │
│  - Captura audio        │    │   - Genera video avatar     │
│  - Muestra video        │    │   - Sincroniza labios       │
│  - UI interactiva       │◄───┤   - Streaming en vivo      │
└────────────┬────────────┘    └─────────────────────────────┘
             │                               ▲
        WebSocket                            │
             │                          API Calls
             ▼                               │
┌────────────────────────────┐    ┌─────────┴─────────────────┐
│   ServerAvatar (Python)    │    │   ElevenLabs ConvAI       │
│  - Orquesta flujo          │───►│   - Procesa conversación  │
│  - Relay de audio/texto    │    │   - Genera respuestas     │
│  - WebSocket handler       │    │   - TTS natural           │
└────────────┬───────────────┘    └───────────────────────────┘
             │
        MCP Protocol
             │
             ▼
┌────────────────────────────┐    ┌───────────────────────────┐
│   MCP-Odoo Server          │───►│      Odoo ERP             │
│  - Tools MCP               │    │   - Base de datos         │
│  - Cliente XML-RPC         │    │   - Lógica de negocio     │
│  - Búsqueda y CRUD         │    │   - CRM, Ventas, etc.     │
└────────────────────────────┘    └───────────────────────────┘
```

## 🛠️ Instalación y Configuración

### Requisitos Previos

- **Python 3.11+**
- **Node.js 18+** (opcional, para herramientas de desarrollo)
- **Cuentas activas:**
  - HeyGen API Key
  - ElevenLabs API Key
  - Odoo ERP (URL, DB, credenciales)

### Instalación Completa

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd Daniel_Agent_Project

# 2. Configurar ServerAvatar
cd services/serverAvatar
cp .env.example .env
# Editar .env con tus credenciales
pip install aiohttp python-dotenv

# 3. Configurar MCP-Odoo
cd ../mcp-odoo
cp .env.example .env
# Editar .env con credenciales de Odoo
pip install -e .

# 4. Ejecutar servicios
# Terminal 1: ServerAvatar
cd services/serverAvatar
python server.py

# Terminal 2: MCP-Odoo (opcional)
cd services/mcp-odoo
python server.py

# 5. Abrir frontend
cd frontend
# Abrir index_livekit.html en navegador
```

## 🔐 Configuración de Variables de Entorno

### ServerAvatar (.env)
```bash
# HeyGen
HEYGEN_API_KEY=your_heygen_api_key
HEYGEN_AVATAR_ID=your_avatar_id

# ElevenLabs
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_AGENT_ID=your_agent_id

# Server
PORT=8080
```

### MCP-Odoo (.env)
```bash
# Odoo
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_LOGIN=your_email@example.com
ODOO_API_KEY=your_odoo_api_key

# Server
PORT=8000
```

## 📚 Documentación Adicional

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura completa del proyecto
- **[frontend/README.md](frontend/README.md)** - Documentación del frontend
- **[services/serverAvatar/ARCHITECTURE.md](services/serverAvatar/ARCHITECTURE.md)** - Arquitectura ServerAvatar
- **[services/mcp-odoo/ARCHITECTURE.md](services/mcp-odoo/ARCHITECTURE.md)** - Arquitectura MCP-Odoo
- **[REFACTORIZACION_COMPLETA.md](REFACTORIZACION_COMPLETA.md)** - Historial de refactorización

## 🧪 Testing

### ServerAvatar
```bash
cd services/serverAvatar
python -c "from core.config import Config; Config.validate(); print('✅ Config OK')"
```

### MCP-Odoo
```bash
cd services/mcp-odoo
python -c "from core import Config, OdooClient; Config.validate(); print('✅ Config OK')"
```

### Frontend
```bash
cd frontend
# Abrir en navegador y verificar consola JavaScript
```

## 🐛 Troubleshooting

### Error: "Import 'aiohttp' could not be resolved"
```bash
pip install aiohttp python-dotenv
```

### Error: "HeyGen API Key no configurada"
```bash
# Verificar .env en services/serverAvatar
cat services/serverAvatar/.env
```

### Error: "No se puede conectar a Odoo"
```bash
# Verificar credenciales en services/mcp-odoo/.env
# Probar conexión manualmente
cd services/mcp-odoo
python -c "from core import OdooClient; c = OdooClient(); print(c.search('res.users', [], 1))"
```

## 🚀 Deployment

### Docker (MCP-Odoo)
```bash
cd services/mcp-odoo/scripts
docker build -f Dockerfile -t mcp-odoo ..
docker run --env-file ../.env -p 8000:8000 mcp-odoo
```

### Producción (ServerAvatar)
```bash
cd services/serverAvatar
pip install gunicorn
gunicorn server:app --bind 0.0.0.0:8080 --worker-class aiohttp.GunicornWebWorker
```

## 📊 Características Principales

### ✅ Implementado

- ✅ Avatar IA en tiempo real con HeyGen
- ✅ Conversación IA con ElevenLabs ConvAI
- ✅ Integración Odoo ERP via MCP
- ✅ Frontend modular con WebRTC
- ✅ Arquitectura modular y escalable
- ✅ Documentación completa
- ✅ Logger con emojis
- ✅ Validación de configuración

### 🔮 Roadmap Futuro

- [ ] Tests unitarios e integración
- [ ] CI/CD pipeline
- [ ] Métricas y monitoring
- [ ] Rate limiting
- [ ] Caché distribuido (Redis)
- [ ] Autenticación y autorización
- [ ] Multi-idioma
- [ ] Dashboard administrativo

## 👥 Contribuciones

Para contribuir al proyecto:

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.

## 🙏 Agradecimientos

- **HeyGen** - Streaming Avatar API
- **ElevenLabs** - Conversational AI
- **Odoo** - ERP System
- **LiveKit** - WebRTC infrastructure
- **FastMCP** - Model Context Protocol framework

---

**Última actualización:** 15 de diciembre de 2025  
**Versión:** 2.0 (Refactorizado y modular)  
**Estado:** ✅ Producción
