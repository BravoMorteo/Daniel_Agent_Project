// Utility functions
class Logger {
    constructor(statusElement, transcriptionElement) {
        this.statusElement = statusElement;
        this.transcriptionElement = transcriptionElement;
    }

    log(msg) {
        const time = new Date().toLocaleTimeString();
        this.statusElement.innerHTML += `[${time}] ${msg}<br>`;
        this.statusElement.scrollTop = this.statusElement.scrollHeight;
        console.log(msg);
    }

    addTranscription(text, type = 'user') {
        const color = type === 'user' ? '#0066cc' : '#cc0000';
        const prefix = type === 'user' ? '👤 Tú' : '🤖 IA';
        this.transcriptionElement.innerHTML += `<p style="color:${color}"><strong>${prefix}:</strong> ${text}</p>`;
    }
}
