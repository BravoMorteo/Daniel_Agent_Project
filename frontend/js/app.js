// Main Application
class App {
    constructor() {
        // DOM elements
        this.videoElement = document.getElementById('videoElement');
        this.statusElement = document.getElementById('status');
        this.transcriptionElement = document.getElementById('transcription');
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.debugBtn = document.getElementById('debugBtn');

        // Handlers
        this.logger = new Logger(this.statusElement, this.transcriptionElement);
        this.videoHandler = new VideoHandler(this.videoElement, this.logger);
        this.audioHandler = new AudioHandler(this.logger);
        this.livekitHandler = new LiveKitHandler(this.logger, this.videoHandler, this.audioHandler);
        
        // State
        this.sessionInfo = null;
        this.wsHandler = null;

        // Setup event listeners
        this.setupEventListeners();
        this.logger.log('✅ Listo para comenzar');
    }

    setupEventListeners() {
        this.startBtn.addEventListener('click', () => this.startConversation());
        this.stopBtn.addEventListener('click', () => this.stopConversation());
        this.debugBtn.addEventListener('click', () => this.videoHandler.debug());
    }

    async startConversation() {
        try {
            this.startBtn.disabled = true;
            this.logger.log('🚀 Iniciando conversación...');

            // Crear WebSocket handler con callbacks
            this.wsHandler = new WebSocketHandler(
                this.logger,
                (data) => this.handleAvatarReady(data),
                () => this.handleElevenLabsConnected(),
                (text) => this.logger.addTranscription(text, 'user'),
                (text) => this.logger.addTranscription(text, 'agent')
            );

            await this.wsHandler.connect();

        } catch (error) {
            this.logger.log(`❌ Error: ${error.message}`);
            this.startBtn.disabled = false;
        }
    }

    async handleAvatarReady(data) {
        this.sessionInfo = data;
        
        this.logger.log('🔗 Conectando a LiveKit...');
        
        // Iniciar LiveKit y esperar a que esté completamente conectado
        await this.livekitHandler.connect(this.sessionInfo);
        
        // Esperar un momento adicional para que se procesen los tracks
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        this.logger.log('✅ LiveKit listo, notificando al servidor...');
        
        // Notificar al servidor que estamos listos
        this.wsHandler.sendJSON({ type: 'client_ready' });
    }

    async handleElevenLabsConnected() {
        // Iniciar captura de micrófono
        await this.audioHandler.startMicrophone(this.wsHandler.ws);
    }

    async stopConversation() {
        this.logger.log('⏹️ Deteniendo conversación...');
        
        // Disconnect LiveKit
        this.livekitHandler.disconnect();
        
        // Close WebSocket
        if (this.wsHandler) {
            this.wsHandler.close();
            this.wsHandler = null;
        }
        
        // Cleanup handlers
        this.videoHandler.cleanup();
        this.audioHandler.cleanup();
        
        // Reset state
        this.sessionInfo = null;
        this.startBtn.disabled = false;
        
        this.logger.log('✅ Conversación detenida');
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new App();
});
