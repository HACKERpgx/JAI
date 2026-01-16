#!/usr/bin/env python3
import requests
import sys
from stt import VoiceListener

def test_server():
    try:
        r = requests.get('http://localhost:8080/api/health', timeout=5)
        print(f"✅ Server status: {r.status_code}")
        print(f"Response: {r.json()}")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

def test_microphone():
    try:
        print("🎤 Testing microphone...")
        listener = VoiceListener(wake_word="test")
        print("✅ Microphone initialized successfully")
        print("📡 Available microphones:")
        import speech_recognition as sr
        for i, mic in enumerate(sr.Microphone.list_microphone_names()):
            print(f"  {i}: {mic}")
        return True
    except Exception as e:
        print(f"❌ Microphone error: {e}")
        return False

def test_voice_recognition():
    try:
        print("\n🎯 Testing voice recognition (say something in 5 seconds)...")
        listener = VoiceListener(wake_word="test")
        result = listener.listen_once(timeout=5, phrase_time_limit=5)
        if result:
            print(f"✅ Recognized: {result}")
            return True
        else:
            print("⚠️ No speech detected")
            return False
    except Exception as e:
        print(f"❌ Voice recognition error: {e}")
        return False

if __name__ == "__main__":
    print("=== JAI Voice System Test ===")
    
    # Test server
    server_ok = test_server()
    
    # Test microphone
    mic_ok = test_microphone()
    
    # Test voice recognition
    voice_ok = test_voice_recognition()
    
    print(f"\n=== Results ===")
    print(f"Server: {'✅' if server_ok else '❌'}")
    print(f"Microphone: {'✅' if mic_ok else '❌'}")
    print(f"Voice Recognition: {'✅' if voice_ok else '❌'}")
    
    if server_ok and mic_ok:
        print("\n🚀 You can now run the voice client:")
        print("   python voice_client.py")
    else:
        print("\n⚠️ Fix the issues above before using voice mode")
