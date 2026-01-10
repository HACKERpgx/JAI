# JAI Quick Start Guide

Get JAI up and running in 5 minutes!

## Prerequisites

- Windows 10/11
- Python 3.8 or higher
- Microphone (for voice commands)
- Internet connection

## Step 1: Install Dependencies

Open PowerShell in the JAI_Assistant directory:

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

**Note**: If you encounter issues with `pyaudio`, you may need to install it separately:
```powershell
pip install pipwin
pipwin install pyaudio
```

## Step 2: Configure API Keys

1. Copy the template:
   ```powershell
   Copy-Item .env.template .env
   ```

2. Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openrouter_key_here
   NEWS_API_KEY=your_newsapi_key_here
   SPEAK_RESPONSES=true
   TTS_VOICE=David
   ```

**Get API Keys:**
- OpenRouter (OpenAI): https://openrouter.ai/keys
- NewsAPI: https://newsapi.org/register

## Step 3: Test the Setup

### Test TTS (Text-to-Speech)
```powershell
python test_tts.py
```
You should hear JAI speak!

### Test STT (Speech-to-Text)
```powershell
python test_speech.py
```
Speak when prompted to test your microphone.

## Step 4: Start JAI

### Option A: Server Mode (HTTP API)
```powershell
python jai_assistant.py
```
Server runs on `http://localhost:8000`

Test with:
```powershell
curl -u user1:pass1 -X POST http://localhost:8000/command `
  -H "Content-Type: application/json" `
  -d '{"command": "weather in Dubai"}'
```

### Option B: Voice Client (Recommended)
```powershell
# In one terminal, start the server
python jai_assistant.py

# In another terminal, start the voice client
python voice_client.py
```

Now say: **"Hey JAI"** followed by your command!

### Option C: Quick Start Script
```powershell
.\start_jai.ps1
```

## Step 5: Try Some Commands

Once JAI is listening, try:

- **"Hey JAI, what's the weather in Toronto?"**
- **"Hey JAI, remind me to call mom in 30 minutes"**
- **"Hey JAI, set volume to 50"**
- **"Hey JAI, play Bohemian Rhapsody on YouTube"**
- **"Hey JAI, open calculator"**
- **"Hey JAI, my name is Abdul"**
- **"Hey JAI, what's the news?"**

## Step 6: Auto-Start on Windows (Optional)

To make JAI start automatically when you log in:

```powershell
# Run PowerShell as Administrator
.\setup_windows_startup.ps1

# To remove auto-start
.\setup_windows_startup.ps1 -Remove
```

## Troubleshooting

### "Module not found" errors
```powershell
pip install -r requirements.txt
```

### TTS not working
- Check available voices: `python test_tts.py`
- Set `SPEAK_RESPONSES=true` in `.env`
- Try different voice: `TTS_VOICE=Zira` or `TTS_VOICE=David`

### Microphone not detected
- Check Windows microphone permissions
- Test with: `python test_speech.py`
- Install PyAudio: `pip install pyaudio`

### "Cannot connect to JAI server"
- Make sure the server is running: `python jai_assistant.py`
- Check the URL in `.env`: `JAI_SERVER=http://localhost:8000`

### Authentication failed
- Check credentials in `.env`:
  ```env
  JAI_USERNAME=user1
  JAI_PASSWORD=pass1
  ```

## File Structure

```
JAI_Assistant/
├── jai_assistant.py       # Main server
├── voice_client.py        # Voice interface
├── personality.py         # Personality & tone
├── tts.py                 # Text-to-speech
├── stt.py                 # Speech-to-text
├── memory.py              # Memory system
├── jai_controls.py        # PC controls
├── jai_media.py           # Media controls
├── jai_calendar.py        # Calendar & reminders
├── .env                   # Your configuration
└── requirements.txt       # Dependencies
```

## Next Steps

1. **Customize Personality**: Edit `personality.py` to change JAI's tone
2. **Add Custom Commands**: Extend `jai_assistant.py` with new intents
3. **Create Plugins**: Build custom modules for specific tasks
4. **Multi-device Setup**: Run voice client on one PC, server on another

## Usage Modes

### 1. Server Only (API)
Best for: Integration with other apps, web dashboards
```powershell
python jai_assistant.py
```

### 2. Voice Client
Best for: Hands-free interaction, Jarvis-like experience
```powershell
python jai_assistant.py  # Terminal 1
python voice_client.py   # Terminal 2
```

### 3. Background Service
Best for: Always-on assistant
```powershell
.\setup_windows_startup.ps1
```

## Tips

- **Wake Word**: Change `WAKE_WORD` in `.env` to customize
- **Continuous Mode**: Voice client runs continuously by default
- **Single Command**: `python voice_client.py --single` for one-shot commands
- **Logs**: Check `jai_assistant.log` and `voice_client.log` for debugging

## Support

Check these files for more info:
- `README.md` - Full documentation
- `IMPLEMENTATION_STATUS.md` - Feature status
- `.env.template` - All configuration options

---

**You're all set! Enjoy your personal AI assistant!** 🚀
