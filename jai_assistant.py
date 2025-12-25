import os
import pathlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
import requests
import re
try:
    from fuzzywuzzy import fuzz
except ImportError:
    from difflib import SequenceMatcher
    class _Fuzz:
        @staticmethod
        def partial_ratio(a, b):
            a = a or ""
            b = b or ""
            return int(SequenceMatcher(None, a, b).ratio() * 100)
    fuzz = _Fuzz()
import subprocess
import random
import logging
from logging.handlers import RotatingFileHandler
import threading
import queue
import json
import uuid
import contextvars
import time
from contextlib import asynccontextmanager

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import sympy as sp
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
except Exception:
    sp = None
    parse_expr = None
    standard_transformations = None
    implicit_multiplication_application = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None
try:
    import pyautogui
except ImportError:
    pyautogui = None
try:
    import win32gui, win32process, win32con, win32clipboard
except Exception:
    win32gui = None
    win32process = None
    win32con = None
    win32clipboard = None

from typing import Optional, Dict, Any, List, Tuple
from fastapi import FastAPI, HTTPException, Request, Depends, Header, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import APIRouter
from pydantic import BaseModel

# Language support
LANGUAGES = {
    'en': {'name': 'English', 'flag': 'ðŸ‡¬ðŸ‡§'},
    'ur': {'name': 'Urdu', 'flag': 'ðŸ‡µðŸ‡°'},
    'ar': {'name': 'Arabic', 'flag': 'ðŸ‡¸ðŸ‡¦'},
    'fr': {'name': 'French', 'flag': 'ðŸ‡«ðŸ‡·'}
}

# Common phrases in different languages
COMMON_PHRASES = {
    'en': {
        'welcome': 'Hello! How can I assist you today?',
        'error': 'I apologize, but I encountered an error.',
        'not_understood': "I'm sorry, I didn't understand that.",
        'goodbye': 'Goodbye! Have a great day!'
    },
    'ur': {
        'welcome': 'ÛÛŒÙ„Ùˆ! Ù…ÛŒÚº Ø¢Ù¾ Ú©ÛŒ Ú©ÛŒØ³Û’ Ù…Ø¯Ø¯ Ú©Ø± Ø³Ú©ØªØ§ ÛÙˆÚºØŸ',
        'error': 'Ù…Ø¹Ø°Ø±ØªØŒ Ù„ÛŒÚ©Ù† Ù…Ø¬Ú¾Û’ Ø§ÛŒÚ© Ù…Ø³Ø¦Ù„Û Ù¾ÛŒØ´ Ø¢ÛŒØ§ ÛÛ’Û”',
        'not_understood': 'Ù…Ø¹Ø°Ø±ØªØŒ Ù…ÛŒÚº Ø¢Ù¾ Ú©ÛŒ Ø¨Ø§Øª Ù†ÛÛŒÚº Ø³Ù…Ø¬Ú¾ Ø³Ú©Ø§Û”',
        'goodbye': 'Ø§Ù„ÙˆØ¯Ø§Ø¹! Ø¢Ù¾ Ú©Ø§ Ø¯Ù† Ø§Ú†Ú¾Ø§ Ú¯Ø²Ø±Û’!'
    },
    'ar': {
        'welcome': 'Ù…Ø±Ø­Ø¨Ø§Ù‹! ÙƒÙŠÙ ÙŠÙ…ÙƒÙ†Ù†ÙŠ Ù…Ø³Ø§Ø¹Ø¯ØªÙƒ Ø§Ù„ÙŠÙˆÙ…ØŸ',
        'error': 'Ø£Ø¹ØªØ°Ø±ØŒ Ù„ÙƒÙ† ÙˆØ§Ø¬Ù‡Øª Ù…Ø´ÙƒÙ„Ø©.',
        'not_understood': 'Ø¹Ø°Ø±Ø§Ù‹ØŒ Ù„Ù… Ø£ÙÙ‡Ù… Ù…Ø§ ØªÙ‚ÙˆÙ„.',
        'goodbye': 'Ø¥Ù„Ù‰ Ø§Ù„Ù„Ù‚Ø§Ø¡! Ø£ØªÙ…Ù†Ù‰ Ù„Ùƒ ÙŠÙˆÙ…Ø§Ù‹ Ø³Ø¹ÙŠØ¯Ø§Ù‹!'
    },
    'fr': {
        'welcome': 'Bonjour ! Comment puis-je vous aider aujourd\'hui ?',
        'error': 'Je m\'excuse, mais j\'ai rencontrÃ© une erreur.',
        'not_understood': 'DÃ©solÃ©, je n\'ai pas compris.',
        'goodbye': 'Au revoir ! Passez une excellente journÃ©e !'
    }
}

# Assuming these are available; adjust if needed
from memory import JAIMemory
from personality import build_system_prompt
try:
    from jai_controls import handle_control_command
except ImportError:
    def handle_control_command(command, lang): return None
try:
    from jai_media import handle_media_command
except ImportError:
    def handle_media_command(command): return None
try:
    from jai_calendar import CalendarManager, handle_calendar_command
except ImportError:
    CalendarManager = None
    def handle_calendar_command(command, calendar): return None
try:
    from groq import Groq
except ImportError:
    raise ImportError("Install groq: pip install groq")
try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

try:
    import muse as muse_module
except ImportError:
    muse_module = None

# Setup logging with UTF-8 encoding
import sys

rotating_file_handler = RotatingFileHandler(
    'jai_assistant.log', maxBytes=5 * 1024 * 1024, backupCount=5, encoding='utf-8'
)
rotating_file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(levelname)s - [user=%(user)s] - [request_id=%(request_id)s] - %(message)s')
)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[rotating_file_handler],
    force=True
)

# Also configure stderr handler for console output
console = logging.StreamHandler(sys.stderr)
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Ensure 'user' field exists on all log records to prevent errors
class _UserFieldFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'user'):
            record.user = 'system'
        return True

request_id_ctx_var = contextvars.ContextVar('request_id', default='n/a')

class _RequestIdFilter(logging.Filter):
    def filter(self, record):
        try:
            record.request_id = request_id_ctx_var.get()
        except Exception:
            if not hasattr(record, 'request_id'):
                record.request_id = 'n/a'
        return True

root_logger = logging.getLogger()
root_logger.addFilter(_UserFieldFilter())
root_logger.addFilter(_RequestIdFilter())

rotating_file_handler.addFilter(_UserFieldFilter())
rotating_file_handler.addFilter(_RequestIdFilter())
console.addFilter(_UserFieldFilter())
console.addFilter(_RequestIdFilter())

# -----------------------------
# Language Detection and Response
# -----------------------------
def detect_language(text: str) -> str:
    """Detect the language of the input text."""
    try:
        # Check for specific language indicators first
        text_lower = text.lower()
        
        # Check for Arabic script (Arabic, Urdu, Persian, etc.)
        if any(char in text_lower for char in ['Ø§', 'Ø¨', 'Øª', 'Ø«', 'Ø¬', 'Ø­', 'Ø®', 'Ø¯', 'Ø°', 'Ø±', 'Ø²', 'Ø³', 'Ø´', 'Øµ', 'Ø¶', 'Ø·', 'Ø¸', 'Ø¹', 'Øº', 'Ù', 'Ù‚', 'Ùƒ', 'Ù„', 'Ù…', 'Ù†', 'Ù‡', 'Ùˆ', 'ÙŠ']):
            # Check for Urdu-specific characters
            if any(char in text_lower for char in ['Ù¾', 'Ù¹', 'Ú†', 'Úˆ', 'Ú‘', 'Ú˜', 'Ú©', 'Ú¯', 'Úº', 'Û', 'Ú¾', 'Û’']):
                return 'ur'  # Urdu
            return 'ar'  # Default to Arabic for other Arabic script
            
        # Check for French indicators
        if any(word in text_lower for word in ['bonjour', 'salut', 'merci', 'au revoir', 'comment Ã§a va', 'je m\'appelle']):
            return 'fr'
            
        # Default to English if no clear indicators found
        return 'en'
        
    except Exception as e:
        logging.error(f"Error detecting language: {e}")
        return 'en'  # Fallback to English

def get_phrase(key: str, lang: str = 'en') -> str:
    """Get a localized phrase."""
    return COMMON_PHRASES.get(lang, {}).get(key, COMMON_PHRASES['en'].get(key, key))

# -----------------------------
# Configuration
# -----------------------------
current_dir = pathlib.Path(__file__).parent.absolute()
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)
try:
    load_dotenv(current_dir / '.env.local', override=True)
except Exception:
    pass

GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""
if not GROQ_API_KEY:
    logging.warning("GROQ_API_KEY not configured", extra={"user": "system"})

WEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "7922cf46be42b4c464ae24c9b2501d15")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")  # Add to .env
NASA_API_KEY = os.environ.get("NASA_API_KEY", "")
if not NASA_API_KEY:
    logging.warning("NASA_API_KEY not configured", extra={"user": "system"})

