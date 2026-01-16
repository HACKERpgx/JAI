#!/usr/bin/env python3
"""
Test what happens when you speak commands to JAI
"""
import os
import sys
from voice_client import JAIVoiceClient

def main():
    print("🎤 JAI Voice Action Test")
    print("=" * 50)
    print("This will test what JAI hears and how it responds")
    print("Try commands like:")
    print("- 'what time is it'")
    print("- 'open calculator'") 
    print("- 'tell me a joke'")
    print("- 'what's the weather'")
    print("- 'play music'")
    print("- 'say goodbye' to exit")
    print("=" * 50)
    
    try:
        client = JAIVoiceClient(
            server_url="http://localhost:8080",
            username="user1",
            password="pass1",
            wake_word="hello"
        )
        
        print("\n🎤 Say 'hello' to start, then try commands...")
        
        # Simple direct listening loop
        while True:
            try:
                print("\n" + "-" * 40)
                print("🎤 Listening... (say a command or 'goodbye')")
                
                # Listen for command
                command = client.listener.listen_once(timeout=15, phrase_time_limit=10)
                
                if command:
                    print(f"🗣️  I heard: '{command}'")
                    
                    # Check for exit
                    if any(word in command.lower() for word in ["goodbye", "exit", "quit", "bye"]):
                        print("👋 Goodbye!")
                        try:
                            from tts import speak
                            speak("Goodbye! Have a great day!")
                        except:
                            pass
                        break
                    
                    # Send to server
                    print("🤖 Processing...")
                    response = client.send_command(command)
                    print(f"🤖 JAI says: {response}")
                    
                    # Check if it's an action
                    action_keywords = ["opening", "playing", "searching", "setting", "scheduling", "launching"]
                    is_action = any(keyword in response.lower() for keyword in action_keywords)
                    
                    if is_action:
                        print("✅ ACTION PERFORMED!")
                    else:
                        print("💬 RESPONSE GIVEN")
                    
                    # Speak response
                    try:
                        from tts import speak, detect_language
                        lang = detect_language(response) if response else "en"
                        speak(response, language=lang)
                    except Exception as e:
                        print(f"(TTS error: {e})")
                        
                else:
                    print("❌ Didn't hear anything. Please speak clearly.")
                    print("💡 Tips:")
                    print("   - Speak clearly and moderately loud")
                    print("   - Wait for the 'Listening...' prompt")
                    print("   - Try simple commands like 'what time is it'")
                    
            except KeyboardInterrupt:
                print("\n👋 Test stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Failed to start voice test: {e}")

if __name__ == "__main__":
    main()
