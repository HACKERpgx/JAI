"""
Test script to diagnose TTS functionality
"""
import pyttsx3
import logging
import sys
import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tts_diagnostic.log'),
        logging.StreamHandler()
    ]
)

def get_audio_devices():
    """Get list of all audio output devices"""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Get device name
        device_name = devices.GetDisplayName()
        return {
            'name': device_name,
            'volume': volume.GetMasterVolumeLevelScalar() * 100,
            'mute': volume.GetMute()
        }
    except Exception as e:
        logging.error(f"Error getting audio devices: {e}")
        return None

def test_tts():
    try:
        # Initialize the TTS engine
        logging.info("Initializing TTS engine...")
        engine = pyttsx3.init()
        
        # Get current audio output device info
        audio_device = get_audio_devices()
        if audio_device:
            logging.info("\n=== Audio Output Device ===")
            logging.info(f"Device: {audio_device['name']}")
            logging.info(f"Volume: {audio_device['volume']:.0f}%")
            logging.info(f"Muted: {'Yes' if audio_device['mute'] else 'No'}")
            
            if audio_device['mute']:
                logging.warning("Audio is currently muted!")
            if audio_device['volume'] < 50:
                logging.warning("Volume is set below 50% - you might have trouble hearing the output.")
        
        # Check audio output settings
        current_volume = engine.getProperty('volume')
        current_rate = engine.getProperty('rate')
        logging.info(f"\n=== Audio Settings ===")
        logging.info(f"Volume: {current_volume} (0.0 to 1.0)")
        logging.info(f"Rate: {current_rate} (words per minute)")
        
        # Get and list all available voices
        voices = engine.getProperty('voices')
        if not voices:
            logging.error("No TTS voices found on this system!")
            logging.info("\n=== Installation Instructions ===")
            logging.info("1. Open Windows Settings")
            logging.info("2. Go to Time & Language > Language & region")
            logging.info("3. Click 'Add a language' and install a language pack")
            logging.info("4. Go to Speech settings and install speech packages")
            return False
            
        logging.info("\n=== Available Voices ===")
        for i, voice in enumerate(voices):
            logging.info(f"{i+1}. ID: {voice.id}")
            logging.info(f"   Name: {voice.name}")
            logging.info(f"   Languages: {getattr(voice, 'languages', ['Not available'])}")
            logging.info(f"   Gender: {getattr(voice, 'gender', 'Not specified')}")
            logging.info("-" * 40)
        
        # Test speaking with default settings
        logging.info("\n=== Testing Default Voice ===")
        test_text = "This is a test of the text-to-speech system. Hello, world!"
        logging.info(f"Testing with text: {test_text}")
        
        # Set volume to maximum in the TTS engine
        # Note: This is separate from system volume
        engine.setProperty('volume', 1.0)
        
        # Get system volume info again to confirm
        audio_device = get_audio_devices()
        if audio_device and audio_device['mute']:
            logging.warning("Audio is muted in Windows Sound Settings. Please unmute to hear the output.")
            logging.info("To unmute:")
            logging.info("1. Right-click the speaker icon in the taskbar")
            logging.info("2. Click 'Open Volume mixer'")
            logging.info("3. Make sure the volume is up and not muted")
        
        # Test each voice with a count
        for i, voice in enumerate(voices, 1):
            try:
                engine.setProperty('voice', voice.id)
                logging.info(f"\nTesting voice {i}: {voice.name}")
                engine.say(f"This is voice number {i}, {voice.name}")
                engine.say(test_text)
                engine.runAndWait()
                logging.info("Did you hear the voice? (y/n)")
                response = input().strip().lower()
                if response == 'y':
                    logging.info(f"Great! Voice {i} is working.")
                else:
                    logging.warning(f"Voice {i} may not be audible. Checking audio settings...")
                    # Additional audio check
                    import winsound
                    winsound.Beep(1000, 500)  # Play a beep sound
                    logging.info("Did you hear the beep sound? (y/n)")
                    beep_response = input().strip().lower()
                    if beep_response != 'y':
                        logging.error("Audio output issue detected!")
                        logging.info("\n=== Audio Troubleshooting ===")
                        logging.info("1. Check if your speakers/headphones are properly connected")
                        logging.info("2. Make sure volume is turned up")
                        logging.info("3. Check Windows Sound Settings to ensure the correct output device is selected")
                        logging.info("4. Try playing a test sound in Windows Sound Settings")
                        return False
            except Exception as e:
                logging.error(f"Error testing voice {i}: {e}")
                continue
        
        # Test with different voices
        if len(voices) > 0:
            logging.info("\n=== Testing All Available Voices ===")
            for i, voice in enumerate(voices):
                try:
                    engine.setProperty('voice', voice.id)
                    logging.info(f"Testing voice {i+1}: {voice.name}")
                    engine.say(f"This is voice {i+1}: {voice.name}")
                    engine.runAndWait()
                except Exception as e:
                    logging.error(f"Error with voice {i+1}: {e}")
        
        logging.info("\n=== TTS Test Complete ===")
        return True
        
    except Exception as e:
        logging.error(f"TTS test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logging.info("Starting TTS Diagnostic Test...")
    if test_tts():
        logging.info("TTS test completed successfully! Check the output above for available voices.")
    else:
        logging.error("TTS test encountered errors. Please check the logs for details.")
