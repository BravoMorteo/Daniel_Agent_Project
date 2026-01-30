/*
═══════════════════════════════════════════════════════════════════════
APP.JS - APLICACIÓN PRINCIPAL DEL FRONTEND
═══════════════════════════════════════════════════════════════════════

DESCRIPCIÓN:
    Orquestador principal de la aplicación. Coordina todos los módulos
    y maneja el flujo completo de la conversación con el avatar.

RESPONSABILIDADES:
    - Inicializar todos los handlers (audio, video, WebSocket, LiveKit)
    - Manejar eventos de UI (botones, clicks)
    - Coordinar el flujo de inicio y detención de la conversación
    - Mantener el estado de la sesión

FLUJO DE INICIO DE CONVERSACIÓN:
    1. Usuario hace click en "Iniciar"
    2. Conecta WebSocket con el servidor
    3. Servidor devuelve info de sesión (tokens LiveKit)
    4. Conecta a LiveKit para recibir video del avatar
    5. Inicia captura de audio del micrófono
    6. Conversación lista

MÓDULOS UTILIZADOS:
    - Logger: Sistema de logs visual en pantalla
    - VideoHandler: Manejo del canvas de video
    - AudioHandler: Captura de micrófono
    - LiveKitHandler: Conexión WebRTC
    - WebSocketHandler: Comunicación con servidor

AUTOR: BravoMorteo
FECHA: Enero 2026
═══════════════════════════════════════════════════════════════════════
*/

// ═══════════════════════════════════════════════════════════════════════
// CLASE PRINCIPAL
// ═══════════════════════════════════════════════════════════════════════

class App {
    constructor() {
        // ────────────────────────────────────────────────────────────
        // ELEMENTOS DEL DOM
        // ────────────────────────────────────────────────────────────
        // Obtener referencias a los elementos HTML
        this.videoElement = document.getElementById('videoElement');
        this.statusElement = document.getElementById('status');
        this.transcriptionElement = document.getElementById('transcription');
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.debugBtn = document.getElementById('debugBtn');

        // ────────────────────────────────────────────────────────────
        // INICIALIZAR HANDLERS
        // ────────────────────────────────────────────────────────────
        // Cada handler maneja una responsabilidad específica:
        
        // Logger: Muestra mensajes de estado y transcripciones
        this.logger = new Logger(this.statusElement, this.transcriptionElement);
        
        // VideoHandler: Renderiza el video del avatar en el canvas
        this.videoHandler = new VideoHandler(this.videoElement, this.logger);
        
        // AudioHandler: Captura audio del micrófono del usuario
        this.audioHandler = new AudioHandler(this.logger);
        
        // LiveKitHandler: Maneja la conexión WebRTC con LiveKit
        this.livekitHandler = new LiveKitHandler(
            this.logger,
            this.videoHandler,
            this.audioHandler
        );
        
        // ────────────────────────────────────────────────────────────
        // ESTADO DE LA APLICACIÓN
        // ────────────────────────────────────────────────────────────
        // sessionInfo: Contiene tokens y configuración de LiveKit
        this.sessionInfo = null;
        
        // wsHandler: Manejador de WebSocket (se crea al conectar)
        this.wsHandler = null;

        // ────────────────────────────────────────────────────────────
        // CONFIGURAR EVENTOS
        // ────────────────────────────────────────────────────────────
        this.setupEventListeners();
        this.logger.log('✅ Listo para comenzar');
    }

