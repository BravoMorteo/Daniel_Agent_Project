# 🤖 Daniel Agent Project

**Sistema de IA Conversacional con Avatar Virtual e Integración Empresarial**

---

## 📖 ¿Qué es este proyecto?

Daniel Agent es un **asistente virtual inteligente** que combina:
- 🎭 **Avatar animado en tiempo real** que habla y se mueve como una persona real
- 🗣️ **Conversaciones naturales con IA** que entiende y responde al usuario
- 💼 **Integración con Odoo ERP** para crear cotizaciones, gestionar clientes y órdenes de venta

**Casos de uso:**
- Atención al cliente 24/7 con interfaz humana
- Generación automática de cotizaciones desde una conversación
- Traspaso a vendedores humanos cuando el cliente lo solicite
- Integración completa con sistemas empresariales (CRM, ventas, proyectos)

---

## 🎯 Objetivo del Proyecto

Crear una experiencia de **atención al cliente conversacional** donde:
1. El usuario habla por micrófono con un avatar animado
2. El avatar responde con voz natural y expresiones faciales sincronizadas
3. La IA puede realizar acciones en Odoo (crear leads, cotizaciones, consultar productos)
4. Si el cliente lo pide, un vendedor humano recibe notificación por WhatsApp

**Resultado:** Una experiencia fluida que combina la eficiencia de la IA con la calidez humana.

---

## 📁 Estructura del Proyecto

```
Daniel_Agent_Project/
│
├── frontend/                    # 🌐 Interfaz Web (Cliente)
│   ├── index_livekit.html      # Página principal de la aplicación
│   ├── css/                    # Estilos CSS
│   └── js/                     # Código JavaScript modular
│       ├── app.js              # Orquestador principal
│       ├── audioHandler.js     # Captura de audio del micrófono
│       ├── videoHandler.js     # Renderizado del video del avatar
│       ├── livekitHandler.js   # Conexión WebRTC con LiveKit
│       ├── websocketHandler.js # Comunicación con el servidor
│       └── utils.js            # Funciones auxiliares
│
├── services/                    # 🔧 Servicios Backend
│   │
│   ├── serverAvatar/           # Servidor de Streaming de Avatar
│   │   ├── server.py           # Punto de entrada (aiohttp)
│   │   ├── core/               # Configuración y lógica central
│   │   ├── handlers/           # Manejadores HTTP y WebSocket
│   │   └── services/           # Integraciones con HeyGen y ElevenLabs
│   │
│   └── mcp-odoo/               # Servidor MCP para Odoo
│       ├── server.py           # Punto de entrada (FastAPI + MCP)
│       ├── core/               # Cliente Odoo, configuración, logger
│       ├── tools/              # Herramientas MCP (CRM, ventas, proyectos)
│       ├── docs/               # Documentación técnica
│       └── scripts/            # Scripts de build y deployment
│
└── resources/                   # 📄 Recursos y configuración
    └── elevenLabs/
        └── prompt.txt          # Prompt del agente conversacional

```

---

## 🚀 ¿Cómo Ejecutar el Proyecto?

### **Paso 1: Requisitos Previos**

Antes de comenzar, asegúrate de tener:
- **Python 3.11+** instalado
- **Navegador moderno** con soporte para WebRTC (Chrome, Firefox, Edge)
- **Cuentas y credenciales:**
  - HeyGen API Key y Avatar ID
  - ElevenLabs API Key y Agent ID
  - Odoo ERP (URL, Database, Login, API Key)

### **Paso 2: Configurar ServerAvatar**

Este servicio maneja el avatar y la conversación con IA:

```bash
cd services/serverAvatar

# Crear archivo de configuración
cat > .env << EOF
HEYGEN_API_KEY=tu_heygen_api_key
HEYGEN_AVATAR_ID=tu_avatar_id
ELEVENLABS_API_KEY=tu_elevenlabs_api_key
ELEVENLABS_AGENT_ID=tu_agent_id
PORT=8080
HOST=0.0.0.0
EOF

# Instalar dependencias
pip install aiohttp python-dotenv

# Ejecutar servidor
python server.py
```

El servidor estará disponible en `http://localhost:8080`

### **Paso 3: Configurar MCP-Odoo (Opcional)**

Este servicio permite que la IA interactúe con Odoo:

```bash
cd services/mcp-odoo

# Crear archivo de configuración
cat > .env << EOF
ODOO_URL=https://tu-instancia.odoo.com
ODOO_DB=nombre_base_datos
ODOO_LOGIN=tu_email@example.com
ODOO_API_KEY=tu_odoo_api_key
PORT=8000
HOST=0.0.0.0
EOF

# Instalar dependencias
pip install -e .

# Ejecutar servidor
python server.py
```

