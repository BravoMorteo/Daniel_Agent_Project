# Utils

Utilidades compartidas del servidor.

## 📁 Contenido

### `Logger`
Sistema de logging con emojis para mejor visualización.

**Métodos:**
- `info(message)` - ℹ️ Información general
- `success(message)` - ✅ Operación exitosa
- `warning(message)` - ⚠️ Advertencia
- `error(message)` - ❌ Error
- `debug(message)` - 🔍 Debug/diagnóstico
- `event(message)` - 📨 Evento
- `avatar(message)` - 🎭 Relacionado con avatar
- `audio(message)` - 🎤 Relacionado con audio
- `video(message)` - 📹 Relacionado con video
- `ai(message)` - 🤖 Relacionado con IA

## 📝 Uso

```python
from utils import Logger

Logger.info("Servidor iniciado")
Logger.success("Avatar creado correctamente")
Logger.warning("Conexión inestable")
Logger.error("Fallo al conectar con API")
Logger.avatar("Enviando comando al avatar")
Logger.ai("ElevenLabs respondió")
```

## 🎨 Ventajas

- **Visual:** Emojis facilitan identificar tipo de mensaje
- **Consistente:** Formato uniforme en todo el servidor
- **Simple:** Métodos estáticos, no requiere instanciación
- **Extensible:** Fácil agregar nuevos métodos temáticos

## 🔧 Extensión

Para agregar nuevos tipos de log:

```python
@staticmethod
def mi_tipo(message: str):
    """Log personalizado"""
    print(f"🔥 {message}")
```