    /**
     * Configura los event listeners de los botones de la UI.
     * 
     * BOTONES:
     *   - Start: Inicia la conversación
     *   - Stop: Detiene la conversación
     *   - Debug: Muestra info de debug del video
     */
    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.startConversation());
        this.stopBtn.addEventListener('click', () => this.stopConversation());
        this.debugBtn.addEventListener('click', () => this.videoHandler.debug());
    }

    /**
     * Inicia el flujo completo de conversación.
     * 
     * PROCESO:
     *   1. Deshabilita el botón de inicio
     *   2. Crea el manejador de WebSocket con callbacks
     *   3. Conecta al servidor via WebSocket
     *   4. Servidor responde con info de sesión (callbacks manejan el resto)
     * 
     * CALLBACKS REGISTRADOS:
     *   - handleAvatarReady: Cuando el avatar está listo
     *   - handleElevenLabsConnected: Cuando ElevenLabs conecta
     *   - addTranscription: Para mostrar texto de usuario y agente
     * 
     * @throws {Error} Si falla la conexión WebSocket
     */
    async startConversation() {
        try {
            this.startBtn.disabled = true;
            this.logger.log('🚀 Iniciando conversación...');

            // Crear WebSocket handler con callbacks para manejar eventos
            this.wsHandler = new WebSocketHandler(
                this.logger,
                (data) => this.handleAvatarReady(data),      // Avatar listo
                () => this.handleElevenLabsConnected(),      // ElevenLabs conectado
                (text) => this.logger.addTranscription(text, 'user'),   // Usuario habló
                (text) => this.logger.addTranscription(text, 'agent')   // Agente respondió
            );

            // Conectar al servidor
            await this.wsHandler.connect();

        } catch (error) {
            this.logger.log(`❌ Error: ${error.message}`);
            this.startBtn.disabled = false;
        }
    }

    /**
     * Manejador: Avatar está listo para streaming.
     * 
     * PROCESO:
     *   1. Guarda la info de sesión (tokens, URLs)
     *   2. Conecta a LiveKit con los tokens recibidos
     *   3. Espera a que se establezca la conexión
     *   4. Notifica al servidor que estamos listos
     * 
     * Este método se llama cuando el servidor envía el mensaje
     * "avatar_ready" con los datos de la sesión de HeyGen.
     * 
     * @param {Object} data - Información de sesión
     *   @param {string} data.session_id - ID de sesión
     *   @param {string} data.token - Token de LiveKit
     *   @param {string} data.url - URL del servidor LiveKit
     */
    async handleAvatarReady(data) {
        this.sessionInfo = data;
        
        this.logger.log('🔗 Conectando a LiveKit...');
        
        // Iniciar conexión LiveKit y esperar a que esté lista
        await this.livekitHandler.connect(this.sessionInfo);
        
        // Esperar un momento adicional para que se procesen los tracks de video
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        this.logger.log('✅ LiveKit listo, notificando al servidor...');
        
        // Notificar al servidor que el cliente está listo para recibir audio
        this.wsHandler.sendJSON({ type: 'client_ready' });
    }

    /**
     * Manejador: ElevenLabs ConvAI conectado.
     * 
     * PROCESO:
     *   1. Inicia la captura de audio del micrófono
     *   2. El audio se envía automáticamente al servidor via WebSocket
     * 
     * Este método se llama cuando el servidor envía el mensaje
     * "elevenlabs_connected", indicando que el agente de IA está listo
     * para recibir audio del usuario.
     */
    async handleElevenLabsConnected() {
        // Iniciar captura de micrófono y conectar al WebSocket
        await this.audioHandler.startMicrophone(this.wsHandler.ws);
    }

    /**
     * Detiene la conversación y limpia todos los recursos.
     * 
     * PROCESO:
     *   1. Desconecta LiveKit (detiene video)
     *   2. Cierra WebSocket (detiene comunicación)
     *   3. Limpia handlers (libera micrófono, etc.)
     *   4. Resetea el estado
     *   5. Habilita el botón de inicio
     * 
     * IMPORTANTE: Siempre llama a este método para limpiar recursos
     * correctamente y evitar memory leaks.
     */
    async stopConversation() {
        this.logger.log('⏹️ Deteniendo conversación...');
        
        // Desconectar LiveKit (detiene streaming de video)
        this.livekitHandler.disconnect();
        
        // Cerrar WebSocket (detiene comunicación con servidor)
        if (this.wsHandler) {
            this.wsHandler.close();
            this.wsHandler = null;
        }
        
        // Limpiar handlers (libera recursos como micrófono)
        this.videoHandler.cleanup();
        this.audioHandler.cleanup();
        
        // Resetear estado
        this.sessionInfo = null;
        this.startBtn.disabled = false;
        
        this.logger.log('✅ Conversación detenida');
    }
}

// ═══════════════════════════════════════════════════════════════════════
// INICIALIZACIÓN
// ═══════════════════════════════════════════════════════════════════════
// Inicializar la aplicación cuando el DOM esté completamente cargado

document.addEventListener('DOMContentLoaded', () => {
    new App();
});