El servidor estará disponible en `http://localhost:8000`

### **Paso 4: Abrir el Frontend**

```bash
cd frontend

# Opción 1: Abrir directamente en navegador
# Doble clic en index_livekit.html

# Opción 2: Servir con Python
python -m http.server 8888
# Luego abrir http://localhost:8888/index_livekit.html
```

### **Paso 5: Usar la Aplicación**

1. Abre la página web en tu navegador
2. Haz clic en **"Iniciar Conversación"**
3. Permite el acceso al micrófono cuando te lo pida el navegador
4. Habla con el avatar y disfruta de la conversación

---

## 🛠️ Herramientas y Tecnologías

### **Frontend (Interfaz de Usuario)**

| Herramienta | Descripción | Para qué sirve |
|-------------|-------------|----------------|
| **HTML5/CSS3/JavaScript** | Tecnologías web estándar | Crear la interfaz de usuario |
| **WebRTC** | Protocolo de comunicación en tiempo real | Transmitir audio y video sin latencia |
| **LiveKit** | Infraestructura WebRTC | Manejar las conexiones de streaming |
| **WebSocket** | Comunicación bidireccional | Enviar y recibir mensajes en tiempo real |

### **ServerAvatar (Backend de Avatar)**

| Herramienta | Descripción | Para qué sirve |
|-------------|-------------|----------------|
| **Python 3.11+** | Lenguaje de programación | Base del servidor backend |
| **aiohttp** | Framework web asíncrono | Manejar conexiones HTTP y WebSocket |
| **HeyGen API** | Servicio de avatares IA | Generar el video animado del avatar |
| **ElevenLabs API** | Servicio de IA conversacional | Procesar las conversaciones y generar voz |

### **MCP-Odoo (Backend de Integración ERP)**

| Herramienta | Descripción | Para qué sirve |
|-------------|-------------|----------------|
| **Python 3.11+** | Lenguaje de programación | Base del servidor backend |
| **FastAPI** | Framework web moderno | Crear APIs REST rápidas |
| **FastMCP** | Model Context Protocol | Exponer herramientas para la IA |
| **Odoo XML-RPC** | Protocolo de comunicación | Conectar con Odoo ERP |
| **Boto3** | SDK de AWS | Subir logs a S3 |
| **Twilio** | Servicio de mensajería | Enviar notificaciones por WhatsApp |

---

## 🏗️ Arquitectura del Proyecto

### **Visión General**

El proyecto está dividido en **3 componentes principales** que trabajan juntos:

```
┌─────────────────────────────────────────────────────────────┐
│                 USUARIO (Navegador Web)                     │
│               Habla por micrófono, ve avatar                │
└───────────────────┬─────────────────────────────────────────┘
                    │
          ┌─────────┴─────────┐
          │                   │
          ▼                   ▼
┌──────────────────┐  ┌──────────────────┐
│    Frontend      │  │   HeyGen API     │
│   (HTML/JS)      │◄─┤  (Avatar Video)  │
│ - Captura audio  │  └──────────────────┘
│ - Muestra video  │
│ - UI interactiva │
└────────┬─────────┘
         │ WebSocket
         ▼
┌──────────────────────────┐    ┌──────────────────┐
│   ServerAvatar (Python)  │───►│ ElevenLabs API   │
│  - Orquesta conversación │    │ (IA Conversación)│
│  - Relay de audio/texto  │    └──────────────────┘
│  - Coordina servicios    │
└────────┬─────────────────┘
         │ MCP Protocol
         ▼
┌────────────────────────┐      ┌──────────────────┐
│   MCP-Odoo (Python)    │─────►│   Odoo ERP       │
│ - Herramientas MCP     │      │ - CRM            │
│ - Cliente XML-RPC      │      │ - Ventas         │
│ - Búsqueda y CRUD      │      │ - Proyectos      │
└────────────────────────┘      └──────────────────┘
```

### **Explicación de cada Componente**

#### **1. Frontend** (`/frontend`)
- **¿Qué es?** La interfaz web que ve el usuario
- **¿Qué hace?**
  - Captura audio del micrófono del usuario
  - Muestra el video del avatar animado
  - Envía y recibe mensajes al servidor
  - Maneja la UI (botones, estado, transcripciones)

#### **2. ServerAvatar** (`/services/serverAvatar`)
- **¿Qué es?** El servidor que coordina el avatar y la conversación
- **¿Qué hace?**
  - Recibe audio del frontend via WebSocket
  - Envía el audio a ElevenLabs para procesamiento
  - Obtiene video del avatar desde HeyGen
  - Coordina la sincronización de audio/video
  - Relay los mensajes entre todos los componentes

