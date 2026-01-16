#!/usr/bin/env python3
"""
Test the voice client feature in the web interface
"""
import requests
import time

def test_voice_client_feature():
    print("🎤 Testing Voice Client Feature")
    print("=" * 50)
    
    try:
        # Test if the web interface is accessible
        response = requests.get("http://localhost:8080/", timeout=5)
        print(f"✅ Web interface accessible: {response.status_code}")
        
        # Check for voice client elements
        html_content = response.text
        
        checks = [
            ("btnMic button", "btnMic" in html_content),
            ("Voice client section", "voice-client-section" in html_content),
            ("Talk to JAI text", "Talk to JAI" in html_content),
            ("Voice client JavaScript", "toggleVoiceClient" in html_content),
            ("Microphone status", "micStatus" in html_content)
        ]
        
        print("\n📋 Feature Check:")
        all_good = True
        for feature, found in checks:
            status = "✅" if found else "❌"
            print(f"  {status} {feature}: {'Found' if found else 'Missing'}")
            if not found:
                all_good = False
        
        if all_good:
            print("\n🎉 Voice client feature is ready!")
            print("\n📝 How to use:")
            print("1. Open browser: http://localhost:8080/")
            print("2. Look for '🎙️ Voice Client Mode' section")
            print("3. Click the green 'Talk to JAI' button")
            print("4. Allow microphone permissions")
            print("5. Speak your command")
            print("6. Click the button again to stop recording")
            print("7. See JAI's response in the chat")
        else:
            print("\n⚠️ Some features are missing. Server may need restart.")
            print("Try restarting: python jai_assistant.py")
            
    except Exception as e:
        print(f"❌ Error testing voice client: {e}")

if __name__ == "__main__":
    test_voice_client_feature()
