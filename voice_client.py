#!/usr/bin/env python3
# voice_client.py
"""
Voice client for JAI - enables voice interaction with the assistant.
Listens for wake word, captures commands, sends to JAI server, and speaks responses.
"""
import os
import sys
import logging
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import re

# Import JAI modules
try:
    from stt import VoiceListener
    from tts import speak, detect_language
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure stt.py and tts.py are in the same directory")
    sys.exit(1)

# Setup logging - only to file, UTF-8 to support non-ASCII (e.g., Arabic)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_client.log', encoding='utf-8')
    ]
)

# Load configuration
load_dotenv()

JAI_SERVER = os.environ.get("JAI_SERVER", "http://localhost:8001")
JAI_USERNAME = os.environ.get("JAI_USERNAME", "user1")
JAI_PASSWORD = os.environ.get("JAI_PASSWORD", "pass1")
WAKE_WORD = os.environ.get("WAKE_WORD", "Activate aj")
TTS_VOICE = os.environ.get("TTS_VOICE", None)


class JAIVoiceClient:
    """Voice client for interacting with JAI server."""
    
    def __init__(self, server_url: str, username: str, password: str, wake_word: str = "Activate aj"):
        self.server_url = server_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, password)
        self.wake_word = wake_word
        self._switch_to_text = False
        self._switch_to_voice = False
        
        # Initialize voice listener
        try:
            self.listener = VoiceListener(wake_word=wake_word)
            logging.info("Voice listener initialized")
        except Exception as e:
            logging.error("Failed to initialize voice listener: %s", e)
            raise
    
    def send_command(self, command: str) -> str:
        """
        Send command to JAI server and get response.
        
        Args:
            command: Voice command text
            
        Returns:
            JAI's response
        """
        try:
            response = requests.post(
                f"{self.server_url}/command",
                json={"command": command, "suppress_tts": True},
                auth=self.auth,
                timeout=60  # Increased to 60s for AI responses with Gemini
            )
            response.raise_for_status()
            data = response.json()
            return data.get('response', 'No response from JAI')
            
        except requests.exceptions.ConnectionError:
            return "Cannot connect to JAI server. Is it running?"
        except requests.exceptions.Timeout:
            return "JAI server timed out. Please try again."
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return "Authentication failed. Check your credentials."
            return f"Server error: {e.response.status_code}"
        except Exception as e:
            logging.error("Command failed: %s", e)
            return f"Error: {str(e)}"
    
    def handle_command(self, command: str) -> bool:
        """
        Handle a voice command.
        
        Returns:
            True to continue session, False to exit
        """
        logging.info("Command: %s", command)
        print(f"\n🎤 You: {command}")
        
        # Check for exit commands
        exit_phrases = ["goodbye", "good bye", "see you soon", "exit", "quit", "bye"]
        if any(phrase in command.lower() for phrase in exit_phrases):
            farewell = "Goodbye! Have a great day!"
            print(f"🤖 AJ: {farewell}\n")
            try:
                speak(farewell)
            except Exception:
                pass
            return False
        
        cmd_lower = command.lower()
        if re.search(r"\bactivate\s+text(?:\s+mode)?\b", cmd_lower):
            self._switch_to_text = True
        elif re.search(r"\bactivate\s+voice(?:\s+mode)?\b", cmd_lower):
            self._switch_to_voice = True
        
        # Send to JAI server
        response = self.send_command(command)
        logging.info("Response: %s", response)
        print(f"🤖 AJ: {response}\n")
        
        # Speak the response in detected language of the text
        try:
            lang = detect_language(response) if response else "en"
            speak(response, language=lang)
        except Exception as e:
            logging.error("TTS failed: %s", e)
        
        return True
    
    def conversation_session(self):
        print("\n✅ Session started! You can now ask questions continuously.")
        try:
            speak("Voice mode activated. I'm listening!", language="en")
        except Exception:
            pass
        self._voice_only_session()
    
    def _text_only_session(self):
        """Text-only conversation mode."""
        print("\n⌨️  TEXT MODE: Type your commands below")
        print("👋 Type 'goodbye' or 'exit' to end session\n")
        
        try:
            speak("Text mode activated. I'm ready!")
        except Exception:
            pass
        
        while True:
            try:
                command = input("💬 You: ").strip()
                
                if not command:
                    continue
                
                should_continue = self.handle_command(command)
                if self._switch_to_voice:
                    self._switch_to_voice = False
                    print("\n🎤 Switching to VOICE MODE...\n")
                    self._voice_only_session()
                    return
                if not should_continue:
                    break
                    
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Session ended.")
                break
    
    def _voice_only_session(self):
        """Voice-only conversation mode."""
        print("\n🎤 VOICE MODE: Speak your commands")
        print("👋 Say 'goodbye' or 'exit' to end session\n")
        
        try:
            speak("Voice mode activated. I'm listening!", language="en")
        except Exception:
            pass
        
        while True:
            print("🎤 Listening...")
            command = self.listener.listen_once(timeout=30, phrase_time_limit=30)
            
            if command:
                should_continue = self.handle_command(command)
                if self._switch_to_text:
                    self._switch_to_text = False
                    print("\n⌨️  Switching to TEXT MODE...\n")
                    self._text_only_session()
                    return
                if not should_continue:
                    break
            else:
                print("⏱️  No speech detected. Still listening...\n")
    
    def run(self, continuous: bool = True):
        """
        Run the voice client.
        
        Args:
            continuous: If True, keep listening after each command
        """
        print("=" * 60)
        print("AJ Voice Assistant")
        print("=" * 60)
        print(f"Server: {self.server_url}")
        print(f"Wake word: '{self.wake_word}'")
        print("=" * 60)
        print("👋 Say 'goodbye' or 'exit' to end session")
        print("⌨️  Press Ctrl+C to force quit\n")
        try:
            while True:
                print(f"Waiting for wake word: '{self.wake_word}'...")
                if self.listener.wait_for_wake_word(timeout=300):
                    print("\n👂 Wake word detected!")
                    try:
                        speak("Yes, I'm here!")
                    except Exception:
                        pass
                    self._voice_only_session()
                    print("\n" + "=" * 60)
                    print("Session ended. Say your wake word to start again.")
                    print("=" * 60 + "\n")
                else:
                    print("Wake word not detected in time. Still listening...\n")
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down AJ voice client...")
            logging.info("Voice client stopped by user")
        except Exception as e:
            logging.error("Voice client error: %s", e)
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="JAI Voice Client")
    parser.add_argument('--server', default=JAI_SERVER, help='JAI server URL')
    parser.add_argument('--username', default=JAI_USERNAME, help='Username')
    parser.add_argument('--password', default=JAI_PASSWORD, help='Password')
    parser.add_argument('--wake-word', default=WAKE_WORD, help='Wake word')
    parser.add_argument('--single', action='store_true', help='Single command mode (exit after one command)')
    
    args = parser.parse_args()
    
    try:
        client = JAIVoiceClient(
            server_url=args.server,
            username=args.username,
            password=args.password,
            wake_word=args.wake_word
        )
        client.run(continuous=not args.single)
    except Exception as e:
        print(f"Failed to start voice client: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
