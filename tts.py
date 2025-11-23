# tts.py
"""
Enhanced Text-to-Speech utilities for JAI with multilingual support.
Supports English, Urdu, Arabic, and French with appropriate voice selection.
"""
import threading
import queue
import logging
import re
import os
from typing import Optional, Dict, Tuple, List

# TTS engine is required; detect_language helpers are optional
try:
    import pyttsx3
except ImportError as e:
    logging.warning("pyttsx3 not available: %s", e)
    pyttsx3 = None

# Optional: language detection
try:
    import langdetect
    from langdetect import DetectorFactory, LangDetectException
    DetectorFactory.seed = 0
except Exception:
    langdetect = None
    class LangDetectException(Exception):
        pass

# Optional: country/locale info (not strictly required)
try:
    import pycountry
except Exception:
    pycountry = None

# Voice and language preferences via environment variables
TTS_PREFERRED_VOICE = (os.environ.get("TTS_PREFERRED_VOICE", "") or "").lower()
TTS_FORCE_LANGUAGE = (os.environ.get("TTS_FORCE_LANGUAGE", "") or "").lower()
_TTS_LOCK = threading.Lock()
_ENGINE_INIT_LOCK = threading.Lock()
_ENGINE = None

# Language to voice mapping for better TTS quality
LANGUAGE_VOICE_MAPPING = {
    'en': {
        'name': 'English',
        'gender': 'male',
        'keywords': ['david', 'mark', 'male', 'english', 'en-'],
        'rtl': False,
        'rate': 150
    },
    'ur': {
        'name': 'Urdu',
        'gender': 'female', 
        'keywords': ['urdu', 'ur-', 'pakistan', 'zira'],
        'rtl': True,
        'rate': 130
    },
    'ar': {
        'name': 'Arabic',
        'gender': 'male',
        'keywords': ['arabic', 'ar-', 'hoda', 'naayef'],
        'rtl': True,
        'rate': 130
    },
    'fr': {
        'name': 'French',
        'gender': 'female',
        'keywords': ['french', 'fr-', 'hélène', 'zira'],
        'rtl': False,
        'rate': 140
    }
}

# Common phrases in different languages
COMMON_PHRASES = {
    'en': {
        'listening': 'I am listening...',
        'not_understood': "I'm sorry, I didn't understand that.",
        'ready': 'I am ready to help!',
        'goodbye': 'Goodbye! Have a great day!',
        'error': 'I apologize, but I encountered an error.'
    },
    'ur': {
        'listening': 'میں سن رہا ہوں...',
        'not_understood': 'معذرت، میں آپ کی بات نہیں سمجھ سکا۔',
        'ready': 'میں مدد کے لیے تیار ہوں!',
        'goodbye': 'الوداع! آپ کا دن اچھا گزرے!',
        'error': 'معذرت، لیکن مجھے ایک مسئلہ پیش آیا ہے۔'
    },
    'ar': {
        'listening': 'أنا أستمع...',
        'not_understood': 'عذراً، لم أفهم ما تقول.',
        'ready': 'أنا مستعد للمساعدة!',
        'goodbye': 'إلى اللقاء! أتمنى لك يوماً سعيداً!',
        'error': 'أعتذر، لكن واجهت مشكلة.'
    },
    'fr': {
        'listening': 'J\'écoute...',
        'not_understood': 'Désolé, je n\'ai pas compris.',
        'ready': 'Je suis prêt à vous aider!',
        'goodbye': 'Au revoir! Passez une excellente journée!',
        'error': 'Je m\'excuse, mais j\'ai rencontré une erreur.'
    }
}

def detect_language(text: str) -> str:
    """
    Detect the language of the given text with improved accuracy.
    Returns language code ('en', 'ur', 'ar', 'fr').
    """
    if not text.strip():
        return 'en'
        
    text_lower = text.lower().strip()
    
    # Check for specific language patterns first
    
    # Check for Arabic script (Arabic, Urdu, Persian, etc.)
    arabic_script = any('\u0600' <= char <= '\u06FF' for char in text)
    
    if arabic_script:
        # Check for Urdu-specific characters
        urdu_chars = ['پ', 'ٹ', 'چ', 'ڈ', 'ڑ', 'ژ', 'ک', 'گ', 'ں', 'ہ', 'ھ', 'ے']
        if any(char in text for char in urdu_chars):
            return 'ur'  # Urdu
        return 'ar'  # Default to Arabic for other Arabic script
    
    # Check for French indicators
    french_indicators = [
        'le ', 'la ', 'les ', 'un ', 'une ', 'des ', 'je ', 'tu ', 'il ', 'elle ',
        'nous ', 'vous ', 'ils ', 'elles', 'bonjour', 'merci', 'au revoir',
        'comment ça va', 'je m\'appelle', 's\'il vous plaît', 'excusez-moi'
    ]
    if any(indicator in text_lower for indicator in french_indicators):
        return 'fr'
    
    # Check for English indicators (as fallback)
    english_indicators = [
        'the ', 'and ', 'ing ', 'tion ', 'you ', 'are ', 'is ', 'am ', 'hello',
        'hi ', 'how are you', 'what\'s up', 'good morning', 'good night'
    ]
    if any(indicator in text_lower for indicator in english_indicators):
        return 'en'
    
    # Use langdetect as fallback
    try:
        lang = langdetect.detect(text)
        # Map to our supported languages
        if lang.startswith('ar'):
            return 'ar'
        elif lang.startswith('ur') or lang.startswith('hi') or lang.startswith('fa'):
            return 'ur'  # Map Hindi/Farsi to Urdu for now
        elif lang.startswith('fr'):
            return 'fr'
        return 'en'  # Default to English
    except (LangDetectException, Exception):
        return 'en'  # Default to English on error

