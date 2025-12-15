# Core

Módulos fundamentales del servidor ServerAvatar.

## 📁 Contenido

### `config.py`
Gestión centralizada de configuración y variables de entorno.

**Clase:** `Config`

**Variables principales:**

#### HeyGen Configuration
- `HEYGEN_API_KEY` - API Key de HeyGen
- `HEYGEN_AVATAR_ID` - ID del avatar a utilizar

#### ElevenLabs Configuration  
- `ELEVENLABS_API_KEY` - API Key de ElevenLabs
- `ELEVENLABS_AGENT_ID` - ID del agente conversacional

#### Server Configuration
- `HOST` - Host del servidor (default: "0.0.0.0")
- `PORT` - Puerto del servidor (default: 8080)

**Métodos:**

#### `validate() -> None`
Valida que todas las variables requeridas estén configuradas. Lanza `ValueError` si falta alguna.

```python
from core import Config

try:
    Config.validate()
    print("✅ Configuración válida")
except ValueError as e:
    print(f"❌ Error: {e}")
```

#### `print_config() -> None`
Imprime la configuración actual (sin exponer las API keys completas).

```python
from core import Config

Config.print_config()
# 🔧 Configuración del Servidor:
# HeyGen API Key: hey_***...
# Avatar ID: avatar_123...
# ...
```

## 🔄 Uso en el Proyecto

La configuración es importada por:
- `server.py` - Validación al inicio
- `services/heygen_service.py` - API key y avatar ID
- `services/elevenlabs_service.py` - API key y agent ID

**Ejemplo:**
```python
from core import Config

# Acceder a configuración
api_key = Config.HEYGEN_API_KEY
avatar_id = Config.HEYGEN_AVATAR_ID

# Validar antes de usar
Config.validate()
```

## ⚙️ Variables de Entorno

Crear archivo `.env` en la raíz de serverAvatar:

```bash
# HeyGen
HEYGEN_API_KEY=tu_heygen_api_key
HEYGEN_AVATAR_ID=tu_avatar_id

# ElevenLabs
ELEVENLABS_API_KEY=tu_elevenlabs_api_key
ELEVENLABS_AGENT_ID=tu_agent_id

# Server (opcional)
PORT=8080
```

## 🔒 Seguridad

- Las API keys nunca se exponen completamente en logs
- El archivo `.env` debe estar en `.gitignore`
- `Config.print_config()` oculta las claves sensibles

## 📚 Dependencias

- `python-dotenv` - Para cargar variables de entorno
- `os` - Para acceder a variables de entorno

---

**Última actualización:** 15 de diciembre de 2025
