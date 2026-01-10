# stt.py
"""
Speech-to-Text module for JAI using SpeechRecognition.
Supports wake word detection and continuous listening.
"""
import logging
import os
from typing import Optional, Callable

try:
    import speech_recognition as sr
except ImportError:
    sr = None
    logging.warning("SpeechRecognition not available. Install: pip install SpeechRecognition")


class VoiceListener:
    """Handles voice input with wake word detection."""
    
    def __init__(self, wake_word: str = "Activate aj", language: str = "en-US"):
        if not sr:
            raise ImportError("SpeechRecognition not installed")
        
        self.recognizer = sr.Recognizer()
        self.wake_word = wake_word.lower()
        self.language = language
        self.fallback_langs = [s.strip() for s in os.environ.get("VOICE_LISTENER_LANGS", "en-US,ur-PK,ar-SA").split(",") if s.strip()]
        if self.language not in self.fallback_langs:
            self.fallback_langs.insert(0, self.language)
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 1.5
        self.recognizer.non_speaking_duration = 0.5
        try:
            self.recognizer.phrase_threshold = 0.1
        except Exception:
            pass
        
        # Adjust for ambient noise on initialization
        try:
            with sr.Microphone() as source:
                logging.info("Calibrating for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                logging.info("Microphone ready")
        except Exception as e:
            logging.error("Microphone initialization failed: %s", e)
    
    def listen_once(self, timeout: int = 20, phrase_time_limit: int = 30) -> Optional[str]:
        """
        Listen for a single voice command.
        
        Args:
            timeout: Seconds to wait for speech to start
            phrase_time_limit: Max seconds for the phrase
            
        Returns:
            Recognized text or None if failed
        """
        try:
            with sr.Microphone() as source:
                logging.info("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                
            logging.info("Processing speech...")
            langs_env = [s.strip() for s in os.environ.get("VOICE_LISTENER_LANGS", "en-US,ur-PK,ar-SA").split(",") if s.strip()]
            tried = []
            for lang_try in [self.language] + [l for l in langs_env if l not in tried]:
                tried.append(lang_try)
                try:
                    text = self.recognizer.recognize_google(audio, language=lang_try)
                    logging.info("Recognized (%s): %s", lang_try, text)
                    return text
                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    continue
            return None
            
        except sr.WaitTimeoutError:
            logging.warning("Listening timed out")
            return None
        except sr.UnknownValueError:
            logging.warning("Could not understand audio")
            return None
        except sr.RequestError as e:
            logging.error("Speech recognition service error: %s", e)
            return None
        except Exception as e:
            logging.error("Unexpected error in listen_once: %s", e)
            return None
    
    def wait_for_wake_word(self, timeout: int = 30) -> bool:
        """
        Wait for the wake word to be spoken.
        
        Args:
            timeout: Seconds to wait before giving up
            
        Returns:
            True if wake word detected, False otherwise
        """
        logging.info("Waiting for wake word: '%s'", self.wake_word)
        text = self.listen_once(timeout=timeout, phrase_time_limit=10)
        
        if text and self.wake_word in text.lower():
            logging.info("Wake word detected!")
            return True
        
        return False
    
    def listen_with_wake_word(self, 
                              on_command: Callable[[str], None],
                              on_wake: Optional[Callable[[], None]] = None,
                              continuous: bool = False) -> None:
        """
        Listen for wake word, then capture command.
        
        Args:
            on_command: Callback function to handle recognized commands
            on_wake: Optional callback when wake word is detected
            continuous: If True, keep listening after each command
        """
        while True:
            if self.wait_for_wake_word():
                if on_wake:
                    on_wake()
                
                # Listen for the actual command
                command = self.listen_once(timeout=20, phrase_time_limit=30)
                
                if command:
                    on_command(command)
                else:
                    logging.warning("No command received after wake word")
                
                if not continuous:
                    break
            else:
                if not continuous:
                    break


def listen_for_command(timeout: int = 20, language: str = "en-US") -> Optional[str]:
    """
    Simple one-shot voice command listener (no wake word).
    
    Args:
        timeout: Seconds to wait for speech
        language: Language code (e.g., 'en-US', 'hi-IN')
        
    Returns:
        Recognized text or None
    """
    if not sr:
        logging.error("SpeechRecognition not available")
        return None
    
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.pause_threshold = 1.5
    recognizer.non_speaking_duration = 0.5
    
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            logging.info("Listening for command...")
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=20)
        
        langs_env = [s.strip() for s in os.environ.get("VOICE_LISTENER_LANGS", "en-US,ur-PK,ar-SA").split(",") if s.strip()]
        tried = []
        for lang_try in [language] + [l for l in langs_env if l not in tried]:
            tried.append(lang_try)
            try:
                text = recognizer.recognize_google(audio, language=lang_try)
                logging.info("Recognized (%s): %s", lang_try, text)
                return text
            except sr.UnknownValueError:
                continue
            except sr.RequestError:
                continue
        return None
        
    except Exception as e:
        logging.error("Voice recognition error: %s", e)
        return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Testing voice listener...")
    print("Say 'Activate aj' followed by a command")
    
    def handle_command(cmd: str):
        print(f"Command received: {cmd}")
    
    def on_wake():
        print("JAI is listening...")
    
    try:
        listener = VoiceListener(wake_word="Activate aj")
        listener.listen_with_wake_word(on_command=handle_command, on_wake=on_wake, continuous=False)
    except Exception as e:
        print(f"Error: {e}")