#### **3. MCP-Odoo** (`/services/mcp-odoo`)
- **¿Qué es?** El servidor que conecta la IA con Odoo
- **¿Qué hace?**
  - Expone "herramientas" que la IA puede usar
  - Permite crear leads, cotizaciones, buscar productos
  - Se comunica con Odoo mediante XML-RPC
  - Registra todas las operaciones en logs
  - Envía notificaciones por WhatsApp cuando se requiere

### **¿Para qué sirve cada carpeta?**

```
frontend/
├── index_livekit.html    → Página principal de la app
├── css/                  → Estilos visuales (colores, diseño)
└── js/
    ├── app.js            → Punto de entrada, coordina todo
    ├── audioHandler.js   → Maneja micrófono y audio
    ├── videoHandler.js   → Maneja el canvas de video
    ├── livekitHandler.js → Conexión WebRTC con LiveKit
    ├── websocketHandler.js → Comunicación con servidor
    └── utils.js          → Funciones auxiliares (logger)

services/serverAvatar/
├── server.py             → Punto de entrada del servidor
├── core/
│   └── config.py         → Configuración (API keys, puertos)
├── handlers/
│   ├── http_handlers.py  → Maneja peticiones HTTP
│   └── websocket_handler.py → Maneja conexiones WebSocket
└── services/
    ├── heygen_service.py → Integración con HeyGen API
    └── elevenlabs_service.py → Integración con ElevenLabs API

services/mcp-odoo/
├── server.py             → Punto de entrada (FastAPI + MCP)
├── core/
│   ├── config.py         → Configuración de Odoo y AWS
│   ├── odoo_client.py    → Cliente para conectar con Odoo
│   ├── tasks.py          → Gestión de tareas asíncronas
│   ├── logger.py         → Sistema de logs (local + S3)
│   ├── whatsapp.py       → Cliente de Twilio para WhatsApp
│   └── helpers.py        → Funciones auxiliares
├── tools/                → Herramientas MCP (lo que la IA puede hacer)
│   ├── crm.py            → Crear/buscar leads y oportunidades
│   ├── sales.py          → Crear/buscar órdenes de venta
│   ├── projects.py       → Buscar proyectos
│   ├── tasks.py          → Buscar tareas
│   ├── users.py          → Buscar usuarios/vendedores
│   ├── search.py         → Búsqueda general en Odoo
│   └── whatsapp.py       → Notificaciones de handoff
├── docs/                 → Documentación técnica
│   ├── S3_LOGS_SETUP.md  → Cómo configurar logs en S3
│   └── WHATSAPP_HANDOFF.md → Cómo funciona el handoff
└── scripts/              → Scripts de deployment
    ├── Dockerfile        → Para crear contenedor Docker
    ├── Makefile          → Comandos útiles de desarrollo
    └── build.sh          → Script de build automatizado

resources/
└── elevenLabs/
    └── prompt.txt        → Prompt del agente conversacional
```

---

## 🔧 Sección Técnica: Relaciones entre Componentes

### **Flujo de Datos en una Conversación**

1. **Usuario habla** → El micrófono captura audio
2. **Frontend** → Envía audio via WebSocket a ServerAvatar
3. **ServerAvatar** → Reenvía audio a ElevenLabs ConvAI
4. **ElevenLabs** → Procesa la conversación y decide qué hacer:
   - Si es una pregunta simple: genera respuesta directamente
   - Si necesita datos de Odoo: llama a MCP-Odoo
5. **MCP-Odoo** (si se llama) → Ejecuta la herramienta solicitada en Odoo
6. **Odoo** → Devuelve los datos (producto, cliente, etc.)
7. **ElevenLabs** → Con los datos, genera la respuesta final en audio
8. **HeyGen** → Genera video del avatar sincronizado con el audio
9. **ServerAvatar** → Reenvía video al Frontend via LiveKit
10. **Frontend** → Muestra el video y reproduce el audio

### **Importaciones y Dependencias**

#### **En ServerAvatar:**

```python
# server.py
from aiohttp import web              # Framework web asíncrono
from core.config import Config       # Configuración centralizada
from handlers import (
    index,                           # Handler de página principal
    WebSocketHandler                 # Handler de WebSocket
)

# handlers/websocket_handler.py
from services.heygen_service import HeyGenService
from services.elevenlabs_service import ElevenLabsService
# Estos servicios se importan para coordinar avatar y conversación
```