def _select_voice(engine, language: str = 'en') -> bool:
    """
    Select the best available voice for the specified language.
    Returns True if a suitable voice was found, False otherwise.
    """
    try:
        if not pyttsx3:
            return False
        voices = engine.getProperty('voices')
        if not voices:
            logging.warning("No voices available")
            return False
        # Get language settings
        lang_settings = LANGUAGE_VOICE_MAPPING.get(language, LANGUAGE_VOICE_MAPPING['en'])
        target_gender = lang_settings['gender']
        keywords = lang_settings['keywords']
        logging.info(f"Looking for {language} voice with keywords: {keywords}")
        # Prefer explicitly configured voice if available
        if TTS_PREFERRED_VOICE:
            for voice in voices:
                voice_name = (voice.name or '').lower()
                if TTS_PREFERRED_VOICE in voice_name:
                    try:
                        engine.setProperty('voice', voice.id)
                        logging.info(f"Selected preferred voice: {voice.name}")
                        return True
                    except Exception:
                        pass
        # Score each voice based on how well it matches our requirements
        voice_scores = []
        for voice in voices:
            score = 0
            voice_name = (voice.name or '').lower()
            voice_lang = ''
            # Get voice language if available
            if hasattr(voice, 'languages') and voice.languages:
                voice_lang = (voice.languages[0] or '').lower()
            # Check for language match
            if language in voice_lang or any(lang in voice_lang for lang in ['en-us', 'en_gb'] if language == 'en'):
                score += 100
            # Check for keyword matches
            for keyword in keywords:
                if keyword in voice_name:
                    score += 50
            # Check for gender match
            if target_gender in voice_name:
                score += 30
            voice_scores.append((score, voice))
        # Sort by score (highest first)
        voice_scores.sort(reverse=True, key=lambda x: x[0])
        # Log available voices for debugging
        logging.info(f"Available voices (language: {language}):")
        for score, voice in voice_scores[:5]:  # Log top 5 voices
            logging.info(f"- {voice.name} (score: {score})")
        # Select the best voice
        if voice_scores and voice_scores[0][0] > 0:
            best_voice = voice_scores[0][1]
            engine.setProperty('voice', best_voice.id)
            logging.info(f"Selected voice: {best_voice.name}")
            return True
        # Fallback to first available voice
        if voices:
            engine.setProperty('voice', voices[0].id)
            logging.warning(f"No ideal voice found for {language}, using: {voices[0].name}")
            return True
        return False
    except Exception as e:
        logging.error(f"Error selecting voice: {e}", exc_info=True)
        return False

def _get_engine(language: Optional[str] = None):
    global _ENGINE
    if not pyttsx3:
        return None
    with _ENGINE_INIT_LOCK:
        if _ENGINE is None:
            try:
                _ENGINE = pyttsx3.init()
            except Exception as e:
                logging.error(f"Error initializing TTS engine: {e}", exc_info=True)
                _ENGINE = None
    return _ENGINE

def speak(text: str, language: Optional[str] = None, rate: Optional[int] = None, 
          volume: float = 0.9, timeout: int = 20) -> bool:
    """
    Speak the given text in the specified language with proper voice selection.
    
    Args:
        text: The text to speak
        language: Language code (en, ur, ar, fr). If None, auto-detects language.
        rate: Speech rate (words per minute). If None, uses language default.
        volume: Volume (0.0 to 1.0)
        timeout: Maximum time to wait for speech to complete (seconds)
    
    Returns:
        bool: True if speech was successful, False otherwise
    """
    if not pyttsx3:
        logging.error("TTS engine not available. Install pyttsx3: pip install pyttsx3")
        return False
    
    if not text.strip():
        logging.warning("Empty text provided to speak")
        return False

    # Auto-detect language if not specified
    if not language:
        if TTS_FORCE_LANGUAGE:
            language = TTS_FORCE_LANGUAGE
        else:
            language = detect_language(text)
    
    # Get language settings
    lang_settings = LANGUAGE_VOICE_MAPPING.get(language, LANGUAGE_VOICE_MAPPING['en'])
    
    # Set language-specific parameters
    if rate is None:
        rate = lang_settings.get('rate', 150)
    
    # For RTL languages (Arabic, Urdu), add RTL markers
    if lang_settings.get('rtl', False):
        text = f"\u202B{text}\u202C"
    
    logging.info(f"Speaking in {language} (rate: {rate}, volume: {volume}): {text[:100]}...")
    
    result_q: queue.Queue[bool | str] = queue.Queue()

    def run():
        try:
            with _TTS_LOCK:
                engine = _get_engine(language)
                if engine is None:
                    result_q.put("No TTS engine")
                    return
                if not _select_voice(engine, language):
                    logging.warning(f"Could not find suitable voice for language: {language}")
                engine.setProperty('rate', rate)
                engine.setProperty('volume', volume)
                engine.say(text)
                engine.runAndWait()
                result_q.put(True)
        
        except Exception as e:
            error_msg = f"TTS error: {str(e)}"
            logging.error(error_msg, exc_info=True)
            result_q.put(error_msg)
    
    try:
        # Run the TTS in a separate thread with timeout
        th = threading.Thread(target=run, daemon=True)
        th.start()
        th.join(timeout)
        
        if th.is_alive():
            logging.error(f"TTS timed out after {timeout} seconds")
            return False
            
        # Check if there was an error
        if not result_q.empty():
            result = result_q.get()
            if isinstance(result, str):  # Error message
                logging.error(f"TTS error: {result}")
                return False
            return result
            
        return False
        
    except Exception as e:
        logging.error(f"TTS thread error: {e}", exc_info=True)
        return False
