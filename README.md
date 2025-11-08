# Fastn.ai Meet Bot

An intelligent AI-powered bot that joins Google Meet sessions, listens to questions using wake word detection, and provides instant answers from FASTN documentation using Google Gemini AI.

## Features

- **Wake Word Detection**: Responds when you say "okay assistant" or "ok assistant"
- **Fast Local Search**: Lightning-fast documentation search with heading-based relevance scoring
- **AI-Powered Responses**: Uses Google Gemini for intelligent, context-aware answers
- **Natural Voice**: Text-to-speech with clean, professional audio output
- **Real-time Dashboard**: Monitor bot activity and conversation history
- **Lobby Detection**: Automatically waits for host admission before joining
- **Auto Camera Off**: Automatically disables camera when joining meetings

## Prerequisites

1. **Python 3.11+**
2. **Microsoft Edge Browser** (for Selenium automation)
3. **Virtual Audio Cable** (for audio injection into Google Meet)

### Download Virtual Audio Cable

Virtual Audio Cable is required for the bot to speak in Google Meet sessions.

**Download Link**: [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)

**Installation Steps:**
1. Download VBCABLE_Driver_Pack43.zip
2. Extract and run `VBCABLE_Setup_x64.exe` (Run as Administrator)
3. Restart your computer after installation
4. Set "CABLE Input" as your default playback device in Windows Sound Settings

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/mZeeDevv/gmeet-bot.git
cd gmeet-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your Google Gemini API key:

```env
# Google Gemini API Key (Required)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

### 6. Run the Bot

```bash
cd src
python app.py
```

The dashboard will automatically open in your browser at `http://localhost:8080`

## Project Structure

```
fastn-bot/
├── src/
│   ├── app.py                          # Main entry point
│   ├── docs_content.json               # FASTN documentation database
│   ├── bot/
│   │   ├── meetbot.py                  # Main bot orchestrator
│   │   ├── meet_controller.py          # Browser automation
│   │   ├── audio_handler.py            # Speech recognition & TTS
│   │   ├── ai_responder.py             # Google Gemini integration
│   │   ├── fast_local_search.py        # Documentation search
│   │   ├── chat_sender.py              # Chat message sender
│   │   ├── script_loader.py            # JavaScript loader utility
│   │   └── scripts/                    # JavaScript files
│   │       ├── disable_webdriver_detection.js
│   │       ├── disable_camera.js
│   │       ├── setup_virtual_microphone.js
│   │       └── inject_virtual_mic_stream.js
│   ├── dashboard/
│   │   ├── dashboard.html              # Dashboard UI
│   │   ├── dashboard_server.py         # WebSocket server
│   │   └── bot_with_dashboard.py       # Bot with dashboard integration
│   └── crawlers/
│       └── improved_docs_crawler.py    # Documentation crawler
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment variables template
└── README.md
```

## How to Use

1. **Start the bot** using `python app.py`
2. The bot will automatically:
   - Open Google Meet in Microsoft Edge
   - Log in with your credentials
   - Wait in lobby if host hasn't admitted yet
   - Turn off camera automatically
   - Start listening for wake words

3. **Interact with the bot** in the meeting:
   - Say **"okay assistant"** or **"ok assistant"** followed by your question
   - Example: *"Okay assistant, how do I create a component in FASTN?"*
   - The bot will search documentation and respond with an AI-generated answer

4. **Monitor activity** on the dashboard:
   - View real-time bot status
   - See conversation history
   - Track questions and responses


## Development

### Updating Documentation Database

To refresh the FASTN documentation:

```bash
cd src/crawlers
python improved_docs_crawler.py
```

This will crawl `docs.fastn.ai` and update `docs_content.json`.

---

Made with <3 for Fastn.ai community
