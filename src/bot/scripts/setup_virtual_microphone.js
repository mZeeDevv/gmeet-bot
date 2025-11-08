// Setup virtual microphone (VB-Audio Cable Output) for Google Meet
(async function() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(d => d.kind === 'audioinput');
        console.log('Available audio inputs:', audioInputs.map(d => d.label));
        
        const virtualMic = audioInputs.find(d => 
            d.label.toLowerCase().includes('cable output') ||
            d.label.toLowerCase().includes('vb-audio virtual cable')
        );
        
        if (virtualMic) {
            window.virtualMicId = virtualMic.deviceId;
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: { 
                    deviceId: { exact: virtualMic.deviceId },
                    echoCancellation: false,
                    noiseSuppression: false,
                    autoGainControl: false
                }
            });
            window.virtualMicStream = stream;
            console.log('Virtual Microphone activated:', virtualMic.label);
            return 'success: ' + virtualMic.label;
        } else {
            return 'error: Virtual microphone not found. Available: ' + audioInputs.map(d => d.label).join(', ');
        }
    } catch(e) {
        return 'error: ' + e.message;
    }
})();
