"""
Test script to verify TTS functionality directly.
Run this to check if text-to-speech is working properly.
"""
import pyttsx3
import sys

def test_tts():
    print("=== Testing TTS Functionality ===")
    
    try:
        # Initialize the TTS engine
        engine = pyttsx3.init()
        print("\n✅ TTS Engine initialized successfully")
        
        # Get and display available voices
        voices = engine.getProperty('voices')
        print("\n🔊 Available voices:")
        for i, voice in enumerate(voices):
            print(f"{i+1}. {voice.name} (ID: {voice.id})")
            print(f"   Languages: {voice.languages if hasattr(voice, 'languages') else 'Not specified'}")
        
        # Set properties
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)
        
        # Try different voices
        test_messages = [
            ("Hello, this is a test of the text-to-speech system.", "English"),
            ("ہیلو، یہ اردو میں ایک ٹیسٹ ہے۔", "Urdu"),
            ("مرحباً، هذا اختبار للغة العربية.", "Arabic"),
            ("Bonjour, ceci est un test en français.", "French")
        ]
        
        print("\n🔊 Testing voices with different languages...")
        for msg, lang in test_messages:
            print(f"\nSpeaking in {lang}: {msg}")
            engine.say(msg)
            engine.runAndWait()
        
        print("\n✅ TTS test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during TTS test: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure you have a TTS engine installed")
        print("   - On Windows: Check in Control Panel > Speech Recognition > Text to Speech")
        print("2. Install additional voices if needed")
        print("3. Check your system's volume is not muted")
        print("4. Try running as administrator")
        return False
    
    return True

if __name__ == "__main__":
    print("JAI TTS Test Script")
    print("==================")
    test_tts()
