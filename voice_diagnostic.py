#!/usr/bin/env python3
"""
Voice mode diagnostic script for JAI Assistant
Tests each component individually to identify issues
"""
import os
import sys
import logging
import time
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_imports():
    """Test all required imports"""
    print("🔍 Testing imports...")
    try:
        import speech_recognition as sr
        print(f"✅ SpeechRecognition: {sr.__version__}")
    except ImportError as e:
        print(f"❌ SpeechRecognition: {e}")
        return False
    
    try:
        import pyttsx3
        print(f"✅ pyttsx3: {pyttsx3.__version__}")
    except ImportError as e:
        print(f"❌ pyttsx3: {e}")
        return False
    
    try:
        import pyaudio
        print("✅ pyaudio: Available")
    except ImportError as e:
        print(f"❌ pyaudio: {e}")
        return False
    
    try:
        from stt import VoiceListener
        print("✅ VoiceListener: Available")
    except ImportError as e:
        print(f"❌ VoiceListener: {e}")
        return False
    
    try:
        from tts import speak, detect_language
        print("✅ TTS functions: Available")
    except ImportError as e:
        print(f"❌ TTS functions: {e}")
        return False
    
    return True

def test_microphone_access():
    """Test microphone access and permissions"""
    print("\n🎤 Testing microphone access...")
    try:
        import speech_recognition as sr
        
        # List available microphones
        mics = sr.Microphone.list_microphone_names()
        print(f"📡 Found {len(mics)} microphones:")
        for i, mic in enumerate(mics[:5]):  # Show first 5
            print(f"  {i}: {mic}")
        
        # Try to access default microphone
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("🔧 Calibrating for ambient noise...")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone access successful")
            return True
    except Exception as e:
        print(f"❌ Microphone access failed: {e}")
        return False

def test_voice_listener():
    """Test VoiceListener initialization"""
    print("\n👂 Testing VoiceListener...")
    try:
        from stt import VoiceListener
        
        # Test with different wake words
        wake_words = ["hello", "test", "activate aj"]
        for wake_word in wake_words:
            try:
                listener = VoiceListener(wake_word=wake_word)
                print(f"✅ VoiceListener initialized with wake word: '{wake_word}'")
                return True
            except Exception as e:
                print(f"❌ Failed with '{wake_word}': {e}")
                continue
        
        return False
    except Exception as e:
        print(f"❌ VoiceListener test failed: {e}")
        return False

def test_tts():
    """Test text-to-speech"""
    print("\n🔊 Testing TTS...")
    try:
        from tts import speak
        
        # Test simple speech
        print("🗣️  Testing speech synthesis...")
        result = speak("Voice mode test successful", language="en")
        if result:
            print("✅ TTS working")
            return True
        else:
            print("❌ TTS failed")
            return False
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        return False

def test_server_connection():
    """Test connection to JAI server"""
    print("\n🌐 Testing server connection...")
    try:
        import requests
        
        # Test health endpoint
        response = requests.get('http://localhost:8080/api/health', timeout=5)
        if response.status_code == 200:
            print(f"✅ Server responding: {response.json()}")
            return True
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return False

def test_voice_command():
    """Test a simple voice command"""
    print("\n🎯 Testing voice command (say 'hello' in 5 seconds)...")
    try:
        from stt import VoiceListener
        
        listener = VoiceListener(wake_word="hello")
        print("🎤 Listening for 'hello'...")
        
        # Quick test with shorter timeout
        result = listener.listen_once(timeout=5, phrase_time_limit=3)
        if result:
            print(f"✅ Recognized: '{result}'")
            return True
        else:
            print("⚠️ No speech detected (this is normal if you didn't speak)")
            return True  # Not a failure, just no input
    except Exception as e:
        print(f"❌ Voice command test failed: {e}")
        return False

def main():
    """Run all diagnostic tests"""
    print("=== JAI Voice Mode Diagnostic ===\n")
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    tests = [
        ("Imports", test_imports),
        ("Microphone Access", test_microphone_access),
        ("VoiceListener", test_voice_listener),
        ("TTS", test_tts),
        ("Server Connection", test_server_connection),
        ("Voice Command", test_voice_command),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results[name] = False
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print("\n" + "="*50)
    print("DIAGNOSTIC SUMMARY")
    print("="*50)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\n🚀 To activate voice mode:")
        print("1. Run: python voice_client.py")
        print("2. Say the wake word: 'Activate aj'")
        print("3. Or use the web interface at http://localhost:3000")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("\n🔧 Troubleshooting:")
        if not results.get("Imports", False):
            print("• Install missing dependencies: pip install -r requirements.txt")
        if not results.get("Microphone Access", False):
            print("• Check microphone permissions in Windows")
            print("• Ensure microphone is not muted")
        if not results.get("Server Connection", False):
            print("• Start the JAI server: python main.py")
        if not results.get("VoiceListener", False):
            print("• Check audio drivers and microphone hardware")
    
    print("\n💡 For web interface voice mode:")
    print("• Open http://localhost:3000")
    print("• Click the microphone button")
    print("• Allow browser microphone access")

if __name__ == "__main__":
    main()
