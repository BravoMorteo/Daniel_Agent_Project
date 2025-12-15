// Configuration
const CONFIG = {
    websocket: {
        url: 'ws://localhost:8000/hybrid'
    },
    audio: {
        echoCancellation: true,
        noiseSuppression: true,
        sampleRate: 16000
    },
    livekit: {
        adaptiveStream: true,
        dynacast: true,
        videoCaptureDefaults: {
            resolution: LivekitClient.VideoPresets.h720.resolution
        }
    }
};
