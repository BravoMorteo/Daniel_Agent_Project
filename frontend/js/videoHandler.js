// Video Handler
class VideoHandler {
    constructor(videoElement, logger) {
        this.videoElement = videoElement;
        this.logger = logger;
        this.initialElement = videoElement; // Guardar referencia inicial
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Limpiar listeners previos si existen
        const element = this.videoElement;
        
        element.addEventListener('loadstart', () => this.logger.log('🎬 Video: loadstart'));
        element.addEventListener('loadedmetadata', () => this.logger.log('📊 Video: metadata cargada'));
        element.addEventListener('loadeddata', () => this.logger.log('📦 Video: data cargada'));
        element.addEventListener('canplay', () => this.logger.log('▶️ Video: can play'));
        element.addEventListener('canplaythrough', () => this.logger.log('⏩ Video: can play through'));
        element.addEventListener('playing', () => this.logger.log('🎥 Video: REPRODUCIENDO'));
        element.addEventListener('error', (e) => {
            this.logger.log(`❌ Video ERROR: ${e.message || 'Unknown error'}`);
            if (element.error) {
                this.logger.log(`   Code: ${element.error.code}, Message: ${element.error.message}`);
            }
        });
        element.addEventListener('stalled', () => this.logger.log('⏸️ Video: stalled'));
        element.addEventListener('waiting', () => this.logger.log('⏳ Video: waiting'));
    }

    attachTrack(track, participant) {
        this.logger.log(`📺 Track recibido de ${participant.identity}: ${track.kind}`);
        
        try {
            // Usar el método attach() de LiveKit que retorna un elemento configurado
            const element = track.attach();
            
            // Log de diagnóstico
            this.logger.log(`🔍 Video creado: readyState=${element.readyState}`);
            this.logger.log(`🔍 srcObject: ${element.srcObject ? 'OK' : 'NULL'}`);
            if (element.srcObject) {
                const tracks = element.srcObject.getTracks();
                this.logger.log(`🔍 Tracks: ${tracks.length} (${tracks.map(t => t.kind).join(', ')})`);
            }
            
            // Configurar propiedades
            element.autoplay = true;
            element.playsInline = true;
            element.muted = true; // MUTED para video (el audio va por separado)
            element.style.display = 'block';
            element.style.width = '100%';
            element.style.height = '100%';
            element.style.objectFit = 'cover';
            element.style.backgroundColor = '#000';
            
            // REEMPLAZAR el elemento completo en el DOM
            const oldElement = this.videoElement;
            if (oldElement && oldElement.parentNode) {
                oldElement.parentNode.replaceChild(element, oldElement);
                element.id = oldElement.id;
                this.videoElement = element;
                this.logger.log(`✅ Video element REEMPLAZADO en DOM`);
                
                // Re-configurar event listeners en el nuevo elemento
                this.setupEventListeners();
            }
            
            // Forzar reproducción
            setTimeout(() => {
                this.logger.log(`🔄 Forzando play... readyState=${element.readyState}`);
                element.play().then(() => {
                    this.logger.log('✅ Play forzado exitoso');
                }).catch(e => {
                    this.logger.log(`⚠️ Play forzado falló: ${e.message}`);
                });
            }, 500);
            
        } catch (error) {
            this.logger.log(`❌ Error en attachTrack: ${error.message}`);
        }
    }

    setupDiagnosticEvents(element) {
        element.addEventListener('loadstart', () => {
            this.logger.log(`🎬 Video: loadstart (readyState=${element.readyState})`);
        });
        element.addEventListener('loadedmetadata', () => {
            this.logger.log(`📐 Metadata cargada: ${element.videoWidth}x${element.videoHeight}`);
        });
        element.addEventListener('canplay', () => {
            this.logger.log('✅ Video: canplay - intentando play...');
            element.play().catch(e => this.logger.log(`❌ Play falló: ${e.message}`));
        });
        element.addEventListener('playing', () => {
            this.logger.log('▶️ Video: PLAYING!');
        });
        element.addEventListener('waiting', () => this.logger.log('⏳ Video: waiting'));
        element.addEventListener('stalled', () => this.logger.log('⚠️ Video: stalled'));
        element.addEventListener('suspend', () => this.logger.log('⏸️ Video: suspend'));
        element.addEventListener('error', (e) => {
            this.logger.log(`❌ Video error: ${e.target.error?.message || 'unknown'}`);
        });
    }

    debug() {
        this.logger.log('🔍 ========== DEBUG VIDEO INFO ==========');
        this.logger.log(`📺 Video element: ${this.videoElement ? 'EXISTS' : 'MISSING'}`);
        
        if (this.videoElement) {
            this.logger.log(`🔍 ID: ${this.videoElement.id}`);
            this.logger.log(`🔍 srcObject: ${this.videoElement.srcObject ? 'ASSIGNED' : 'NULL'}`);
            
            if (this.videoElement.srcObject) {
                const tracks = this.videoElement.srcObject.getTracks();
                this.logger.log(`🔍 Total tracks: ${tracks.length}`);
                tracks.forEach((track, i) => {
                    this.logger.log(`  Track ${i}: ${track.kind} - ${track.enabled ? 'enabled' : 'disabled'} - ${track.readyState}`);
                });
            }
            
            this.logger.log(`🔍 readyState: ${this.videoElement.readyState} (0=HAVE_NOTHING, 1=HAVE_METADATA, 2=HAVE_CURRENT_DATA, 3=HAVE_FUTURE_DATA, 4=HAVE_ENOUGH_DATA)`);
            this.logger.log(`🔍 paused: ${this.videoElement.paused}`);
            this.logger.log(`🔍 muted: ${this.videoElement.muted}`);
            this.logger.log(`🔍 autoplay: ${this.videoElement.autoplay}`);
            this.logger.log(`🔍 playsinline: ${this.videoElement.playsInline}`);
            this.logger.log(`🔍 dimensions: ${this.videoElement.videoWidth}x${this.videoElement.videoHeight}`);
            this.logger.log(`🔍 display: ${window.getComputedStyle(this.videoElement).display}`);
        }
        
        this.logger.log('🔍 ====================================');
        
        // Intentar forzar play
        if (this.videoElement && this.videoElement.srcObject) {
            this.logger.log('🎬 Intentando forzar play...');
            this.videoElement.play().then(() => {
                this.logger.log('✅ Video play() exitoso');
            }).catch(e => {
                this.logger.log(`❌ Video play() falló: ${e.message}`);
                this.logger.log('🔇 Intentando con muted=true...');
                this.videoElement.muted = true;
                this.videoElement.play().catch(err => {
                    this.logger.log(`❌ Play con muted también falló: ${err.message}`);
                });
            });
        } else {
            this.logger.log('⚠️ No hay srcObject para reproducir');
        }
    }

    cleanup() {
        if (this.videoElement.srcObject) {
            this.videoElement.srcObject.getTracks().forEach(track => track.stop());
            this.videoElement.srcObject = null;
        }
    }
}
