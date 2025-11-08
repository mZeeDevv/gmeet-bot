# JavaScript Scripts for Google Meet Bot

This folder contains all JavaScript code used by the bot to interact with Google Meet's web interface.

## 📁 Scripts Overview

### `disable_webdriver_detection.js`
**Purpose**: Hide automation detection from Google Meet  
**Usage**: Executed once during browser setup  
**Returns**: Nothing (modifies navigator object)

### `disable_camera.js`
**Purpose**: Find and click the camera button to turn it off  
**Usage**: Fallback when Selenium can't find the camera button  
**Returns**: String status message

### `setup_virtual_microphone.js`
**Purpose**: Configure VB-Audio Cable as the microphone input  
**Usage**: Called before joining the meeting  
**Returns**: `success: [device name]` or `error: [message]`  
**Side Effects**: Creates `window.virtualMicStream` and `window.virtualMicId`

### `inject_virtual_mic_stream.js`
**Purpose**: Inject the virtual microphone stream into the active call  
**Usage**: Called after successfully joining the meeting  
**Returns**: `success: [track label]` or `error: [message]`  
**Dependencies**: Requires `window.virtualMicStream` from setup script

## 🔧 How to Use

### From Python:

```python
from bot.script_loader import get_script_loader

# Get the loader
loader = get_script_loader()

# Load a script (returns string)
script = loader.load('disable_camera')

# Execute a script (returns result)
result = loader.execute(driver, 'disable_camera')
```

## ✨ Benefits

1. **Separation of Concerns**: JavaScript logic is separate from Python code
2. **Easier Maintenance**: Edit JS files without touching Python
3. **Reusability**: Scripts can be used by multiple Python modules
4. **Better IDE Support**: Proper JavaScript syntax highlighting and linting
5. **Caching**: Scripts are cached in memory after first load
6. **Testability**: Scripts can be tested independently in browser console

## 📝 Adding New Scripts

1. Create a new `.js` file in this folder
2. Write your JavaScript code
3. Use `loader.execute(driver, 'your_script_name')` in Python
4. Document it in this README

## 🐛 Debugging

To test scripts in the browser console:
1. Open Google Meet in your browser
2. Press F12 to open DevTools
3. Copy script content from `.js` file
4. Paste and run in Console tab
5. Check the returned value

## 📋 Dependencies

- **VB-Audio Virtual Cable**: Required for virtual microphone functionality
- **Google Meet**: Scripts are designed specifically for Google Meet's DOM structure
- **Selenium WebDriver**: Used to execute scripts from Python