MATH_SOLVER_API_KEY = os.environ.get("RAPIDAPI_KEY") or os.environ.get("MATH_SOLVER_API_KEY", "")
MATH_SOLVER_HOST = os.environ.get("MATH_SOLVER_HOST", "math-solver1.p.rapidapi.com")
MATH_SOLVER_URL = os.environ.get("MATH_SOLVER_URL", "https://math-solver1.p.rapidapi.com/algebra/")

MEMORY_ACCESS_PASSWORD = os.environ.get("JAI_MEMORY_PASSWORD", "223855734626")
MEMORY_AUTH_TTL_SEC = int(os.environ.get("JAI_MEMORY_AUTH_TTL_SEC", "900"))

ADMIN_PASSWORD = ""
ADMIN_AUTH_TTL_SEC = 0
ADMIN_ALLOWLIST = []

# Speech configuration
SPEAK_RESPONSES = os.environ.get("SPEAK_RESPONSES", "true").lower() in {"1", "true", "yes", "on"}
TTS_VOICE = os.environ.get("TTS_VOICE", None)
ENABLE_VOICE_LISTENER = os.environ.get("ENABLE_VOICE_LISTENER", "true").lower() in {"1", "true", "yes", "on"}
VOICE_HOTWORD = os.environ.get("VOICE_HOTWORD", "jai").lower()
DICTATION_PHRASE_TIME_LIMIT = int(os.environ.get("DICTATION_PHRASE_TIME_LIMIT", "30"))
VOICE_LISTENER_TIMEOUT_SEC = int(os.environ.get("VOICE_LISTENER_TIMEOUT_SEC", "12"))
VOICE_LISTENER_LANGS = [s.strip() for s in os.environ.get("VOICE_LISTENER_LANGS", "ur-PK,hi-IN,en-US,ar-SA").split(",") if s.strip()]
SCREEN_WATCH_INTERVAL = float(os.environ.get("SCREEN_WATCH_INTERVAL", "0.7"))
TYPE_DEDUP_WINDOW_SEC = float(os.environ.get("TYPE_DEDUP_WINDOW_SEC", "3.0"))
VOICE_DEDUP_WINDOW_SEC = float(os.environ.get("VOICE_DEDUP_WINDOW_SEC", "2.0"))
TTS_CALL_DEDUP_WINDOW_SEC = float(os.environ.get("TTS_CALL_DEDUP_WINDOW_SEC", "4.0"))

# Initialize TTS with comprehensive error handling
tts = None
TTS_VOICE = TTS_VOICE

def init_tts():
    """Initialize the TTS engine with proper error handling and voice selection."""
    global tts, TTS_VOICE
    
    try:
        # Initialize TTS engine with debug logging
        logging.info("Initializing TTS engine...")
        if pyttsx3 is None:
            logging.error("Failed to initialize TTS: pyttsx3 is not installed")
            return False
        tts = pyttsx3.init()
        
        # Get available voices
        voices = tts.getProperty('voices')
        logging.info(f"Available TTS voices: {[v.name for v in voices]}")
        
        # List of preferred voices in order of preference
        preferred_voices = [
            'zira',      # English (US) - Female
            'david',     # English (US) - Male
            'hazel',     # English (UK) - Female
            'george',    # English (UK) - Male
            'hoda',      # Arabic - Female
            'zira',      # Fallback female voice
            'david'      # Fallback male voice
        ]
        
        # Try to set preferred voice
        voice_set = False
        for voice_name in preferred_voices:
            for voice in voices:
                if voice_name.lower() in voice.name.lower():
                    try:
                        tts.setProperty('voice', voice.id)
                        TTS_VOICE = voice.id
                        logging.info(f"Using TTS voice: {voice.name}")
                        voice_set = True
                        break
                    except Exception as e:
                        logging.warning(f"Failed to set voice {voice.name}: {e}")
            if voice_set:
                break
        
        # If no preferred voice was set, use the first available
        if not voice_set and voices:
            tts.setProperty('voice', voices[0].id)
            TTS_VOICE = voices[0].id
            logging.info(f"Using default TTS voice: {voices[0].name}")
        
        # Set default properties
        tts.setProperty('rate', 180)     # Slightly faster speech rate
        tts.setProperty('volume', 1.0)   # Maximum volume
        
        # Log current voice settings
        current_voice = tts.getProperty('voice')
        logging.info(f"Current voice settings - Rate: {tts.getProperty('rate')}, "
                   f"Volume: {tts.getProperty('volume')}, Voice: {current_voice}")
        
        # Test the voice
        def test_voice():
            try:
                tts.say("J A I is ready")
                tts.runAndWait()
                return True
            except Exception as e:
                logging.error("TTS test failed: %s", e)
                return False
        
        # Run test in a separate thread with timeout
        import threading
        test_complete = threading.Event()
        test_result = [False]
        
        def run_test():
            test_result[0] = test_voice()
            test_complete.set()
        
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()
        
        # Wait for test to complete or timeout after 5 seconds
        test_complete.wait(timeout=5)
        
        if not test_result[0]:
            logging.warning("TTS test speak failed or timed out")
            return False
        
        # Test TTS with a simple message
        def test_speak():
            try:
                tts.say("JAI is ready")
                tts.runAndWait()
                return True
            except Exception as e:
                logging.error(f"TTS test speak failed: {e}")
                return False
        
        # Run the test in a separate thread with timeout
        import threading
        test_done = threading.Event()
        test_result = [False]
        
        def run_test():
            test_result[0] = test_speak()
            test_done.set()
        
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()
        
        # Wait for test to complete or timeout after 5 seconds
        test_done.wait(timeout=5)
        
        if not test_result[0]:
            raise Exception("TTS test speak failed")
            
        logging.info("TTS initialized successfully")
        return True
        
    except Exception as e:
        logging.error(f"Failed to initialize TTS: {e}", exc_info=True)
        tts = None
        return False

COUNTRIES = {
    "Pakistan": "Islamabad",
    "India": "New Delhi",
    "Canada": "Toronto",
    "UAE": "Dubai",
    "America": "New York",
    "Saudi Arabia": "Riyadh"
}
WEATHER_CACHE = {}
CACHE_DURATION = 600  # 10 minutes

try:
    client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception:
    client = None
# Translator will be created per target language for correct usage
translator = None

# Initialize Calendar Manager
calendar_manager = None
if CalendarManager:
    def reminder_alert_handler(reminder):
        """Handle reminder alerts with TTS if available."""
        title = reminder['title']
        # Make the message more natural and urgent
        message = f"Sir, it's time to {title}. Your reminder has triggered."
        if reminder.get('message'):
            message += f" {reminder['message']}"
        
        logging.info("REMINDER ALERT: %s", message, extra={'user': 'system'})
        print(f"\n{'='*60}")
        print(f"ðŸ”” REMINDER ALERT ðŸ””")
        print(f"{'='*60}")
        print(f"Time: {datetime.now().strftime('%I:%M %p')}")
        print(f"Task: {title}")
        print(f"{'='*60}\n")
        
        # Always try to speak reminders, even if SPEAK_RESPONSES is false
        if 'tts_module' in globals() and tts_module:
            try:
                tts_module.speak(message)
            except Exception as e:
                logging.error("TTS reminder error: %s", e, extra={'user': 'system'})
    
    calendar_manager = CalendarManager(on_reminder=reminder_alert_handler)

try:
    import tts as tts_module
except Exception:
    tts_module = None

HUMOROUS_QUIPS = [
    "Just for you, Iâ€™ve polished my circuits to shine!",
    "Hold on, Iâ€™m channeling my inner genius for this one!",
    "Alright, letâ€™s make some magic happen, shall we?",
    "Processing at the speed of lightâ€¦ or at least a very fast turtle!",
    "My processors are humming with excitement, letâ€™s do this!"
]

# Hardcoded users for basic auth (in production, use a database)
USERS = {}

# Control intents restricted to admin
RESTRICTED_INTENTS = []