**¿Cómo se relacionan?**
- `server.py` crea la aplicación web y registra las rutas
- `WebSocketHandler` usa `HeyGenService` y `ElevenLabsService`
- Cada servicio encapsula la lógica de comunicación con sus APIs

#### **En MCP-Odoo:**

```python
# server.py
from fastapi import FastAPI          # Framework web moderno
from mcp.server.fastmcp import FastMCP  # Model Context Protocol
from core import Config, OdooClient  # Configuración y cliente
from tools import load_all           # Carga todas las herramientas

# tools/crm.py
from core import OdooClient          # Para conectar con Odoo
from core.tasks import task_manager  # Para tareas asíncronas
from core.logger import quotation_logger  # Para logs
```

**¿Cómo se relacionan?**
- `server.py` monta el servidor FastAPI + MCP
- Carga dinámicamente todas las herramientas de `/tools`
- Cada herramienta usa `OdooClient` para hacer operaciones en Odoo
- Las operaciones largas usan `task_manager` para procesamiento asíncrono
- Todo se registra con `quotation_logger` para auditoría

#### **En Frontend:**

```javascript
// app.js
class App {
    constructor() {
        // Crea instancias de todos los manejadores
        this.videoHandler = new VideoHandler(...)
        this.audioHandler = new AudioHandler(...)
        this.livekitHandler = new LiveKitHandler(...)
        this.wsHandler = new WebSocketHandler(...)
    }
}
```

**¿Cómo se relacionan?**
- `app.js` es el orquestador principal
- Crea instancias de cada handler y los conecta
- Cada handler maneja una responsabilidad específica
- Se pasan callbacks entre handlers para coordinar acciones

### **Patrón de Arquitectura**

El proyecto sigue una **arquitectura de microservicios modular**:

- **Separación de responsabilidades**: Cada servicio tiene una función clara
- **Comunicación via APIs**: Los servicios se comunican por HTTP/WebSocket/MCP
- **Configuración externalizada**: Todo se configura via variables de entorno
- **Logging centralizado**: Todos los eventos se registran para auditoría
- **Procesamiento asíncrono**: Las tareas largas no bloquean el sistema

---

## 📚 Documentación Adicional

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Diagramas detallados de arquitectura
- **[frontend/README.md](frontend/README.md)** - Documentación del frontend
- **[services/serverAvatar/README.md](services/serverAvatar/README.md)** - Documentación ServerAvatar
- **[services/mcp-odoo/README.md](services/mcp-odoo/README.md)** - Documentación MCP-Odoo
- **[services/mcp-odoo/docs/S3_LOGS_SETUP.md](services/mcp-odoo/docs/S3_LOGS_SETUP.md)** - Configuración de logs en S3
- **[services/mcp-odoo/docs/WHATSAPP_HANDOFF.md](services/mcp-odoo/docs/WHATSAPP_HANDOFF.md)** - Sistema de handoff a vendedores

---

## 🐛 Solución de Problemas

### **El servidor no inicia**
- Verifica que tienes Python 3.11+ instalado: `python --version`
- Verifica que instalaste las dependencias: `pip list`
- Revisa el archivo `.env` y asegúrate de que las variables estén correctas

### **El avatar no aparece**
- Verifica que ServerAvatar esté ejecutándose
- Abre la consola del navegador (F12) y busca errores
- Verifica que las API keys de HeyGen sean correctas

### **No se escucha la voz**
- Verifica que permitiste acceso al micrófono
- Revisa que ElevenLabs API Key sea correcta
- Comprueba la consola del navegador para errores de WebSocket

### **La IA no puede crear cotizaciones**
- Verifica que MCP-Odoo esté ejecutándose
- Comprueba las credenciales de Odoo en el `.env`
- Revisa los logs del servidor MCP-Odoo

---

## 📊 Estado del Proyecto

**Versión:** 2.0 (Refactorizado y Limpio)  
**Última actualización:** Enero 2026  
**Estado:** ✅ En Producción

### Características Implementadas

- ✅ Avatar IA en tiempo real con HeyGen
- ✅ Conversación IA con ElevenLabs ConvAI
- ✅ Integración completa con Odoo ERP
- ✅ Frontend modular con WebRTC
- ✅ Sistema de logs en S3
- ✅ Notificaciones por WhatsApp
- ✅ Procesamiento asíncrono de cotizaciones
- ✅ Documentación completa y actualizada

---

## 👤 Autor

**BravoMorteo**

---

## 📄 Licencia

Este proyecto es privado y confidencial.

---

**¿Tienes dudas?** Revisa la documentación adicional en cada carpeta o contacta al equipo de desarrollo.
