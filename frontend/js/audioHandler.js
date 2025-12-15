// Audio Handler
class AudioHandler {
    constructor(logger) {
        this.logger = logger;
        this.audioContext = null;
        this.processor = null;
        this.stream = null;
    }

    async startMicrophone(wsClient) {
        try {
            this.logger.log('🎤 Solicitando micrófono...');
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: CONFIG.audio
            });
            
            this.logger.log('✅ Micrófono capturado');
            
            // Crear procesador de audio
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: CONFIG.audio.sampleRate
            });
            const source = this.audioContext.createMediaStreamSource(this.stream);
            this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);

            source.connect(this.processor);
            this.processor.connect(this.audioContext.destination);

            this.processor.onaudioprocess = (e) => {
                if (wsClient && wsClient.readyState === WebSocket.OPEN) {
                    const inputData = e.inputBuffer.getChannelData(0);
                    
                    // Convertir a PCM16
                    const pcm16 = new Int16Array(inputData.length);
                    for (let i = 0; i < inputData.length; i++) {
                        const s = Math.max(-1, Math.min(1, inputData[i]));
                        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                    }
                    
                    // Enviar al servidor
                    wsClient.send(pcm16.buffer);
                }
            };

            this.logger.log('🎙️ Captura de audio activa');
            
        } catch (error) {
            this.logger.log(`❌ Error de micrófono: ${error.message}`);
        }
    }

    attachAudioTrack(track) {
        const audioElement = track.attach();
        audioElement.autoplay = true;
        document.body.appendChild(audioElement);
        this.logger.log(`🔊 Audio reproduciendo`);
        return audioElement;
    }

    cleanup() {
        if (this.processor) {
            this.processor.disconnect();
            this.processor = null;
        }
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }
}