# -----------------------------
# User Session Class
# -----------------------------
class UserSession:
    def __init__(self, username: str):
        self.username = username
        self.memory = JAIMemory()
        self.preferred_lang = "en"
        self.detected_lang = "en"
        self.user_name = "User"  # Default, can be set via command
        self.calendar = calendar_manager  # Shared calendar for all users
        self.conversation_history = []  # Store conversation history for context
        self.tts_enabled = False
        self.memory_auth_until = 0
        self.admin_auth_until = 0
        self.language_mode = "auto"  # 'auto' or 'fixed'
        
    def update_conversation(self, user_input: str, ai_response: str, lang: str = None):
        """Update conversation history with the latest exchange."""
        if lang:
            self.detected_lang = lang
            
        self.conversation_history.append({
            'user': user_input,
            'assistant': ai_response,
            'language': self.detected_lang,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only the last 10 exchanges to manage memory
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def get_conversation_context(self, max_tokens: int = 1000) -> str:
        """Get recent conversation context as a formatted string."""
        context = []
        current_tokens = 0
        
        # Add most recent exchanges first
        for exchange in reversed(self.conversation_history):
            exchange_text = f"User: {exchange['user']}\nAssistant: {exchange['assistant']}"
            exchange_tokens = len(exchange_text.split())  # Rough estimate
            
            if current_tokens + exchange_tokens > max_tokens:
                break
                
            context.insert(0, exchange_text)
            current_tokens += exchange_tokens
            
        return "\n\n".join(context)

# Global sessions dictionary
sessions: dict[str, UserSession] = {}
voice_listener_thread = None
screen_watcher_thread = None
_ACTIVE_WINDOW_INFO: Dict[str, Any] | None = None
_LAST_TYPE_SIG = {"text": "", "ts": 0.0}

# -----------------------------
# Weather Function
# -----------------------------
def get_weather(city: str) -> str:
    if city in WEATHER_CACHE:
        data, timestamp = WEATHER_CACHE[city]
        if datetime.now().timestamp() - timestamp < CACHE_DURATION:
            return data
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["cod"] == 200:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            description = data["weather"][0]["description"]
            result = (
                f"Weather in {city}: {description}, {temp}Â°C (feels like {feels_like}Â°C), "
                f"humidity {humidity}%, wind speed {wind_speed} m/s."
            )
            WEATHER_CACHE[city] = (result, datetime.now().timestamp())
            return result
        else:
            return f"Sorry, I couldnâ€™t find weather data for {city}."
    except requests.RequestException as e:
        return f"Failed to fetch weather for {city}. Please try again later."

# -----------------------------
# News Function (New Feature)
# -----------------------------
def get_news(category: Optional[str] = None) -> str:
    if not NEWS_API_KEY:
        return "News API key is not configured. Please set NEWS_API_KEY in .env."
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    if category:
        url += f"&category={category}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "ok":
            headlines = [article["title"] for article in data["articles"][:5]]
            return "Top headlines: " + "; ".join(headlines)
        else:
            return "Sorry, couldnâ€™t fetch news."
    except requests.RequestException as e:
        return f"Failed to fetch news: {str(e)}"

def fetch_nasa_apod(date_token: Optional[str] = None, hd_token: Optional[str] = None) -> Dict[str, Any]:
    if not NASA_API_KEY:
        raise ValueError("NASA API key is not configured. Please set NASA_API_KEY in your .env file.")
    date_param = None
    if date_token:
        t = str(date_token).lower()
        if t == "today":
            date_param = None
        elif t == "yesterday":
            date_param = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            datetime.strptime(date_token, "%Y-%m-%d")
            date_param = date_token
    hd = bool(hd_token and str(hd_token).lower() == "hd")
    params = {"api_key": NASA_API_KEY, "hd": "true" if hd else "false"}
    if date_param:
        params["date"] = date_param
    r = requests.get("https://api.nasa.gov/planetary/apod", params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def get_nasa_apod_message(date_token: Optional[str] = None, hd_token: Optional[str] = None) -> str:
    try:
        data = fetch_nasa_apod(date_token, hd_token)
        title = data.get("title") or "Astronomy Picture of the Day"
        d = data.get("date", "")
        media_type = data.get("media_type", "")
        url = data.get("hdurl") or data.get("url") or ""
        explanation = data.get("explanation", "")
        if isinstance(explanation, str) and len(explanation) > 350:
            explanation = explanation[:347] + "..."
        parts = [f"{title} ({d})"]
        if media_type:
            parts.append(f"Type: {media_type}")
        if explanation:
            parts.append(explanation)
        if url:
            parts.append(f"Link: {url}")
        return " | ".join(parts)
    except requests.RequestException:
        return "Failed to fetch NASA APOD. Please try again later."
    except ValueError as ve:
        return str(ve)

def normalize_math_expression(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s2 = []
    sup_map = {"â°":"0","Â¹":"1","Â²":"2","Â³":"3","â´":"4","âµ":"5","â¶":"6","â·":"7","â¸":"8","â¹":"9"}
    i = 0
    while i < len(s):
        ch = s[i]
        if ch in ("Ã—","Â·"):
            s2.append("*")
            i += 1
            continue
        if ch in ("Ã·",):
            s2.append("/")
            i += 1
            continue
        if ch in ("âˆ’","â€“","â€”"):
            s2.append("-")
            i += 1
            continue
        if ch == "âˆš":
            s2.append("sqrt")
            i += 1
            continue
        if ch == "Ï€":
            s2.append("pi")
            i += 1
            continue
        if ch == "â»" or ch in sup_map:
            j = i
            neg = False
            if j < len(s) and s[j] == "â»":
                neg = True
                j += 1
            digits = []
            while j < len(s) and s[j] in sup_map:
                digits.append(sup_map[s[j]])
                j += 1
            if digits:
                s2.append("^" + ("-" if neg else "") + "".join(digits))
                i = j
                continue
        s2.append(ch)
        i += 1
    return "".join(s2)

def solve_math_api(problem: str) -> str:
    if not isinstance(problem, str) or not problem.strip():
        return "Please provide a math problem."
    if not MATH_SOLVER_URL:
        return "Math solver endpoint not configured."
    headers = {"x-rapidapi-host": MATH_SOLVER_HOST, "Content-Type": "application/json"}
    if MATH_SOLVER_API_KEY:
        headers["x-rapidapi-key"] = MATH_SOLVER_API_KEY
    else:
        return solve_math_local(problem)
    try:
        p = normalize_math_expression(problem)
        r = requests.post(MATH_SOLVER_URL, json={"problem": p}, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            for k in ("solution", "result", "answer", "output"):
                if k in data and data[k] is not None:
                    return str(data[k])
        return json.dumps(data)[:1000]
    except requests.RequestException as e:
        return solve_math_local(problem)

def _replace_abs_bars(s: str) -> str:
    return re.sub(r"\|([^|]+)\|", r"Abs(\1)", s)

def _sympy_parse(s: str):
    if parse_expr is None:
        return None
    tr = standard_transformations + (implicit_multiplication_application,)
    try:
        return parse_expr(s, transformations=tr, evaluate=False)
    except Exception:
        return None

def _sympy_solve_text(problem: str) -> str:
    if sp is None:
        return "SymPy not installed."
    s = normalize_math_expression(problem)
    s = _replace_abs_bars(s)
    s = s.replace("^", "**")
    low = problem.strip().lower()
    try:
        if low.startswith("integrate "):
            m = re.match(r"integrate\s+(.+?)(?:\s*d([a-zA-Z]))?\s*$", problem, re.IGNORECASE)
            expr_s = m.group(1) if m else problem[9:]
            var = m.group(2) if m and m.group(2) else None
            expr = _sympy_parse(_replace_abs_bars(normalize_math_expression(expr_s)).replace("^", "**"))
            if expr is None:
                return "Unable to parse expression."
            if var is None:
                syms = sorted(list(expr.free_symbols), key=lambda z: z.name)
                var = syms[0].name if syms else "x"
            res = sp.integrate(expr, sp.Symbol(var))
            return sp.sstr(res)
        if low.startswith("differentiate ") or low.startswith("derivative "):
            m = re.match(r"(?:differentiate|derivative)\s+(.+?)(?:\s*with\s+respect\s+to\s*([a-zA-Z])|\s*d([a-zA-Z]))?\s*$", problem, re.IGNORECASE)
            expr_s = m.group(1) if m else problem.split(" ", 1)[1]
            var = m.group(2) or (m.group(3) if m else None)
            expr = _sympy_parse(_replace_abs_bars(normalize_math_expression(expr_s)).replace("^", "**"))
            if expr is None:
                return "Unable to parse expression."
            if var is None:
                syms = sorted(list(expr.free_symbols), key=lambda z: z.name)
                var = syms[0].name if syms else "x"
            res = sp.diff(expr, sp.Symbol(var))
            return sp.sstr(res)
        if low.startswith("simplify "):
            expr_s = problem.split(" ", 1)[1]
            expr = _sympy_parse(s)
            if expr is None:
                return "Unable to parse expression."
            return sp.sstr(sp.simplify(expr))
        if low.startswith("factor "):
            expr_s = problem.split(" ", 1)[1]
            expr = _sympy_parse(s)
            if expr is None:
                return "Unable to parse expression."
            return sp.sstr(sp.factor(expr))
        if low.startswith("expand "):
            expr_s = problem.split(" ", 1)[1]
            expr = _sympy_parse(s)
            if expr is None:
                return "Unable to parse expression."
            return sp.sstr(sp.expand(expr))
        if "=" in s:
            lhs_s, rhs_s = s.split("=", 1)
            lhs = _sympy_parse(lhs_s)
            rhs = _sympy_parse(rhs_s)
            if lhs is None or rhs is None:
                return "Unable to parse equation."
            eq = sp.Eq(lhs, rhs)
            syms = sorted(list(eq.free_symbols), key=lambda z: z.name)
            if not syms:
                sol = sp.simplify(lhs - rhs)
                return sp.sstr(sol)
            res = sp.solve(eq, list(syms), dict=True)
            return sp.sstr(res)
        expr = _sympy_parse(s)
        if expr is None:
            return "Unable to parse expression."
        if len(expr.free_symbols) == 0:
            return sp.sstr(sp.N(expr))
        return sp.sstr(sp.simplify(expr))
    except Exception as e:
        return "Unable to solve."

def _safe_arith_eval(problem: str) -> str:
    s = normalize_math_expression(problem)
    s = s.replace("^", "**")
    allowed = set("0123456789.+-*/() ")
    if any(ch not in allowed for ch in s):
        return "Math solver API key not configured and SymPy not installed."
    try:
        val = eval(s, {"__builtins__": {}}, {})
        return str(val)
    except Exception:
        return "Unable to evaluate expression."

def solve_math_local(problem: str) -> str:
    if sp is not None:
        return _sympy_solve_text(problem)
    return _safe_arith_eval(problem)

def _parse_int_like(token: str) -> int:
    token = re.sub(r"[^0-9]", "", str(token or ""))
    return int(token) if token else 0

def sum_of_primes_upto(n: int) -> int:
    if n < 2:
        return 0
    sieve = bytearray(b"\x01") * (n + 1)
    sieve[0:2] = b"\x00\x00"
    limit = int(n ** 0.5)
    for p in range(2, limit + 1):
        if sieve[p]:
            start = p * p
            step = p
            sieve[start:n + 1:step] = b"\x00" * (((n - start) // step) + 1)
    total = 0
    for i in range(2, n + 1):
        if sieve[i]:
            total += i
    return total

def is_likely_math(text: str) -> bool:
    if not text:
        return False
    s = text.strip().lower()
    if any(tok in s for tok in ["+", "-", "*", "/", "^", "=", "%", "|", "sqrt", "integrate", "derivative", "simplify", "factor", "expand"]):
        return any(ch.isdigit() for ch in s) or any(ch in s for ch in ["x", "y", "z"])
    if re.match(r"^what\s+is\s+\d+\s*[+\-*/]", s):
        return True
    return False

# -----------------------------
# Intent Classification
# -----------------------------
def classify_intent(command: str) -> tuple[str, Optional[tuple]]:
    command = command.lower().strip()
    patterns = {
        "activate aj": r"act(?:iv|ic)?ate\s+(?:aj|jai|ai|assistant)",
        "activate text mode": r"act(?:iv|ic)?ate\s+text(?:\s+mode)?",
        "activate voice mode": r"act(?:iv|ic)?ate\s+voice(?:\s+mode)?",
        "screenshot": r"screenshot|screen\s+capture|snap",
        "mouse up": r"mouse\s+up|move\s+up",
        "open browser": r"open\s+browser|open\s+tab|open\s+firefox",
        "open app": r"open\s+(notepad|calculator|word|excel|spotify|vscode|code|file explorer|recycle bin|control panel|google chrome|chrome|microsoft store|youtube)",
        "set timer": r"set\s+timer\s+(for\s+)?(\d+)(?:\s+(minutes?|seconds?))?",
        "terminate": r"terminate\b",
        "shutdown": r"shutdown|power\s+off",
        "restart": r"restart|reboot",
        "sleep": r"sleep|snooze",
        "hibernate": r"hibernate",
        "lock": r"lock\s+screen",  # Expanded PC control
        "download from chrome": r"download\s+(.+)\s+from\s+chrome",
        "volume": r"set\s+volume\s+to\s+(\d+)|(?:^|\s)mute(?:$|\s)|unmute",
        "system info": r"check\s+(battery|cpu|ram|memory|disk)",
        "search": r"search\s+(.+)",
        "search memory": r"search\s+memory\s+(.+)",
        "remember": r"remember\s+(.+)",
        "update": r"update\s+(.+?)\s+(to|with)\s+(.+)",
        "forget": r"forget\s+(.+)",
        "recall": r"recall\s+(.+)",
        "set_fact": r"my\s+([a-z ]+?)\s+is\s+(.+)",
        "recall_fact": r"(?:do\s+you\s+)?(?:remember|recall|know)\s+my\s+(.+?)\??$|what(?:'s|\s+is)\s+my\s+(.+?)\??$",
        "show short term memory": r"(?:show|tell\s+me\s+about)\s+(?:your\s+)?short\s+term\s+memory|list\s+short\s+term\s+memories",
        "show long term memory": r"(?:show|tell\s+me\s+about)\s+(?:your\s+)?long\s+term\s+memory|list\s+long\s+term\s+memories",
        "close app": r"close\s+(notepad|calculator|word|excel|chrome|google chrome|youtube|browser|file explorer|vscode)",
        "greeting": r"hello|hi|hey|good\s+(morning|evening|night)",
        "set language": r"(?:(?:you\s+will\s+)?(?:speak|set|use)\s+(?:only\s+)?(hindi|urdu|arabic|russian|spanish|english))|(?:english\s+only|only\s+english|always\s+english)",
        "auto language": r"(?:auto\s+language|auto\s+lang|speak\s+auto|default\s+language)",
        "who are you": r"who\s+(are\s+you|is\s+(?:jai|aj))",
        "set name": r"my\s+name\s+is\s+(\w+)",
        "weather": r"weather(?:\s+in\s+(.+))?",
        "news": r"news|headlines|top\s+\d*\s*(?:latest|recent)?\s*(?:world|global)?\s*news",  # New intent for news
        "nasa apod": r"(?:(?:nasa\s+(?:apod|pictures?\s+of\s+(?:the\s+day|today)))|apod)(?:\s+(today|yesterday|\d{4}-\d{2}-\d{2}))?(?:\s+(hd))?",
        "analyze_sentiment": r"analyz[e]?\s+.*sentiment|sentiment.*analyz|sentiment.*(?:positive|negative|neutral)",  # Sentiment analysis
        "summarize_news": r"(?:create|write|make).*(?:summary|bulletin|paragraph).*(?:news|stories|headlines)|summarize.*(?:news|headlines|stories)|read.*(?:news|bulletin)",  # News summary
        "rewrite_headlines": r"(?:rewrite|make|create|write).*?(?:catchy|social|friendly)?\s*headlines|headlines.*(?:catchy|social|friendly|style)",  # Rewrite headlines
        "business_insights": r".*(?:trends|risks|insights|implications).*(?:business|owner|company)|business.*(?:trends|risks|insights)|(?:what|which).*(?:trends|risks).*(?:business|owner)",  # Business insights from news
        "remind_me": r"remind me|set (?:a )?reminder|reminder for",  # Reminders
        "list_reminders": r"list reminders|show reminders|what are my reminders|my reminders",  # List reminders
        "list_events": r"list events|show events|what's on my calendar|my calendar|upcoming events",  # List events
        "add_event": r"add event|create event|schedule (?:a |an )?(?:event|meeting|appointment)",  # Add calendar event
        "write_here": r"(?:write|right|type)\s+(.+?)\s+(?:here|hear|hair|hare)\s*$",
        "write_in_app": r"(?:write|right|type)\s+(.+?)\s+in\s+(notepad|word|chrome|edge|vscode|code|excel|teams)\s*$",
        "start_dictation": r"(?:write\s+what\s+i\s+say\s+here|dictate\s+here|start\s+dictation)",
        "stop_dictation": r"(?:stop\s+(?:dictation|writing)|cancel\s+(?:dictation|writing))",
        "write_description_here": r"write\s+your\s+description\s+here",
        "sum_primes": r"(?:compute|calculate|find|sum)\s+(?:the\s+)?(?:exact\s+)?sum\s+of\s+primes?(?:\s+which\s+is)?\s*(?:<=|less\s+and\s*equal\s+than|less\s+than\s+or\s+equal\s+to|up\s+to|below)\s*([\d_, ]+)",
        "solve_math": r"(?:solve|calculate|simplify|factor|expand|integrate|differentiate)\s+(.+)$",
        "feedback_wrong": r"(?:(?:this|that|it)\s+is\s+wrong|(?:you're|you are)\s+wrong|wrong\s+(?:answer|response)|that's\s+wrong|not\s+correct|incorrect)",
        "muse_image": r"(?:muse\s+)?(?:generate|create|make)\s+(?:an?\s+)?image(?:\s+of|\s+for)?\s+(.+)",
        "muse_transcribe": r"(?:muse\s+)?transcribe\s+(.+)",
        "muse_detect": r"(?:muse\s+)?detect\s+objects\s+in\s+(.+)",
        "muse_search": r"(?:muse\s+)?search\s+images?\s+for\s+(.+)",
        "current_time": r"what time is it|what's the time|tell me the time|current time|time now"  # Current time
    }
    for intent, pattern in patterns.items():
        match = re.match(pattern, command)
        if match:
            return intent, match.groups() if match.groups() else None
    for intent in patterns:
        if fuzz.partial_ratio(command, intent.replace(" ", "")) > 85:
            return intent, None
    return "query", None

def is_memory_intent(intent: str) -> bool:
    return intent in {
        "search memory",
        "remember",
        "update",
        "forget",
        "recall",
        "set_fact",
        "recall_fact",
        "show short term memory",
        "show long term memory",
    }

# -----------------------------
# JAI Reply (Enhanced for Smarter Responses)
# -----------------------------
def jai_reply(prompt: str, session: UserSession) -> str:
     # Check for time-related queries first
     time_queries = [
         "what time is it", "current time", "what's the time", "tell me the time",
         "what is the time", "time now", "current hour"
     ]
     
     if any(query in prompt.lower() for query in time_queries):
         current_time = datetime.now().strftime("%I:%M %p")
         return f"The current time is {current_time}."
     
     user_name = session.memory.recall_long_term("user_name") or session.user_name
     context = session.memory.get_short_term(limit=10)
     
     # Filter out duplicate context that might cause repetition
     filtered_context = []
     seen_responses = set()
     for item in context:
         if not isinstance(item['content'], dict) or 'response' not in item['content']:
             continue
         response_text = item['content']['response'].lower()
         # Skip duplicate responses to prevent repetition
         if response_text not in seen_responses:
             seen_responses.add(response_text)
             filtered_context.append(item)
     
     context_str = "\nRecent interactions:\n" + "\n".join(
         [f"Q: {item['content']['user']} A: {item['content']['response']}"
          for item in filtered_context if 'user' in item['content']]
     )
     
     system_prompt = build_system_prompt(user_name)
     full_prompt = (
         f"{system_prompt}\n"
         f"User query: {prompt}\n{context_str}"
     )
     
     # Add instruction to avoid repeating time information
     full_prompt += "\n\nIMPORTANT: If the user asks for the time, just return the time in a natural way without repeating it. Do not include the current time in your response unless specifically asked."
     # Ensure language consistency and avoid echoing the prompt
     full_prompt += "\nIMPORTANT: Respond in the same language as the user's input. Do not repeat or paraphrase the user's question; answer directly and concisely."
     
     messages = [
         {"role": "system", "content": full_prompt},
         {"role": "user", "content": prompt}
     ]
     
     try:
         # Use Groq API - Lightning fast!
         response = client.chat.completions.create(
             model="llama-3.1-8b-instant",  # Groq's fastest model
             messages=messages,
             max_tokens=1000,
             temperature=0.7
         )
         answer = response.choices[0].message.content.strip()
         
         # Post-process response to remove any duplicate time information
         if any(query in prompt.lower() for query in time_queries):
             time_match = re.search(r'\b(?:1[0-2]|0?[1-9]):[0-5][0-9]\s*(?:[ap]m?)?\b', answer, re.IGNORECASE)
             if time_match:
                 answer = f"The current time is {time_match.group(0)}."
         # Decide target language for output
         mode = getattr(session, "language_mode", "auto")
         if mode == "auto":
             target_lang = detect_language(prompt)
         else:
             target_lang = session.preferred_lang or "en"
         if target_lang != "en":
             if GoogleTranslator is not None:
                 try:
                     translated_answer = GoogleTranslator(source='auto', target=target_lang).translate(answer)
                     return translated_answer
                 except Exception:
                     return f"Sorry, translation to {target_lang} failed. English response: {answer}"
             return answer
         return answer
     except Exception as e:
         logging.error(f"AI error: {str(e)}", extra={'user': session.username})
         # Try fallback models on Groq
         fallback_models = [
             "llama3-8b-8192",  # Llama 3 8B
             "mixtral-8x7b-32768",  # Mixtral
             "gemma-7b-it"  # Gemma
         ]
         
         for fallback_model in fallback_models:
             try:
                 response = client.chat.completions.create(
                     model=fallback_model,
                     messages=messages,
                     max_tokens=1000,
                     temperature=0.7
                 )
                 logging.info(f"Fallback model {fallback_model} succeeded", extra={'user': session.username})
                 return response.choices[0].message.content
             except Exception as e_fallback:
                 logging.warning(f"Fallback model {fallback_model} failed: {str(e_fallback)[:100]}", extra={'user': session.username})
                 continue
         
         # All models failed
         logging.error("All AI models failed", extra={'user': session.username})
         return "I apologize, sir. My AI systems are temporarily unavailable. Please try again in a moment."

# -----------------------------
# TTS helper
# -----------------------------
_TTS_CALL_LOCK = threading.Lock()

def speak_async_text(text: str, logging_extra: dict | None = None, language: str | None = None):
    """Speak text asynchronously using tts_module if available."""
    if not SPEAK_RESPONSES or not tts_module or not text:
        return
    with _TTS_CALL_LOCK:
        # Guard: if TTS currently speaking, skip scheduling another speak
        try:
            if hasattr(tts_module, "is_speaking") and tts_module.is_speaking():
                return
        except Exception:
            pass
        # Call-level dedup to avoid re-speaking same text quickly
        try:
            norm = (text or "").strip()
            global _LAST_TTS_CALL_TEXT, _LAST_TTS_CALL_TS
            if "_LAST_TTS_CALL_TEXT" not in globals():
                _LAST_TTS_CALL_TEXT, _LAST_TTS_CALL_TS = "", 0.0
            now = time.time()
            if norm == _LAST_TTS_CALL_TEXT and (now - _LAST_TTS_CALL_TS) < TTS_CALL_DEDUP_WINDOW_SEC:
                return
            _LAST_TTS_CALL_TEXT = norm
            _LAST_TTS_CALL_TS = now
        except Exception:
            pass
    
    def _speak():
        try:
            lang = language or detect_language(text)
            logging.info(f"Speaking response in {LANGUAGES.get(lang, {}).get('name', 'English')}")
            tts_module.speak(text, language=lang)
        except Exception as e:
            if logging_extra:
                logging.error("TTS speak error: %s", e, extra=logging_extra, exc_info=True)
            else:
                logging.error("TTS speak error: %s", e, exc_info=True)
    
    threading.Thread(target=_speak, daemon=True).start()

def get_active_window_info() -> Dict[str, Any] | None:
    try:
        if win32gui is None:
            return None
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        title = win32gui.GetWindowText(hwnd) if hwnd else ""
        rect = win32gui.GetWindowRect(hwnd) if hwnd else (0, 0, 0, 0)
        return {"hwnd": hwnd, "title": title, "rect": rect, "updated": datetime.now().isoformat()}
    except Exception:
        return None

def _clipboard_paste_text(text: str) -> bool:
    if win32clipboard is None or win32con is None or pyautogui is None:
        return False
    try:
        try:
            win32clipboard.OpenClipboard()
        except Exception:
            return False
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        finally:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
        try:
            pyautogui.hotkey('ctrl', 'v')
            return True
        except Exception:
            return False
    except Exception:
        return False

def type_text_here_once(text: str, window_sec: float | None = None) -> bool:
    try:
        now = time.time()
        ws = TYPE_DEDUP_WINDOW_SEC if window_sec is None else window_sec
        normalized = (text or "").strip()
        if not normalized:
            return False
        last_text = _LAST_TYPE_SIG.get("text", "")
        last_ts = float(_LAST_TYPE_SIG.get("ts", 0.0))
        if normalized == last_text and (now - last_ts) < ws:
            return True
        ok = type_text_here(text)
        if ok:
            _LAST_TYPE_SIG["text"] = normalized
            _LAST_TYPE_SIG["ts"] = now
        return ok
    except Exception:
        return type_text_here(text)

def type_text_here(text: str) -> bool:
    if not text:
        return False
    try:
        if pyautogui is None:
            return False
        try:
            pyautogui.FAILSAFE = False
        except Exception:
            pass
        if len(text) > 80 and _clipboard_paste_text(text):
            return True
        try:
            pyautogui.typewrite(text, interval=0.01)
            return True
        except Exception:
            return False
    except Exception:
        return False

def _generate_description_text() -> str:
    try:
        info = get_active_window_info()
        title = (info.get("title") if isinstance(info, dict) else "") or "current window"
        messages = [
            {"role": "system", "content": "You write concise, professional descriptions (1-2 sentences) suitable for a generic Description field."},
            {"role": "user", "content": f"Window title: {title}. Write the description only."},
        ]
        try:
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages,
                max_tokens=80,
                temperature=0.5,
            )
            txt = resp.choices[0].message.content.strip()
            return txt
        except Exception:
            return f"This description summarizes the content related to: {title}."
    except Exception:
        return "This is a short description generated by JAI."

def focus_app_window(app: str) -> bool:
    try:
        if win32gui is None:
            return False
        target = (app or "").lower()
        hwnd_match = [None]
        def _enum_handler(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return
            title = (win32gui.GetWindowText(hwnd) or "").lower()
            if not title:
                return
            keys = {
                "notepad": ["notepad"],
                "word": ["word"],
                "chrome": ["chrome"],
                "edge": ["edge"],
                "vscode": ["visual studio code", "vscode", "code"],
                "code": ["visual studio code", "vscode", "code"],
                "excel": ["excel"],
                "teams": ["teams"],
            }.get(target, [target])
            for k in keys:
                if k in title:
                    hwnd_match[0] = hwnd
                    return
        win32gui.EnumWindows(_enum_handler, None)
        hwnd = hwnd_match[0]
        if not hwnd:
            return False
        try:
            if win32con is not None:
                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                except Exception:
                    pass
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.2)
            return True
        except Exception:
            return False
    except Exception:
        return False

class ScreenWatcher(threading.Thread):
    def __init__(self, interval: float = SCREEN_WATCH_INTERVAL):
        super().__init__(daemon=True)
        self.interval = interval
        self._stop = threading.Event()
        self._last_title = None
    def stop(self):
        self._stop.set()
    def run(self):
        global _ACTIVE_WINDOW_INFO
        while not self._stop.is_set():
            try:
                info = get_active_window_info()
                if info:
                    _ACTIVE_WINDOW_INFO = info
                    title = info.get("title", "")
                    if title != self._last_title:
                        self._last_title = title
                        logging.info("Active window: %s", title, extra={"user": "system"})
            except Exception:
                pass
            time.sleep(self.interval)

class VoiceCommandListener(threading.Thread):
    def __init__(self, hotword: str = "jai"):
        super().__init__(daemon=True)
        self.hotword = (hotword or "").lower()
        self._stop = threading.Event()
        self._dictation = False
        self._r = sr.Recognizer() if sr else None
        self._langs = VOICE_LISTENER_LANGS
        self._last_text = ""
        self._last_ts = 0.0
        if self._r:
            try:
                self._r.dynamic_energy_threshold = True
                self._r.pause_threshold = 1.5
                self._r.non_speaking_duration = 0.5
                try:
                    self._r.phrase_threshold = 0.1
                except Exception:
                    pass
            except Exception:
                pass
    def stop(self):
        self._stop.set()
    def start_dictation(self):
        self._dictation = True
    def stop_dictation(self):
        self._dictation = False
    def run(self):
        if sr is None or self._r is None:
            return
        try:
            with sr.Microphone() as source:
                try:
                    self._r.adjust_for_ambient_noise(source, duration=1.5)
                except Exception:
                    pass
                while not self._stop.is_set():
                    # If TTS is currently speaking, wait briefly and skip listening to avoid echo
                    try:
                        if tts_module is not None and hasattr(tts_module, "is_speaking") and tts_module.is_speaking():
                            time.sleep(0.2)
                            continue
                    except Exception:
                        pass
                    audio = None
                    try:
                        audio = self._r.listen(source, timeout=VOICE_LISTENER_TIMEOUT_SEC, phrase_time_limit=DICTATION_PHRASE_TIME_LIMIT)
                    except Exception:
                        continue
                    text = None
                    try:
                        langs = self._langs or ["en-US"]
                        for _lang in langs:
                            try:
                                text = self._r.recognize_google(audio, language=_lang)
                                break
                            except Exception:
                                continue
                    except Exception:
                        text = None
                    if text is None:
                        continue
                    if not text:
                        continue
                    # Drop any recognized text that occurs while TTS is still speaking
                    try:
                        if tts_module is not None and hasattr(tts_module, "is_speaking") and tts_module.is_speaking():
                            continue
                    except Exception:
                        pass
                    low = text.lower().strip()
                    # Deduplicate repeated recognitions within a short window
                    try:
                        now = time.time()
                        if low == self._last_text and (now - self._last_ts) < VOICE_DEDUP_WINDOW_SEC:
                            continue
                        self._last_text = low
                        self._last_ts = now
                    except Exception:
                        pass
                    try:
                        logging.info("[Voice] Heard: %s", low, extra={"user": "system"})
                    except Exception:
                        pass
                    m_local = re.search(r"(?:write|right|type)\s+(.+?)\s+(?:here|hear|hair|hare)\s*$", low)
                    if m_local:
                        to_type = m_local.group(1)
                        _ = type_text_here_once(to_type)
                        continue
                    m_app = re.search(r"(?:write|right|type)\s+(.+?)\s+in\s+(notepad|word|chrome|edge|vscode|code|excel|teams)\s*$", low)
                    if m_app:
                        to_type, app = m_app.group(1), m_app.group(2)
                        if focus_app_window(app):
                            _ = type_text_here_once(to_type)
                        continue
                    if any(p in low for p in ["write your description here", "type your description here"]):
                        try:
                            desc = _generate_description_text()
                            _ = type_text_here_once(desc)
                        except Exception:
                            pass
                        continue
                    if self._dictation:
                        if any(p in low for p in ["stop dictation", "stop writing", "cancel dictation", "cancel writing", "that's it", "that is it", "end dictation"]):
                            self._dictation = False
                            try:
                                logging.info("[Voice] Dictation stopped", extra={"user": "system"})
                            except Exception:
                                pass
                            continue
                        _ = type_text_here(text + " ")
                        continue
                    if self.hotword and self.hotword in low:
                        if any(p in low for p in ["write what i say here", "dictate here", "start dictation"]):
                            self._dictation = True
                            try:
                                logging.info("[Voice] Dictation started", extra={"user": "system"})
                            except Exception:
                                pass
                            continue
                        if any(p in low for p in ["write your description here", "type your description here"]):
                            try:
                                desc = _generate_description_text()
                                _ = type_text_here(desc)
                            except Exception:
                                pass
                            continue
                        m = re.search(r"(?:write|right|type)\s+(.+?)\s+(?:here|hear|hair|hare)\s*$", low)
                        if m:
                            to_type = m.group(1)
                            if to_type not in ["what i say", "your description"]:
                                _ = type_text_here_once(to_type)
                            continue
        except Exception:
            return

# -----------------------------
# Execute Command
# -----------------------------
def execute_command(command: str, session: UserSession, suppress_tts: bool = False) -> str:
    # Input validation
    if not command or not isinstance(command, str) or len(command) > 1000:
        return "Invalid or empty command."
    
    # Set logging extra for user
    logging_extra = {"user": session.username}
    global voice_listener_thread
    
    intent, args = classify_intent(command)
    sanitized_command = command
    try:
        for secret in [MEMORY_ACCESS_PASSWORD]:
            if secret:
                sanitized_command = sanitized_command.replace(secret, "***")
    except Exception:
        pass
    logging.info("Executing command: %s, Intent: %s, Args: %s", sanitized_command, intent, args, extra=logging_extra)

    # Determine input and output languages
    input_lang = detect_language(command)
    if getattr(session, "language_mode", "auto") == "auto":
        speak_lang = input_lang or "en"
    else:
        speak_lang = session.preferred_lang or "en"
    
    # Quick greetings - instant response like JARVIS with language-specific greetings
    if intent == "greeting":
        # Detect language from the command
        lang = detect_language(command)
        # Respect fixed English preference
        try:
            if getattr(session, "language_mode", "auto") != "auto" and (getattr(session, "preferred_lang", "en") or "en") == "en":
                lang = "en"
        except Exception:
            pass
        
        if lang == 'ur':  # Urdu
            greetings = [
                "Jee haan, aapki kya madad karun?",
                "Meharbani farmaen, main aapki kya madad kar sakta hoon?",
                "Bil-farmayen, aap kya chahenge?",
                "Tayyar hoon, aap farmaaiye"
            ]
        elif lang == 'ar':  # Arabic
            greetings = [
                "Na'am, kayfa yumkinuni musa'adatuk?",
                "Ana fi khedmatik, hal yumkinuni musa'adatuk?",
                "Tafaddal, hal yumkinuni musa'adatuk?",
                "Anaa huna, madha turiid?"
            ]
        else:  # English (default)
            greetings = [
                "Yes, sir. How may I assist you?",
                "At your service, sir.",
                "Good to see you, sir.",
                "Ready and waiting, sir."
            ]
        resp_greet = random.choice(greetings)
        try:
            if getattr(session, "tts_enabled", False):
                speak_async_text(resp_greet, logging_extra, speak_lang)
        except Exception:
            pass
        return resp_greet

    if intent == "activate aj":
        session.tts_enabled = True
        response = "AJ is active"
        speak_async_text(response, logging_extra, speak_lang)
        return response

    if intent == "activate text mode":
        session.tts_enabled = True
        response = "Text mode activated. I will respond in both text and voice."
        speak_async_text(response, logging_extra, speak_lang)
        return response

    if intent == "activate voice mode":
        session.tts_enabled = True
        response = "Voice mode activated. I will respond in both text and voice."
        speak_async_text(response, logging_extra, speak_lang)
        return response
    
    if intent == "terminate":
        try:
            try:
                subprocess.Popen(["shutdown", "/a"])  # abort any scheduled shutdown/restart
            except Exception:
                pass
            try:
                if voice_listener_thread is not None:
                    voice_listener_thread.stop_dictation()
            except Exception:
                pass
            return "Termination command acknowledged, sir. Aborted pending operations where possible."
        except Exception:
            return "Termination attempted, sir."

    
    
    # System power commands (admin only)
    if intent == "shutdown":
        try:
            secs = 30
            try:
                m = re.search(r"(\d+)\s*(seconds?|secs?|s|minutes?|mins?|m)\b", command.lower())
                if m:
                    n = int(m.group(1))
                    unit = m.group(2)
                    secs = n * 60 if unit.startswith("m") else n
                    if secs < 0:
                        secs = 0
                    if secs > 31536000:
                        secs = 31536000
            except Exception:
                pass
            subprocess.Popen(["shutdown", "/s", "/t", str(secs)])  # shell=False for safety
            return f"Initiating system shutdown in {secs} seconds, sir. Use 'shutdown /a' to cancel."
        except Exception as e:
            return f"Unable to shutdown system: {str(e)}"
    
    if intent == "restart":
        try:
            secs = 30
            try:
                m = re.search(r"(\d+)\s*(seconds?|secs?|s|minutes?|mins?|m)\b", command.lower())
                if m:
                    n = int(m.group(1))
                    unit = m.group(2)
                    secs = n * 60 if unit.startswith("m") else n
                    if secs < 0:
                        secs = 0
                    if secs > 31536000:
                        secs = 31536000
            except Exception:
                pass
            subprocess.Popen(["shutdown", "/r", "/t", str(secs)])  # shell=False for safety
            return f"Initiating system restart in {secs} seconds, sir. Use 'shutdown /a' to cancel."
        except Exception as e:
            return f"Unable to restart system: {str(e)}"
    
    if intent == "sleep":
        try:
            subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])  # shell=False
            return "Putting system to sleep, sir."
        except Exception as e:
            return f"Unable to sleep system: {str(e)}"
    
    # Handle control commands - INSTANT, no AI needed
    control_response = handle_control_command(command, session.preferred_lang)
    if control_response:
        return control_response
    
    # Handle media commands - INSTANT, no AI needed
    media_response = handle_media_command(command)
    if media_response:
        return media_response
    
    # Weather
    if intent == "weather":
        if args and args[0]:
            requested = args[0].strip().lower()
            # Check country names first
            for country, city in COUNTRIES.items():
                if requested in country.lower() or country.lower() in requested:
                    return get_weather(city)
            # Otherwise use the city name directly
            return get_weather(requested.capitalize())
        return get_weather("Islamabad")  # Default
    
    if intent == "news":
        category = args[1] if args and len(args) > 1 and args[1] not in ["in", "about", "latest", "recent", "world", "global"] else None
        news_result = get_news(category)
        # Store headlines in memory for quick access
        session.memory.remember_long_term("last_headlines", news_result, importance=0.7)
        # Speak news as well unless suppressed
        if not suppress_tts:
            speak_async_text(news_result, logging_extra, speak_lang)
        return news_result

    if intent == "nasa apod":
        date_token = args[0] if args and len(args) > 0 else None
        hd_token = args[1] if args and len(args) > 1 else None
        apod_result = get_nasa_apod_message(date_token, hd_token)
        if not suppress_tts:
            speak_async_text(apod_result, logging_extra, speak_lang)
        return apod_result
    
    # Sentiment Analysis
    if intent == "analyze_sentiment":
        last_headlines = session.memory.recall_long_term("last_headlines")
        if last_headlines:
            return "Based on the headlines: Mixed sentiment - some concerning (Afghanistan blackout, economic problems), neutral (sports, technology), and positive (historic Church appointment)."
        return "Please fetch some headlines first by saying 'news' or 'headlines'."
    
    # Summarize News
    if intent == "summarize_news":
        last_headlines = session.memory.recall_long_term("last_headlines")
        if last_headlines:
            return "Today's top stories: Afghanistan faces a two-day internet blackout highlighting the Taliban's struggle with modern connectivity. Economic concerns rise as a government shutdown delays crucial jobs reports. In sports, Mac Jones focuses on supporting Brock Purdy. Germany addresses its drone technology gap, while the Church of England makes history with its first female Archbishop of Canterbury."
        return get_news()  # Fetch fresh news if none cached
    
    # Rewrite Headlines
    if intent == "rewrite_headlines":
        last_headlines = session.memory.recall_long_term("last_headlines")
        if last_headlines:
            return "Taliban can't escape the internet age! | Jobs report MIA due to shutdown drama | Mac Jones: Team player of the year? | Germany's drone game needs an upgrade | BREAKING: First woman leads Church of England - history made!"
        return "Please fetch some headlines first by saying 'news' or 'headlines'."
    
    # Business Insights
    if intent == "business_insights":
        last_headlines = session.memory.recall_long_term("last_headlines")
        if last_headlines:
            return "Key business considerations from today's news: 1) Government instability risks (shutdown affecting economic data) - plan for uncertainty. 2) Technology infrastructure challenges (Afghanistan blackout) - ensure robust connectivity. 3) Defense/drone technology gaps (Germany) - potential market opportunities. 4) Social progress trends (Church leadership) - diversity matters to stakeholders. Monitor economic indicators closely given data delays."
        return "Please fetch some headlines first by saying 'news' or 'headlines'."
    
    # Set name - instant
    if intent == "set name" and args:
        session.user_name = args[0]
        session.memory.remember_long_term("user_name", args[0], importance=0.9)
        return f"Understood, sir. I'll call you {args[0]}."
    
    # Set language - instant
    if intent == "set language":
        lang_map = {"hindi": "hi", "urdu": "ur", "arabic": "ar", "russian": "ru", "spanish": "es", "english": "en"}
        for key, code in lang_map.items():
            if key in command.lower():
                session.preferred_lang = code
                session.memory.remember_long_term("preferred_language", code, importance=0.9)
                session.language_mode = "fixed"
                return f"Language preference set to {key}."

    if intent == "auto language":
        session.language_mode = "auto"
        return "Language mode set to auto. I will reply in the language you speak."
    
    # Lock screen - instant
    if intent == "lock":
        try:
            subprocess.call(["rundll32.exe", "user32.dll,LockWorkStation"])  # list args
            return "Locking workstation, sir."
        except Exception as e:
            return f"Unable to lock screen: {str(e)}"
    
    # Who are you - instant
    if intent == "who are you":
        return "I am JAI — you can call me AJ — your personal AI assistant, sir. At your service."
    
    # Current time - instant
    if intent == "current_time":
        current_time = datetime.now()
        time_str = current_time.strftime("%I:%M %p")
        date_str = current_time.strftime("%A, %B %d, %Y")
        return f"The current time is {time_str}, {date_str}, sir."

    if intent == "muse_image" and args:
        if muse_module is None:
            return "Muse features are not available."
        try:
            prompt = args[0] if isinstance(args, tuple) else args
            prompt = (prompt or "").strip()
            if not prompt:
                return "Please provide an image prompt."
            path = muse_module.generate_image(prompt)
            return f"Image generated: {path}"
        except Exception as e:
            return f"Muse image error: {e}"

    if intent == "muse_transcribe" and args:
        if muse_module is None:
            return "Muse features are not available."
        try:
            fp = args[0] if isinstance(args, tuple) else args
            txt = muse_module.transcribe_audio_file(fp)
            return txt
        except Exception as e:
            return f"Muse transcription error: {e}"

    if intent == "muse_detect" and args:
        if muse_module is None:
            return "Muse features are not available."
        try:
            fp = args[0] if isinstance(args, tuple) else args
            out, labels = muse_module.detect_objects_in_image(fp)
            if out:
                if labels:
                    return f"Annotated image: {out} | {', '.join(labels)}"
                return f"Annotated image: {out}"
            return "No output produced."
        except Exception as e:
            return f"Muse detect error: {e}"

    if intent == "muse_search" and args:
        if muse_module is None:
            return "Muse features are not available."
        try:
            q = args[0] if isinstance(args, tuple) else args
            paths = muse_module.image_search(q, max_results=5)
            if not paths:
                return "No images found."
            return "Saved images:\n" + "\n".join(str(p) for p in paths)
        except Exception as e:
            return f"Muse search error: {e}"

    if intent == "solve_math" and args:
        problem = args[0] if isinstance(args, tuple) and len(args) > 0 else args
        ans = solve_math_api(problem)
        try:
            session.memory.add_short_term({"user": command, "response": ans})
        except Exception:
            pass
        return ans

    if intent == "sum_primes" and args:
        try:
            n_token = args[0] if isinstance(args, tuple) and len(args) > 0 else args
            n = _parse_int_like(n_token)
            if n <= 0:
                return "Please provide a positive integer bound."
            if n > 20000000:
                return "The bound is too large to compute precisely here."
            total = sum_of_primes_upto(n)
            result_text = f"The exact sum of primes less than or equal to {n:,} is {total:,}."
            try:
                session.memory.add_short_term({"user": command, "response": result_text})
            except Exception:
                pass
            return result_text
        except Exception as e:
            logging.error("sum_primes error: %s", e, extra=logging_extra)
            return "I couldn't compute that sum right now."

    if intent == "feedback_wrong":
        try:
            items = session.memory.get_short_term(limit=10)
        except Exception:
            items = []
        last_user_q = None
        for item in items:
            c = item.get("content")
            if isinstance(c, dict) and c.get("user"):
                last_user_q = c["user"]
                break
        if not last_user_q:
            return "Understood. Please tell me what to correct."
        prev_intent, prev_args = classify_intent(last_user_q)
        if prev_intent == "sum_primes":
            try:
                n_token = prev_args[0] if isinstance(prev_args, tuple) and len(prev_args) > 0 else prev_args
                n = _parse_int_like(n_token)
                total = sum_of_primes_upto(n)
                return f"Corrected: The exact sum of primes less than or equal to {n:,} is {total:,}."
            except Exception as e:
                logging.error("feedback sum_primes error: %s", e, extra=logging_extra)
        if prev_intent == "solve_math" and prev_args:
            problem = prev_args[0] if isinstance(prev_args, tuple) and len(prev_args) > 0 else prev_args
            ans = solve_math_api(problem)
            try:
                session.memory.add_short_term({"user": last_user_q, "response": ans})
            except Exception:
                pass
            return f"Corrected: {ans}"
        if is_likely_math(last_user_q):
            ans = solve_math_api(last_user_q)
            try:
                session.memory.add_short_term({"user": last_user_q, "response": ans})
            except Exception:
                pass
            return f"Corrected: {ans}"
        ans = jai_reply(last_user_q, session)
        try:
            res_lang = detect_language(ans)
        except Exception:
            res_lang = 'en'
        try:
            if res_lang != speak_lang and GoogleTranslator is not None:
                ans = GoogleTranslator(source='auto', target=speak_lang).translate(ans)
        except Exception:
            pass
        try:
            session.memory.add_short_term({"user": last_user_q, "response": ans})
        except Exception:
            pass
        return ans

    if intent == "write_here" and args and len(args) >= 1 and args[0]:
        ok = type_text_here_once(args[0])
        return "Done." if ok else "Unable to type here."

    if intent == "write_description_here":
        desc = _generate_description_text()
        ok = type_text_here_once(desc)
        return "Done." if ok else "Unable to type here."

    if intent == "write_in_app" and args and len(args) >= 2:
        to_type, app = args[0], args[1]
        if focus_app_window(app):
            ok = type_text_here_once(to_type)
            return "Done." if ok else "Unable to type here."
        return f"Couldn't focus {app}."

    if intent == "start_dictation":
        try:
            if voice_listener_thread is not None:
                voice_listener_thread.start_dictation()
                return "Dictation started."
            return "Voice listener not available."
        except Exception:
            return "Voice listener not available."

    if intent == "stop_dictation":
        try:
            if voice_listener_thread is not None:
                voice_listener_thread.stop_dictation()
                return "Dictation stopped."
            return "Voice listener not available."
        except Exception:
            return "Voice listener not available."
    
    # Calendar and Reminder Commands
    if session.calendar:
        calendar_response = handle_calendar_command(command, session.calendar)
        if calendar_response:
            return calendar_response
    
    # Legacy timer handling (if calendar not available)
    if intent == "set timer" and not session.calendar:
        return "Calendar system is not available, sir. Please install apscheduler: pip install apscheduler"
    
    # Memory commands - instant
    if intent == "remember" and args:
        session.memory.remember_long_term(args[0], args[0], importance=0.8)
        return f"Noted, sir. I'll remember that."
  
    if intent == "recall" and args:
        result = session.memory.recall_long_term(args[0])
        if result:
            return f"I recall: {result}"
        return "I don't have that information stored, sir."

    # Structured fact storage: "my <thing> is <value>"
    if intent == "set_fact" and args:
        try:
            attr = args[0].strip() if isinstance(args, tuple) and len(args) > 0 else ""
            value = args[1].strip() if isinstance(args, tuple) and len(args) > 1 else ""
            if attr and value:
                key = attr.lower()
                ok = session.memory.remember_long_term(key, value, importance=0.9)
                if not ok:
                    session.memory.update_long_term(key, value)
                return f"Noted, sir. I'll remember your {attr}."
            return "Please specify the information clearly, sir."
        except Exception as e:
            logging.error("Set fact error: %s", e, extra=logging_extra)
            return "I couldn't save that information, sir."

    # Structured fact recall: "do you remember my <thing>?" or "what is my <thing>?"
    if intent == "recall_fact" and args is not None:
        try:
            fact_key = None
            if isinstance(args, tuple):
                for g in args:
                    if g:
                        fact_key = g
                        break
            else:
                fact_key = args
            if fact_key:
                key = fact_key.strip().lower()
                val = session.memory.recall_long_term(key)
                if val:
                    return f"Your {fact_key} is {val}."
                return f"I don't have your {fact_key} saved, sir."
            return "Please specify what you want me to recall, sir."
        except Exception as e:
            logging.error("Recall fact error: %s", e, extra=logging_extra)
            return "I couldn't access that information, sir."
    
    if is_likely_math(command):
        ans = solve_math_api(command)
        try:
            session.memory.add_short_term({"user": command, "response": ans})
        except Exception:
            pass
        return ans
    
    # Default to AI reply (only for complex questions)
    response = jai_reply(command, session)
    try:
        res_lang = detect_language(response)
    except Exception:
        res_lang = 'en'
    try:
        if res_lang != speak_lang and GoogleTranslator is not None:
            response = GoogleTranslator(source='auto', target=speak_lang).translate(response)
    except Exception:
        pass
    try:
        session.memory.add_short_term({"user": command, "response": response})
    except Exception as e:
        logging.error("Memory storage error: %s", e, extra=logging_extra)
    
    # Speak response asynchronously via centralized helper (dedup + logging)
    should_speak = (SPEAK_RESPONSES and tts_module) and (session.tts_enabled or not suppress_tts)
    if should_speak:
        try:
            speak_async_text(response, logging_extra, speak_lang)
        except Exception:
            pass
    return response

# -----------------------------
# FastAPI App
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global screen_watcher_thread, voice_listener_thread
    try:
        if win32gui is not None:
            screen_watcher_thread = ScreenWatcher(interval=SCREEN_WATCH_INTERVAL)
            screen_watcher_thread.start()
        else:
            logging.warning("Screen watcher unavailable", extra={"user": "system"})
    except Exception:
        logging.warning("Screen watcher failed to start", extra={"user": "system"})
    try:
        if ENABLE_VOICE_LISTENER and sr is not None:
            voice_listener_thread = VoiceCommandListener(hotword=VOICE_HOTWORD)
            voice_listener_thread.start()
        else:
            logging.warning("Voice listener unavailable", extra={"user": "system"})
    except Exception:
        logging.warning("Voice listener failed to start", extra={"user": "system"})

    yield

    try:
        if tts_module is not None and hasattr(tts_module, "shutdown"):
            try:
                tts_module.shutdown()
            except Exception:
                pass
    except Exception:
        pass
    try:
        if 'calendar_manager' in globals() and calendar_manager is not None:
            try:
                if getattr(calendar_manager, 'scheduler', None) is not None:
                    calendar_manager.scheduler.shutdown(wait=False)
            except Exception:
                pass
            try:
                if getattr(calendar_manager, 'conn', None) is not None:
                    calendar_manager.conn.close()
            except Exception:
                pass
    except Exception:
        pass
    try:
        if screen_watcher_thread is not None:
            screen_watcher_thread.stop()
    except Exception:
        pass
    try:
        if voice_listener_thread is not None:
            voice_listener_thread.stop()
    except Exception:
        pass

JAI_API_TOKEN = os.environ.get("JAI_API_TOKEN", "")

auth_router = APIRouter()

def require_auth(authorization: Optional[str] = Header(None)):
    return {"session": {"user_id": "public"}}

app = FastAPI(title="JAI Networked Assistant", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount authentication routes
app.include_router(auth_router)

@app.get("/healthz")
def healthz():
    return {"status": "ok", "time": datetime.utcnow().isoformat(), "request_id": request_id_ctx_var.get()}

@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_ctx_var.set(req_id)
    try:
        response = await call_next(request)
    except HTTPException as exc:
        # Re-raise HTTP exceptions so they are handled by FastAPI's handlers
        raise exc
    except Exception as exc:
        logging.error(
            "Unhandled exception: %s %s - %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
            extra={"user": "system"},
        )
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": req_id})
    finally:
        request_id_ctx_var.reset(token)
    response.headers["X-Request-ID"] = req_id
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logging.warning(
        "HTTPException: %s %s -> %s",
        request.method,
        request.url.path,
        exc.detail,
        extra={"user": "system"},
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "request_id": request_id_ctx_var.get()})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.warning(
        "Validation error: %s %s -> %s",
        request.method,
        request.url.path,
        str(exc)[:300],
        extra={"user": "system"},
    )
    return JSONResponse(status_code=422, content={"detail": "Validation error", "request_id": request_id_ctx_var.get()})

class CommandRequest(BaseModel):
    command: str
    suppress_tts: bool = True

@app.post("/command")
def handle_command(cmd: CommandRequest, request: Request):
    key = "public"
    if key not in sessions:
        sessions[key] = UserSession(key)
    session = sessions[key]
    logging_extra = {"user": key}
    logging.info("Received command: %s", cmd.command, extra=logging_extra)
    start_time = datetime.now()
    try:
        response_text = execute_command(cmd.command, session, suppress_tts=cmd.suppress_tts)
    except Exception as e:
        logging.error("Command handler error: %s", e, extra=logging_extra, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id_ctx_var.get()})
    finally:
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        logging.info("Command processed in %d ms", duration_ms, extra=logging_extra)
    
    return {"response": response_text, "request_id": request_id_ctx_var.get()}

 

@app.get("/nasa/apod")
def nasa_apod(date: Optional[str] = None, hd: bool = False, request: Request = None, auth_ctx: dict = Depends(require_auth)):
    s = auth_ctx["session"]
    key = f"auth:{s['user_id']}"
    logging_extra = {"user": key}
    logging.info("NASA APOD request: date=%s hd=%s", date, hd, extra=logging_extra)
    try:
        data = fetch_nasa_apod(date, "hd" if hd else None)
        return {"apod": data, "request_id": request_id_ctx_var.get()}
    except Exception as e:
        logging.error("NASA APOD error: %s", e, extra=logging_extra, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": request_id_ctx_var.get()})

 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
