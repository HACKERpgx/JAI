#!/usr/bin/env python3
"""
Test voice mode functionality in JAI Assistant
"""

import sys
import os
sys.path.insert(0, '.')

def test_tts_import():
    """Test if TTS module can be imported"""
    try:
        import tts as tts_module
        print("✅ TTS module imported successfully")
        
        # Check if pyttsx3 is available
        if hasattr(tts_module, 'pyttsx3') and tts_module.pyttsx3:
            print("✅ pyttsx3 engine available")
        else:
            print("❌ pyttsx3 engine not available")
            return False
            
        return tts_module
    except ImportError as e:
        print(f"❌ Failed to import TTS module: {e}")
        return None

def test_tts_engine(tts_module):
    """Test TTS engine initialization"""
    try:
        # Test if we can get engine
        if hasattr(tts_module, 'get_engine'):
            engine = tts_module.get_engine()
            if engine:
                print("✅ TTS engine initialized successfully")
                return True
            else:
                print("❌ TTS engine failed to initialize")
                return False
        else:
            print("⚠️  get_engine method not found")
            return False
    except Exception as e:
        print(f"❌ TTS engine test failed: {e}")
        return False

def test_voice_list(tts_module):
    """Test available voices"""
    try:
        if hasattr(tts_module, 'get_voices'):
            voices = tts_module.get_voices()
            if voices:
                print(f"✅ Found {len(voices)} available voices")
                for i, voice in enumerate(voices[:3]):  # Show first 3
                    voice_name = getattr(voice, 'name', 'Unknown')
                    voice_lang = getattr(voice, 'languages', ['Unknown'])
                    print(f"   {i+1}. {voice_name} ({voice_lang})")
                return True
            else:
                print("❌ No voices found")
                return False
        else:
            print("⚠️  get_voices method not found")
            return False
    except Exception as e:
        print(f"❌ Voice list test failed: {e}")
        return False

def test_speak_function(tts_module):
    """Test speak function"""
    try:
        print("🔊 Testing speech synthesis...")
        
        # Test a simple speak
        if hasattr(tts_module, 'speak'):
            # Test with a short message
            tts_module.speak("Voice mode test", language='en')
            print("✅ Speak function executed successfully")
            return True
        else:
            print("❌ Speak function not found")
            return False
            
    except Exception as e:
        print(f"❌ Speak test failed: {e}")
        return False

def test_jai_voice_integration():
    """Test JAI Assistant voice integration"""
    try:
        import jai_assistant
        
        # Check voice-related constants
        if hasattr(jai_assistant, 'SPEAK_RESPONSES'):
            speak_enabled = jai_assistant.SPEAK_RESPONSES
            print(f"✅ SPEAK_RESPONSES: {speak_enabled}")
        else:
            print("❌ SPEAK_RESPONSES not found")
            
        if hasattr(jai_assistant, 'tts_module'):
            tts_available = jai_assistant.tts_module is not None
            print(f"✅ TTS module available: {tts_available}")
        else:
            print("❌ tts_module not found")
            
        # Test voice mode intent
        test_commands = [
            "activate voice mode",
            "activate text mode", 
            "activate aj"
        ]
        
        for cmd in test_commands:
            intent, args = jai_assistant.classify_intent(cmd)
            print(f"📝 '{cmd}' -> Intent: {intent}, Args: {args}")
            
        return True
        
    except Exception as e:
        print(f"❌ JAI voice integration test failed: {e}")
        return False

def test_environment_variables():
    """Check environment variables for voice configuration"""
    env_vars = [
        'SPEAK_RESPONSES',
        'TTS_VOICE', 
        'TTS_PREFERRED_VOICE',
        'TTS_FORCE_LANGUAGE',
        'TTS_ENGINE',
        'ENABLE_VOICE_LISTENER',
        'VOICE_HOTWORD'
    ]
    
    print("🔧 Environment Variables:")
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        status = "✅" if value != 'Not set' else "⚠️"
        print(f"   {status} {var}: {value}")

def main():
    """Main test function"""
    print("🎤 JAI Assistant Voice Mode Test Suite")
    print("=" * 50)
    
    # Test environment
    test_environment_variables()
    print()
    
    # Test TTS import
    tts_module = test_tts_import()
    if not tts_module:
        print("\n❌ Voice mode cannot work without TTS module")
        return
    
    print()
    
    # Test TTS engine
    engine_ok = test_tts_engine(tts_module)
    print()
    
    # Test voices
    voices_ok = test_voice_list(tts_module)
    print()
    
    # Test speak function
    speak_ok = test_speak_function(tts_module)
    print()
    
    # Test JAI integration
    jai_ok = test_jai_voice_integration()
    print()
    
    # Results
    print("📊 Voice Mode Test Results:")
    print(f"   TTS Import: {'✅' if tts_module else '❌'}")
    print(f"   TTS Engine: {'✅' if engine_ok else '❌'}")
    print(f"   Voices: {'✅' if voices_ok else '❌'}")
    print(f"   Speak Function: {'✅' if speak_ok else '❌'}")
    print(f"   JAI Integration: {'✅' if jai_ok else '❌'}")
    
    overall = tts_module and engine_ok and voices_ok and speak_ok and jai_ok
    print(f"\n🎯 Overall Status: {'✅ VOICE MODE WORKING' if overall else '❌ VOICE MODE ISSUES'}")
    
    if overall:
        print("\n📖 Voice Mode Usage:")
        print('   "activate voice mode" - Enable voice responses')
        print('   "activate text mode" - Enable text + voice responses') 
        print('   "activate aj" - Enable AJ with voice')
        print("\n🔊 Voice should now work in JAI Assistant!")
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Install pyttsx3: pip install pyttsx3")
        print("2. Check audio drivers")
        print("3. Verify SPEAK_RESPONSES=true environment variable")

if __name__ == "__main__":
    main()
