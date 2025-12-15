// LiveKit Handler
class LiveKitHandler {
    constructor(logger, videoHandler, audioHandler) {
        this.logger = logger;
        this.videoHandler = videoHandler;
        this.audioHandler = audioHandler;
        this.room = null;
    }

    async connect(sessionInfo) {
        try {
            this.logger.log('🔗 Configurando LiveKit...');
            
            // Crear LiveKit Room
            this.room = new LivekitClient.Room(CONFIG.livekit);

            this.setupEventHandlers();

            // Conectar a LiveKit
            await this.room.connect(sessionInfo.url, sessionInfo.access_token);
            this.logger.log('✅ Conectado a LiveKit Room');
            
            // Procesar participantes existentes
            this.processExistingParticipants();

        } catch (error) {
            this.logger.log(`❌ Error LiveKit: ${error.message}`);
            throw error;
        }
    }

    setupEventHandlers() {
        // Manejar PARTICIPANTES remotos
        this.room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            this.logger.log(`📺 Track recibido: ${track.kind} de ${participant.identity}`);
            
            if (track.kind === 'video') {
                this.logger.log(`🎥 Adjuntando video track...`);
                this.videoHandler.attachTrack(track, participant);
            }
            
            if (track.kind === 'audio') {
                this.logger.log(`🔊 Adjuntando audio track...`);
                this.audioHandler.attachAudioTrack(track);
            }
        });

        this.room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track, publication, participant) => {
            this.logger.log(`🔴 Track removido de ${participant.identity}: ${track.kind}`);
            track.detach();
        });

        this.room.on(LivekitClient.RoomEvent.Disconnected, (reason) => {
            this.logger.log(`🔴 LiveKit desconectado: ${reason}`);
        });

        this.room.on(LivekitClient.RoomEvent.ParticipantConnected, (participant) => {
            this.logger.log(`👥 Participante conectado: ${participant.identity}`);
        });

        this.room.on(LivekitClient.RoomEvent.MediaDevicesError, (error) => {
            this.logger.log(`❌ Error de dispositivos: ${error}`);
        });

        this.room.on(LivekitClient.RoomEvent.ConnectionQualityChanged, (quality, participant) => {
            this.logger.log(`📶 Calidad conexión: ${quality}`);
        });
    }

    processExistingParticipants() {
        // Verificar que participants existe y tiene métodos
        if (!this.room || !this.room.remoteParticipants) {
            this.logger.log('⚠️  room.remoteParticipants no disponible');
            return;
        }

        // Obtener los participantes remotos (el avatar de HeyGen)
        const participants = Array.from(this.room.remoteParticipants.values());
        const participantCount = participants.length;
        
        this.logger.log(`👥 Procesando ${participantCount} participantes remotos existentes`);
        
        if (participantCount === 0) {
            this.logger.log('⚠️  No hay participantes remotos aún (avatar aún no se unió al room)');
            return;
        }
        
        participants.forEach((participant) => {
            this.logger.log(`👥 Procesando participante: ${participant.identity}`);
            
            // Obtener las publicaciones de tracks
            const publications = Array.from(participant.trackPublications.values());
            this.logger.log(`📊 Participante tiene ${publications.length} publicaciones`);
            
            publications.forEach((publication) => {
                this.logger.log(`📡 Track: ${publication.trackName}, kind: ${publication.kind}, subscrito: ${publication.isSubscribed}`);
                
                if (publication.isSubscribed && publication.track) {
                    this.logger.log(`📺 Track disponible: ${publication.track.kind}`);
                    
                    if (publication.track.kind === 'video') {
                        this.videoHandler.attachTrack(publication.track, participant);
                    }
                    
                    if (publication.track.kind === 'audio') {
                        this.audioHandler.attachAudioTrack(publication.track);
                        this.logger.log(`🔊 Audio configurado (participante existente)`);
                    }
                }
            });
        });
    }

    disconnect() {
        if (this.room) {
            this.room.disconnect();
            this.room = null;
        }
    }
}
