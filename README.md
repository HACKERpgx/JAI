# JAI - Your Personal AI Assistant

**JAI** (Just an Assistant, Intelligent) is a modular, networked personal assistant inspired by Jarvis. JAI combines polite, calm, and witty personality with powerful operational capabilities.

## Features

### Core Functions ✓
- **Weather Updates**: Real-time weather data with caching
- **News Headlines**: Top news from NewsAPI
- **Memory System**: Short-term and long-term context awareness
- **Multi-language Support**: Translate responses to Hindi, Urdu, Arabic, Russian, Spanish
- **Text-to-Speech**: Optional spoken responses with voice customization
- **PC Control**: Open apps, lock screen, and more (admin-restricted)
- **Networked API**: FastAPI server with HTTP Basic Auth

### Advanced Features (In Progress)
- **Voice Commands**: Speech recognition with wake word detection
- **Music & YouTube Control**: Play, pause, search, and control media
- **Calendar & Reminders**: Schedule events with alerts
- **Windows Startup Service**: Auto-launch on boot
- **Custom Voice Packs**: Personalize JAI's tone

### Personality
JAI is designed to be:
- **Polite**: Professional and respectful
- **Calm**: Measured responses, never rushed
- **Witty**: Occasional humor and charm

## Installation

### 1. Clone or Download
```bash
cd "C:\Users\Abdul Rahman\Documents\JAI_Assistant"
```

### 2. Create Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the project root:

```env
# Required
OPENAI_API_KEY=your_openrouter_api_key_here

# Optional
OPENWEATHER_API_KEY=your_weather_api_key
NEWS_API_KEY=your_newsapi_key

# Speech (set to true to enable spoken responses)
SPEAK_RESPONSES=false
TTS_VOICE=David
```

**Get API Keys:**
- OpenAI (via OpenRouter): https://openrouter.ai/
- Weather: https://openweathermap.org/api
- News: https://newsapi.org/

## Usage

### Start the Server
```powershell
python jai_assistant.py
```

Server runs on `http://0.0.0.0:8000`

### Send Commands (HTTP)
```powershell
curl -u user1:pass1 -X POST http://localhost:8000/command `
  -H "Content-Type: application/json" `
  -d '{"command": "weather in Dubai"}'
```

### Example Commands
- `"weather in Canada"`
- `"news"`
- `"my name is Abdul"`
- `"remember my favorite color is blue"`
- `"recall favorite color"`
- `"open calculator"`
- `"lock screen"` (admin only)
- `"speak hindi"` (switch to Hindi responses)

## Architecture

```
JAI_Assistant/
├── jai_assistant.py       # Main FastAPI server & command executor
├── personality.py         # Personality prompt builder & quips
├── tts.py                 # Text-to-speech module
├── memory.py              # Short/long-term memory (SQLite)
├── jai_controls.py        # PC control commands
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (API keys, settings)
└── README.md              # This file
```

## Modules

### `personality.py`
Centralizes JAI's tone and prompt generation. Ensures consistent polite, calm, witty responses.

### `tts.py`
Safe text-to-speech with:
- Voice selection (male/female, by name)
- Timeout protection
- Non-blocking operation

### `memory.py`
SQLite-backed memory:
- **Short-term**: Recent conversation context
- **Long-term**: User preferences, facts (with importance scoring)

### `jai_controls.py`
System control commands:
- Open applications (Notepad, Calculator, Chrome, etc.)
- Future: Volume, media playback, shutdown/restart

## Security

- **HTTP Basic Auth**: Username/password required for all commands
- **Admin Restrictions**: Sensitive commands (shutdown, lock) require admin role
- **API Key Protection**: Store keys in `.env`, never commit to version control
- **Logging**: All commands logged with user attribution

## Roadmap

### High Priority
- [ ] Speech-to-Text (STT) module with wake word
- [ ] Media controls (volume, play/pause, YouTube)
- [ ] Calendar & reminders with APScheduler
- [ ] Windows startup service

### Medium Priority
- [ ] Plugin system for extensibility
- [ ] Enhanced memory with semantic search
- [ ] Multi-device sync (cloud storage)
- [ ] Web dashboard UI

### Future Extensions
- [ ] IoT & smart home integration
- [ ] Secure password manager
- [ ] Finance advisor plugin
- [ ] Study helper & coding assistant plugins

## Troubleshooting

### TTS Not Working
- Ensure `pyttsx3` is installed: `pip install pyttsx3`
- Check available voices: Run `test_tts.py`
- Set `SPEAK_RESPONSES=true` in `.env`

### Speech Recognition Issues
- Install PyAudio: `pip install pyaudio` (may require Microsoft C++ Build Tools)
- Test microphone: Run `test_speech.py`

### API Errors
- Verify API keys in `.env`
- Check internet connection
- Review `jai_assistant.log` for details

## Contributing

JAI is designed to be modular and extensible. To add features:
1. Create a new module (e.g., `jai_media.py`)
2. Add intent patterns in `classify_intent()`
3. Handle the intent in `execute_command()`
4. Update `requirements.txt` if new dependencies are needed

## License

Personal project - feel free to adapt and extend for your own use.

## Credits

Built with:
- OpenAI GPT-4o-mini (via OpenRouter)
- FastAPI
- pyttsx3
- SpeechRecognition
- deep-translator

---

**JAI**: *"Just for you, I've polished my circuits to shine!"*
