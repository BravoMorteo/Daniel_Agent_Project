# Frontend - Daniel Agent Project

Este directorio contiene la interfaz de usuario para la integración de HeyGen Avatar + ElevenLabs con LiveKit.

## 📁 Estructura del Proyecto

```
frontend/
├── index_livekit.html      # Archivo HTML principal
├── css/
│   └── main.css            # Estilos de la aplicación
├── js/
│   ├── config.js           # Configuración de la aplicación
│   ├── utils.js            # Utilidades (Logger)
│   ├── videoHandler.js     # Manejo de video
│   ├── audioHandler.js     # Manejo de audio y micrófono
│   ├── livekitHandler.js   # Integración con LiveKit
│   ├── websocketHandler.js # Manejo de WebSocket
│   └── app.js              # Aplicación principal
└── assets/                 # Recursos estáticos
```

## 🏗️ Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                        App.js                           │
│              (Orquestador Principal)                    │
└────────────┬──────────────┬──────────────┬─────────────┘
             │              │              │
    ┌────────▼──────┐  ┌───▼────────┐  ┌──▼───────────┐
    │   Logger      │  │  Config    │  │ DOM Elements │
    │  (utils.js)   │  │ (config.js)│  │              │
    └────────┬──────┘  └────────────┘  └──────────────┘
             │
    ┌────────┴────────────────────────────────────┐
    │                                              │
┌───▼──────────────┐  ┌─────────────────────────▼────┐
│ VideoHandler     │  │    WebSocketHandler          │
│ (videoHandler.js)│  │  (websocketHandler.js)       │
└───┬──────────────┘  └─────────────┬────────────────┘
    │                                │
┌───▼──────────────┐  ┌─────────────▼────────────────┐
│ AudioHandler     │  │    LiveKitHandler            │
│ (audioHandler.js)│◄─┤  (livekitHandler.js)         │
└──────────────────┘  └──────────────────────────────┘
```

## 🧩 Componentes

### `config.js`
Contiene toda la configuración centralizada de la aplicación:
- URLs de WebSocket
- Configuración de audio
- Configuración de LiveKit

**Exporta:** `CONFIG` (objeto de configuración)

### `utils.js`
Clase `Logger` para:
- Mostrar logs en la consola de estado
- Agregar transcripciones

**Exporta:** `Logger` (clase)

### `videoHandler.js`
Clase `VideoHandler` que gestiona:
- Eventos del elemento de video
- Attachment de tracks de video
- Debug del video
- Limpieza de recursos

**Exporta:** `VideoHandler` (clase)

**Dependencias:**
- `Logger` (utils.js)

### `audioHandler.js`
Clase `AudioHandler` que gestiona:
- Captura del micrófono
- Procesamiento de audio PCM16
- Attachment de tracks de audio
- Limpieza de recursos

**Exporta:** `AudioHandler` (clase)

**Dependencias:**
- `Logger` (utils.js)
- `CONFIG` (config.js)

### `livekitHandler.js`
Clase `LiveKitHandler` que gestiona:
- Conexión con LiveKit Room
- Eventos de participantes
- Suscripción a tracks
- Procesamiento de participantes existentes

**Exporta:** `LiveKitHandler` (clase)

**Dependencias:**
- `Logger` (utils.js)
- `VideoHandler` (videoHandler.js)
- `AudioHandler` (audioHandler.js)
- `CONFIG` (config.js)

### `websocketHandler.js`
Clase `WebSocketHandler` que gestiona:
- Conexión WebSocket con el servidor
- Envío y recepción de mensajes
- Callbacks para diferentes tipos de eventos

**Exporta:** `WebSocketHandler` (clase)

**Dependencias:**
- `Logger` (utils.js)
- `CONFIG` (config.js)

### `app.js`
Clase principal `App` que:
- Inicializa todos los componentes
- Coordina el flujo de la aplicación
- Maneja eventos de botones
- Gestiona el ciclo de vida de la conversación

**Exporta:** Instancia de `App` (se auto-inicializa)

**Dependencias:**
- Todos los componentes anteriores

## � Flujo de Datos

1. **Inicio de Conversación**
   ```
   Usuario hace clic → App → WebSocketHandler → Servidor
   ```

2. **Avatar Listo**
   ```
   Servidor → WebSocketHandler → App → LiveKitHandler
   ```

3. **Streaming de Video**
   ```
   LiveKit → LiveKitHandler → VideoHandler → DOM
   ```

4. **Captura de Audio**
   ```
   Micrófono → AudioHandler → WebSocketHandler → Servidor
   ```

5. **Transcripciones**
   ```
   Servidor → WebSocketHandler → Logger → DOM
   ```

## �🚀 Uso

Simplemente abre `index_livekit.html` en un navegador moderno. Los componentes se cargarán en el orden correcto y la aplicación se inicializará automáticamente.

## 🔧 Modificaciones

Para modificar la configuración, edita el archivo `js/config.js`. Los cambios se aplicarán automáticamente sin necesidad de modificar otros archivos.

## 🐛 Debug

El botón "Debug Video" en la interfaz ejecuta diagnósticos del estado del video y fuerza la reproducción si es necesario.

## 📝 Notas

- Todos los componentes son modulares y reutilizables
- La separación de responsabilidades facilita el mantenimiento
- Los estilos están centralizados en `css/main.css`
- La configuración está separada del código lógico
- Cada componente tiene una responsabilidad única y bien definida
