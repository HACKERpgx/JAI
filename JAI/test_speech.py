# test_speech.py
import speech_recognition as sr
import logging
logging.basicConfig(level=logging.INFO, filename='test_speech.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say: weather in Canada")
    audio = r.listen(source, timeout=7)
    try:
        query = r.recognize_google(audio)
        print(f"Heard: {query}")
        logging.info("Heard: %s", query)
    except Exception as e:
        print(f"Error: {e}")
        logging.error("Error: %s", e)