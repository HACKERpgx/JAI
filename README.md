# JAI - Your Personal AI Assistant

**JAI** (Just an Assistant, Intelligent) is a modular, networked personal assistant inspired by Jarvis. JAI combines polite, calm, and witty personality with powerful operational capabilities.

## Why JAI

JAI is a self-hosted, local-first assistant that runs on your Windows PC via FastAPI. It emphasizes privacy, extensibility, and practical day-to-day usefulness.

- Local-first and private: Run the server on your own machine. Protect credentials in `.env`; no secrets in version control.
- Modular and extensible: Clear modules for personality, memory, TTS, controls, and APIs. Easy to add new intents and skills.
- Built-in memory system: Short-term and long-term memory (SQLite) with importance scoring and search.
- Multi-language out of the box: Translate responses to Hindi, Urdu, Arabic, Russian, and Spanish.
- Voice-ready: Text-to-Speech with configurable voice; voice commands on the roadmap.
- PC & media control: Open apps, lock screen, and more; media controls and YouTube integration are planned/available depending on your branch.
- Secure by default: HTTP Basic Auth for all commands; environment-based configuration for API keys.
- Observability: Commands are logged with user attribution for audits and debugging.

### Better localization
- Translate responses into key languages without changing your workflow.
- Keep tone consistent via the personality module while adapting to user language preferences.
- Run locally to respect regional data residency preferences.

### Superior privacy & control
- Host the assistant on your machine or LAN.
- Use Basic Auth and store keys in `.env`.
- Keep long-term memory local in SQLite; logs provide a clear audit trail.

## Business Benefits
JAI can drive measurable outcomes across operations, support, and revenue enablement.

- Cost reduction
  - Consolidate multiple assistant/SaaS tools into one local service.
  - Reduce external API usage by caching and only calling what you need.
  - Simpler IT surface area (single venv + `.env`), fewer vendor lock-ins.
  - Example KPIs to track: monthly API spend, number of SaaS seats replaced, average time per routine task.

- Automation
  - Automate repetitive desktop tasks (open apps, run commands), information pulls (weather, news), and daily summaries.
  - Expand with intents for reminders, media control, and more as needed.
  - Example KPIs: tasks automated per week, minutes saved per user, number of manual steps removed.

- Customer service improvement
  - Multilingual responses (Hindi/Urdu/Arabic/Russian/Spanish) for internal helpdesks or branches.
  - Consistent, polite tone via the personality module; quick responses via HTTP endpoints.
  - Example KPIs: first-response time, CSAT, average resolution time.

- Sales growth enablement
  - Draft outreach snippets, summarize news, and generate spoken prompts with TTS.
  - Assist with research and content prep; integrate lightweightly with desktop workflows.
  - Example KPIs: meeting booking rate, opportunity creation rate, time-to-first-touch.

### Business Impact Examples

- Cost reduction
  - Consolidate overlapping SaaS assistants into JAI and reduce external API calls via caching and selective requests.
  - Example: 10 users × 2 tools at $15/user/mo ≈ $300/mo saved; API optimizations cut $300 → $150–$210/mo.
  - Track: monthly API spend, SaaS seats replaced, cost per automated task.

- Automation
  - Automate routine desktop tasks (open apps, run commands), info pulls (weather/news), and daily summaries.
  - Example: 8 tasks/day × 1.5 min × 10 users ≈ 120 min/day → ~40 h/month. At $20/h ≈ $800/mo saved.
  - Track: tasks automated/week, minutes saved/user, manual steps removed.

- Customer service improvement
  - Multilingual responses (Hindi/Urdu/Arabic/Russian/Spanish) and consistent tone improve speed and quality.
  - Example: First-response time 15 → 5 min; CSAT +5–10 pts with quicker, clearer answers.
  - Track: FRT, CSAT, average resolution time.

- Sales growth enablement
  - Draft outreach snippets, summarize news, and generate spoken prompts with TTS to speed prep.
  - Example: +5% meetings booked (e.g., 20 → 21/mo). With 20% win rate and $500 margin/deal ≈ +$100 MRR.
  - Track: meeting booking rate, opportunity creation rate, time-to-first-touch.

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
