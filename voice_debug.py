#!/usr/bin/env python3
"""
Debug voice mode issues step by step
"""
import os
import sys
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_voice_to_text():
    """Test voice recognition directly"""
    print("🎤 Testing Voice-to-Text...")
    try:
        from stt import VoiceListener
        
        listener = VoiceListener(wake_word="hello")
        print("✅ VoiceListener initialized")
        print("🗣️  Say something in 5 seconds...")
        
        result = listener.listen_once(timeout=5, phrase_time_limit=3)
        if result:
            print(f"✅ Voice recognized: '{result}'")
            return result
        else:
            print("⚠️ No voice detected (try speaking louder/clearer)")
            return None
            
    except Exception as e:
        print(f"❌ Voice-to-Text error: {e}")
        return None

def test_server_with_text(text):
    """Test server with text command"""
    print(f"\n🤖 Testing server with text: '{text}'")
    try:
        response = requests.post(
            "http://localhost:8080/command",
            json={"command": text, "suppress_tts": True},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server response: {data.get('response', 'N/A')[:100]}")
            return data.get('response', '')
        else:
            print(f"❌ Server error: {response.status_code} - {response.text[:100]}")
            return None
            
    except Exception as e:
        print(f"❌ Server connection error: {e}")
        return None

def test_voice_client_directly():
    """Test voice client directly"""
    print("\n🎯 Testing Voice Client directly...")
    try:
        from voice_client import JAIVoiceClient
        
        client = JAIVoiceClient(
            server_url="http://localhost:8080",
            username="user1",
            password="pass1",
            wake_word="hello"
        )
        
        # Test with a simple text command
        response = client.send_command("what time is it")
        if "Cannot connect" in response:
            print("❌ Voice client cannot connect to server")
            return False
        else:
            print(f"✅ Voice client working: {response[:100]}")
            return True
            
    except Exception as e:
        print(f"❌ Voice client error: {e}")
        return False

def test_wake_word_detection():
    """Test wake word detection"""
    print("\n👂 Testing Wake Word Detection...")
    try:
        from stt import VoiceListener
        
        listener = VoiceListener(wake_word="activate aj")
        print("✅ Wake word listener initialized")
        print("🗣️  Say 'activate aj' in 10 seconds...")
        
        detected = listener.wait_for_wake_word(timeout=10)
        if detected:
            print("✅ Wake word detected!")
            return True
        else:
            print("⚠️ Wake word not detected (try saying 'activate aj' clearly)")
            return False
            
    except Exception as e:
        print(f"❌ Wake word detection error: {e}")
        return False

def main():
    print("=" * 60)
    print("JAI VOICE MODE DEBUG")
    print("=" * 60)
    
    # Test 1: Voice client connection
    voice_client_ok = test_voice_client_directly()
    
    # Test 2: Voice to text
    voice_text = test_voice_to_text()
    
    # Test 3: Server with text (if voice was detected)
    if voice_text:
        server_response = test_server_with_text(voice_text)
    else:
        # Test with a predefined text
        server_response = test_server_with_text("hello")
    
    # Test 4: Wake word detection
    wake_word_ok = test_wake_word_detection()
    
    print("\n" + "=" * 60)
    print("DEBUG SUMMARY")
    print("=" * 60)
    
    print(f"Voice Client:     {'✅' if voice_client_ok else '❌'}")
    print(f"Voice Recognition: {'✅' if voice_text else '❌'}")
    print(f"Server Response:  {'✅' if server_response else '❌'}")
    print(f"Wake Word:        {'✅' if wake_word_ok else '❌'}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    if not voice_client_ok:
        print("❌ Voice client cannot connect to server")
        print("   • Ensure JAI server is running: python jai_assistant.py")
        print("   • Check if port 8080 is blocked")
    
    if not voice_text:
        print("❌ Voice recognition not working")
        print("   • Check microphone permissions")
        print("   • Try speaking louder and clearer")
        print("   • Ensure microphone is not muted")
    
    if not server_response:
        print("❌ Server not responding properly")
        print("   • Check server logs for errors")
        print("   • API quota issues (but GROQ is working)")
    
    if not wake_word_ok:
        print("❌ Wake word detection failing")
        print("   • Try saying 'activate aj' slowly and clearly")
        print("   • Minimize background noise")
        print("   • Check microphone quality")
    
    if voice_client_ok and server_response:
        print("\n🎉 CORE SYSTEMS WORKING!")
        print("Voice mode should work. Issues might be:")
        print("• Microphone permissions")
        print("• Background noise interference")
        print("• Wake word pronunciation")
        
        print("\n📋 Try these steps:")
        print("1. Run: python voice_client.py")
        print("2. Say clearly: 'activate aj' (pause between words)")
        print("3. Wait for confirmation, then ask question")
        print("4. Try web interface: http://localhost:3000")

if __name__ == "__main__":
    main()
