# 🔧 MCP-Odoo: Servidor Híbrido de Integración con Odoo ERP

**Servidor híbrido que combina Model Context Protocol (MCP) + FastAPI REST en un solo servicio.**

> 📖 **Para documentación exhaustiva**: Ver [README_DETALLADO.md](README_DETALLADO.md)

---

## 🎯 ¿Qué hace este servicio?

MCP-Odoo permite que:
- **LLMs** (Claude, GPT) ejecuten acciones en Odoo mediante herramientas MCP
- **Aplicaciones web** creen cotizaciones y consulten datos via REST API
- **Servicios externos** (ElevenLabs, Twilio) envíen webhooks

**Todo en un solo servidor, puerto 8000.**

---

## ✨ Características Principales

- ⚡ **Protocolo Híbrido** - MCP para IA + REST API para web
- 🔄 **Operaciones Asíncronas** - Cotizaciones en background con tracking
- 📝 **Logging Avanzado** - Logs JSON locales + subida automática a S3
- 🔔 **Notificaciones WhatsApp** - Handoff automático a vendedores
- 🐳 **Docker Ready** - Deployment simplificado
- 📊 **Auto-documentación** - Swagger UI en `/docs`

---

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

\`\`\`bash
cd services/mcp-odoo
pip install -e .
\`\`\`

### 2. Configurar Variables de Entorno

\`\`\`bash
cp .env.example .env
nano .env
\`\`\`

**Mínimo requerido**:
\`\`\`bash
# Odoo Producción (solo lectura)
ODOO_URL=https://tu-instancia.odoo.com
ODOO_DB=tu_database
ODOO_LOGIN=tu_email@example.com
ODOO_API_KEY=tu_api_key

# Odoo Desarrollo (escritura)
DEV_ODOO_URL=https://tu-instancia-dev.odoo.com
DEV_ODOO_DB=tu_database_dev
DEV_ODOO_LOGIN=tu_email@example.com
DEV_ODOO_API_KEY=tu_api_key
\`\`\`

**Opcional** (logs S3, WhatsApp):
\`\`\`bash
# AWS S3 para Logs
S3_LOGS_BUCKET=ilagentslogs
AWS_REGION=us-west-2

# WhatsApp / Twilio
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
\`\`\`

### 3. Ejecutar Servidor

\`\`\`bash
python server.py
\`\`\`

**Acceso**:
- 📡 MCP Protocol: http://localhost:8000/mcp/sse
- 🌐 API REST: http://localhost:8000/api/*
- 📚 Documentación: http://localhost:8000/docs
- ✅ Health Check: http://localhost:8000/health

---

## 🔧 Herramientas MCP Disponibles

| Herramienta | Descripción | Parámetros |
|-------------|-------------|------------|
| \`dev_create_quotation\` | Crea cotización completa (lead + orden) | partner_name, email, phone, product_id |
| \`dev_create_sale\` | Crea orden de venta | partner_id, user_id |
| \`list_tasks\` | Lista tareas de proyectos | project_id, assigned_to_name, limit |
| \`list_users\` | Lista usuarios/vendedores | q, limit |
| \`list_sales\` | Lista órdenes de venta | state, user_id, limit |
| \`search\` | Búsqueda general en Odoo | query, limit |
| \`message_notification\` | Envía WhatsApp a vendedor | user_phone, reason, lead_id |

> 📖 **Ver todas las herramientas**: [README_DETALLADO.md#8-herramientas-mcp](README_DETALLADO.md#8-herramientas-mcp-disponibles)

---

## 🌐 API REST Endpoints

### Crear Cotización Asíncrona
\`\`\`bash
POST /api/quotation/async
Content-Type: application/json

{
  "partner_name": "Almacenes Torres",
  "contact_name": "Luis Fernández",
  "email": "luis@almacenes.com",
  "phone": "+521234567890",
  "lead_name": "Cotización Robot PUDU",
  "product_id": 26174,
  "product_qty": 2
}

# Respuesta:
{
  "tracking_id": "quot_abc123",
  "status": "queued",
  "message": "Cotización en proceso"
}
\`\`\`

### Consultar Estado
\`\`\`bash
GET /api/quotation/status/{tracking_id}

# Respuesta:
{
  "status": "completed",
  "output": {
    "sale_order_id": 12345,
    "sale_order_name": "S12345",
    "lead_id": 9876
  }
}
\`\`\`

### Handoff a Vendedor
\`\`\`bash
POST /api/elevenlabs/handoff
Content-Type: application/json

{
  "user_phone": "+521234567890",
  "reason": "Cliente solicita asistencia personalizada",
  "conversation_id": "conv_xyz"
}
\`\`\`

> 📖 **Documentación completa de API**: [README_DETALLADO.md#9-api-rest-endpoints](README_DETALLADO.md#9-api-rest-endpoints)

---

## 🏗️ Arquitectura Simplificada

\`\`\`
┌────────────────────────────────────────────────┐
│          FastAPI App (Puerto 8000)             │
├────────────────────────────────────────────────┤
│                                                │
│  /mcp/*   →  Para LLMs (Claude)                │
│              • Protocol MCP                     │
│              • Herramientas tools/*             │
│                                                │
│  /api/*   →  Para Apps Web/Webhooks            │
│              • REST tradicional                 │
│              • JSON requests/responses          │
│                                                │
└──────────────────┬─────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
    ┌────▼─────┐      ┌──────▼─────┐
    │  Odoo    │      │  AWS S3    │
    │  ERP     │      │  (Logs)    │
    └──────────┘      └────────────┘
\`\`\`

> 📖 **Arquitectura detallada**: [README_DETALLADO.md#2-arquitectura-del-sistema](README_DETALLADO.md#2-arquitectura-del-sistema)

---

## 📂 Estructura del Proyecto

\`\`\`
mcp-odoo/
├── server.py              # 🚀 Punto de entrada (FastMCP + FastAPI)
├── core/                  # 🧠 Lógica central
│   ├── config.py         # Configuración y variables .env
│   ├── odoo_client.py    # Cliente XML-RPC para Odoo
│   ├── api.py            # Modelos Pydantic para REST
│   ├── tasks.py          # TaskManager (async background)
│   ├── logger.py         # Logging JSON → S3
│   └── whatsapp.py       # Cliente Twilio WhatsApp
├── tools/                 # 🔧 Herramientas MCP
│   ├── __init__.py       # Auto-carga de tools
│   ├── crm.py            # Gestión CRM (leads)
│   ├── sales.py          # Gestión ventas (órdenes)
│   ├── projects.py       # Gestión proyectos
│   ├── tasks.py          # Gestión tareas
│   ├── users.py          # Gestión usuarios
│   ├── search.py         # Búsqueda general
│   └── whatsapp.py       # Notificaciones
├── docs/                  # 📚 Documentación
│   ├── S3_LOGS_SETUP.md  # Setup logs AWS S3
│   └── WHATSAPP_HANDOFF.md # Sistema handoff
└── scripts/               # 🐳 Deployment
    ├── Dockerfile        # Imagen Docker
    ├── build.sh          # Build script
    └── Makefile          # Comandos útiles
\`\`\`

> 📖 **Explicación de cada archivo**: [README_DETALLADO.md#4-estructura-de-archivos](README_DETALLADO.md#4-estructura-de-archivos)

---

## ⚠️ Problemas Comunes

### 1. "Missing environment variables"
\`\`\`bash
# Editar .env y agregar las variables faltantes
nano .env
\`\`\`

### 2. "Authentication failed"
\`\`\`bash
# Verificar que tu API Key sea correcta en Odoo:
# Settings → Users → Tu usuario → Preferences → Security → API Keys
\`\`\`

### 3. "Port 8000 already in use"
\`\`\`bash
# Encontrar y matar proceso
lsof -ti:8000 | xargs kill -9

# Reiniciar servidor
python server.py
\`\`\`

### 4. "Logs no se suben a S3"
\`\`\`bash
# Verificar credenciales AWS
aws sts get-caller-identity

# Ver guía completa
cat docs/S3_LOGS_SETUP.md
\`\`\`

> 📖 **Más soluciones**: [README_DETALLADO.md#10-problemas-comunes-y-soluciones](README_DETALLADO.md#10-problemas-comunes-y-soluciones)

---

## 🧪 Testing y Desarrollo

### Health Check
\`\`\`bash
curl http://localhost:8000/health
\`\`\`

### Crear Cotización de Prueba
\`\`\`bash
curl -X POST http://localhost:8000/api/quotation/async \\
  -H "Content-Type: application/json" \\
  -d '{
    "partner_name": "Test Company",
    "contact_name": "Test User",
    "email": "test@example.com",
    "phone": "+521234567890",
    "lead_name": "Test Lead",
    "product_id": 26174,
    "product_qty": 1
  }'
\`\`\`

### Ver Documentación Interactiva
\`\`\`bash
open http://localhost:8000/docs
\`\`\`

### Ejecutar con Logs Visibles
\`\`\`bash
python -u server.py
\`\`\`

> 📖 **Guía completa de testing**: [README_DETALLADO.md#11-desarrollo-y-testing](README_DETALLADO.md#11-desarrollo-y-testing)

---

## 📚 Documentación Adicional

| Documento | Contenido |
|-----------|-----------|
| **[README_DETALLADO.md](README_DETALLADO.md)** | 📖 Guía completa y exhaustiva del servicio |
| [docs/S3_LOGS_SETUP.md](docs/S3_LOGS_SETUP.md) | ☁️ Configurar logs en AWS S3 |
| [docs/WHATSAPP_HANDOFF.md](docs/WHATSAPP_HANDOFF.md) | 📱 Sistema de handoff a vendedores |
| [scripts/README.md](scripts/README.md) | 🐳 Deployment con Docker |

---

## 🔄 Flujo de Operaciones

### Ejemplo: LLM crea cotización

\`\`\`
1. Usuario → "Crea cotización para Robot PUDU, cliente Torres"
2. Claude → Llama tool dev_create_quotation via MCP
3. MCP-Odoo → Crea lead + orden + producto en Odoo
4. Odoo → Retorna S12345
5. Claude → "Cotización S12345 creada exitosamente"
\`\`\`

### Ejemplo: Web App crea cotización

\`\`\`
1. Frontend → POST /api/quotation/async
2. FastAPI → TaskManager.create_task()
3. Task Background → Ejecuta creación en Odoo
4. Frontend → GET /api/quotation/status/{id} (polling)
5. FastAPI → Retorna estado: "completed" + resultado
\`\`\`

> 📖 **Diagramas detallados**: [README_DETALLADO.md#5-flujo-de-peticiones](README_DETALLADO.md#5-flujo-de-peticiones)

---

## 🚀 Deployment

### Con Docker

\`\`\`bash
cd scripts
docker build -t mcp-odoo .
docker run -p 8000:8000 --env-file ../.env mcp-odoo
\`\`\`

### Con PM2

\`\`\`bash
pm2 start server.py --name mcp-odoo --interpreter python3
pm2 save
pm2 startup
\`\`\`

### Producción

\`\`\`bash
# Usar Gunicorn con Uvicorn workers
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
\`\`\`

---

## 👤 Autor

**BravoMorteo**

---

## 📄 Licencia

MIT License

---

**Versión**: 2.0.0  
**Estado**: ✅ Producción  
**Actualizado**: Enero 2025

---

## 💡 Consejos Finales

1. **Siempre lee [README_DETALLADO.md](README_DETALLADO.md) primero** - Contiene información exhaustiva
2. **Usa \`/docs\` en desarrollo** - Swagger UI te muestra todas las APIs disponibles
3. **Revisa logs en tiempo real** - \`python -u server.py\` para debugging
4. **Consulta S3 para logs históricos** - Todos los requests quedan registrados
5. **Usa ambiente DEV para pruebas** - Variables \`DEV_*\` en \`.env\`

---
