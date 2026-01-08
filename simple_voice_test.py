#!/usr/bin/env python3
"""
Simple voice test for JAI Assistant - tests actual speech output
"""

import sys
import os
sys.path.insert(0, '.')

def test_simple_speech():
    """Test simple speech output"""
    try:
        import tts as tts_module
        print("🔊 Testing simple speech...")
        
        # Test basic speak
        result = tts_module.speak("Voice mode is working", language='en')
        if result:
            print("✅ Speech executed successfully")
            return True
        else:
            print("❌ Speech failed")
            return False
            
    except Exception as e:
        print(f"❌ Speech test error: {e}")
        return False

def test_jai_voice_commands():
    """Test JAI voice mode commands"""
    try:
        import jai_assistant
        
        # Create a mock session
        session = jai_assistant.UserSession("test")
        
        # Test voice mode activation
        commands = [
            "activate voice mode",
            "hello"
        ]
        
        for cmd in commands:
            print(f"📝 Testing: '{cmd}'")
            try:
                response = jai_assistant.execute_command(cmd, session, suppress_tts=False)
                print(f"   Response: {response[:50]}...")
            except Exception as e:
                print(f"   Error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ JAI voice test error: {e}")
        return False

def check_audio_system():
    """Check if audio system is working"""
    try:
        import win32com.client
        
        # Try to create SAPI voice
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        voices = speaker.GetVoices()
        
        print(f"✅ SAPI available with {len(voices)} voices")
        for i in range(min(3, len(voices))):
            voice = voices.Item(i)
            voice_name = voice.GetDescription()
            print(f"   {i+1}. {voice_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ SAPI not available: {e}")
        return False

def main():
    """Main test function"""
    print("🎤 Simple Voice Mode Test")
    print("=" * 30)
    
    # Check audio system
    audio_ok = check_audio_system()
    print()
    
    # Test simple speech
    speech_ok = test_simple_speech()
    print()
    
    # Test JAI commands
    jai_ok = test_jai_voice_commands()
    print()
    
    print("📊 Results:")
    print(f"   Audio System: {'✅' if audio_ok else '❌'}")
    print(f"   Speech Output: {'✅' if speech_ok else '❌'}")
    print(f"   JAI Commands: {'✅' if jai_ok else '❌'}")
    
    if speech_ok:
        print("\n🎉 VOICE MODE IS WORKING!")
        print("You should have heard speech output.")
        print("\n📖 Usage in JAI Assistant:")
        print('   "activate voice mode"')
        print('   "activate text mode"')
        print('   "hello" (should speak response)')
    else:
        print("\n⚠️  Voice mode has issues but may still work partially")
        print("The speak function executes but audio may not work due to:")
        print("- Python 3.13 compatibility issues")
        print("- Missing audio drivers")
        print("- comtypes library issues")

if __name__ == "__main__":
    main()
