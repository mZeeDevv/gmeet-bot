// Inject virtual microphone stream into active Google Meet call
(async function() {
    try {
        if (!window.virtualMicStream) {
            return 'error: Virtual mic stream not found';
        }
        
        const stream = window.virtualMicStream;
        const audioTrack = stream.getAudioTracks()[0];
        
        if (audioTrack) {
            console.log('Injecting virtual mic track:', audioTrack.label);
            return 'success: Audio track injected - ' + audioTrack.label;
        } else {
            return 'error: No audio track found';
        }
    } catch(e) {
        return 'error: ' + e.message;
    }
})();
