# test_tts.py
import pyttsx3
import logging
import threading
import queue
logging.basicConfig(level=logging.INFO, filename='test_tts.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def speak_with_timeout(text, timeout=10):
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        male_voice = None
        for v in voices:
            if "male" in v.name.lower() or "david" in v.name.lower() or "mark" in v.name.lower():
                male_voice = v.id
                break
        if male_voice:
            engine.setProperty('voice', male_voice)
            logging.info("Male voice selected: %s", male_voice)
        else:
            logging.warning("No male voice found")
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        result_queue = queue.Queue()
        def speak_thread():
            try:
                engine.say(text)
                engine.runAndWait()
                result_queue.put(True)
            except Exception as e:
                result_queue.put(str(e))
        thread = threading.Thread(target=speak_thread)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            logging.error("TTS timed out after %s seconds", timeout)
            return False
        return result_queue.get() is True
    except Exception as e:
        logging.error("TTS setup failed: %s", e)
        return False

success = speak_with_timeout("Weather in Toronto: mist, 17.74 degrees Celsius")
logging.info("TTS success: %s", success)
print("TTS test complete. Check test_tts.log for details.")