#!/usr/bin/env python3
"""
Direct voice client - no wake word needed
"""
import os
import sys
import logging
from voice_client import JAIVoiceClient

def main():
    print("🎤 JAI Voice Client - Direct Mode")
    print("=" * 50)
    print("No wake word needed - just speak when prompted!")
    print("=" * 50)
    
    try:
        client = JAIVoiceClient(
            server_url="http://localhost:8080",
            username="user1",
            password="pass1",
            wake_word="dummy"  # Won't be used
        )
        
        print("\n🎤 Listening... Speak your command now!")
        
        # Direct voice session without wake word
        while True:
            try:
                print("\n" + "-" * 40)
                print("🎤 Speak your command (or say 'goodbye' to exit)...")
                
                # Listen directly for command
                command = client.listener.listen_once(timeout=10, phrase_time_limit=10)
                
                if command:
                    print(f"🗣️  You said: {command}")
                    
                    # Check for exit
                    if any(word in command.lower() for word in ["goodbye", "exit", "quit", "bye"]):
                        print("👋 Goodbye!")
                        break
                    
                    # Send to server
                    response = client.send_command(command)
                    print(f"🤖 JAI: {response}")
                    
                    # Speak response (if TTS available)
                    try:
                        from tts import speak, detect_language
                        lang = detect_language(response) if response else "en"
                        speak(response, language=lang)
                    except Exception:
                        pass
                else:
                    print("⏱️  Didn't catch that. Try again...")
                    
            except KeyboardInterrupt:
                print("\n👋 Voice client stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Failed to start voice client: {e}")

if __name__ == "__main__":
    main()
