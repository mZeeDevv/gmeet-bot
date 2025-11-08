// Find and click camera button to turn it off
const buttons = document.querySelectorAll('button');
for (let btn of buttons) {
    const label = btn.getAttribute('aria-label') || '';
    if (label.toLowerCase().includes('camera')) {
        if (label.toLowerCase().includes('turn off') || 
            (label.toLowerCase().includes('camera') && !label.toLowerCase().includes('off'))) {
            btn.click();
            return 'Camera turned OFF via JavaScript';
        } else if (label.toLowerCase().includes('turn on') || label.toLowerCase().includes('off')) {
            return 'Camera already OFF';
        }
    }
}
return 'Camera button not found';
