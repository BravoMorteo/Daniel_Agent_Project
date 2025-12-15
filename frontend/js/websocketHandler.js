// WebSocket Handler
class WebSocketHandler {
    constructor(logger, onAvatarReady, onElevenLabsConnected, onUserTranscript, onAgentResponse) {
        this.logger = logger;
        this.ws = null;
        this.onAvatarReady = onAvatarReady;
        this.onElevenLabsConnected = onElevenLabsConnected;
        this.onUserTranscript = onUserTranscript;
        this.onAgentResponse = onAgentResponse;
    }

    connect() {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(CONFIG.websocket.url);
            
            this.ws.onopen = () => {
                this.logger.log('✅ Conectado al servidor');
                resolve();
            };

            this.ws.onmessage = async (event) => {
                const data = JSON.parse(event.data);
                
                switch(data.type) {
                    case 'avatar_ready':
                        this.logger.log(`✅ Avatar creado: ${data.session_id}`);
                        this.onAvatarReady(data);
                        break;
                    case 'elevenlabs_connected':
                        this.logger.log('✅ ElevenLabs conectado');
                        this.onElevenLabsConnected();
                        break;
                    case 'user_transcript':
                        this.onUserTranscript(data.text);
                        break;
                    case 'agent_response':
                        this.onAgentResponse(data.text);
                        break;
                }
            };

            this.ws.onerror = (error) => {
                this.logger.log(`❌ Error WebSocket: ${error}`);
                reject(error);
            };

            this.ws.onclose = () => {
                this.logger.log('🔴 Conexión cerrada');
            };
        });
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(message);
        }
    }

    sendJSON(data) {
        this.send(JSON.stringify(data));
    }

    close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    get readyState() {
        return this.ws ? this.ws.readyState : WebSocket.CLOSED;
    }

    get isOpen() {
        return this.readyState === WebSocket.OPEN;
    }
}
