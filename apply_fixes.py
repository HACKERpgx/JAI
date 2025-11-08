#!/usr/bin/env python3
"""Script to apply fixes to jai_assistant.py"""

with open('jai_assistant.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add personality import
content = content.replace(
    'from memory import JAIMemory',
    'from memory import JAIMemory\nfrom personality import build_system_prompt'
)

# 2. Add logging filter after basicConfig
logging_filter = '''

# Ensure 'user' field exists on all log records to prevent errors
class _UserFieldFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'user'):
            record.user = 'system'
        return True

logging.getLogger().addFilter(_UserFieldFilter())'''

content = content.replace(
    '                    force=True)',
    '                    force=True)' + logging_filter
)

# 3. Fix NEWS_API_KEY and add speech config
content = content.replace(
    'NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "your_news_api_key_here")  # Add to .env',
    '''NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")  # Add to .env

# Speech configuration
SPEAK_RESPONSES = os.environ.get("SPEAK_RESPONSES", "false").lower() in {"1", "true", "yes", "on"}
TTS_VOICE = os.environ.get("TTS_VOICE", None)'''
)

# 4. Fix translator and add tts import
content = content.replace(
    "translator = GoogleTranslator(source='auto', target='en')",
    '''# Translator will be created per target language for correct usage
translator = None

try:
    import tts
except Exception:
    tts = None'''
)

# 5. Add NEWS_API_KEY check in get_news
content = content.replace(
    'def get_news(category: Optional[str] = None) -> str:\n    url = f"https://newsapi',
    '''def get_news(category: Optional[str] = None) -> str:
    if not NEWS_API_KEY:
        return "News API key is not configured. Please set NEWS_API_KEY in .env."
    url = f"https://newsapi'''
)

# 6. Replace personality prompt building in jai_reply
old_prompt_block = '''    current_hour = datetime.now().hour
    time_prompt = ""
    if current_hour >= 22 or current_hour < 6:
        time_prompt = "It's late—maybe time for a story or a lullaby?"
    elif current_hour < 12:
        time_prompt = f"Good morning, {user_name}! Ready to conquer the day?"
    elif current_hour < 18:
        time_prompt = f"Afternoon, {user_name}! Need a quick boost or a joke?"
    else:
        time_prompt = f"Evening, {user_name}! Wrapping up or just getting started?"
    
    quip = random.choice(HUMOROUS_QUIPS)
    full_prompt = (
        f"You are JAI, a witty, helpful, and intelligent personal assistant. Address the user as {user_name}. "
        f"Use a playful, humorous tone with insightful responses. Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
        f"Keep responses concise, relevant, and engaging. Incorporate context for continuity. {time_prompt}\\n"
        f"User query: {prompt}\\n{context_str}\\n{quip}"
    )'''

new_prompt_block = '''    
    system_prompt = build_system_prompt(user_name)
    full_prompt = (
        f"{system_prompt}\\n"
        f"User query: {prompt}\\n{context_str}"
    )'''

content = content.replace(old_prompt_block, new_prompt_block)

# 7. Fix translator usage in jai_reply
content = content.replace(
    '''        lang = session.preferred_lang
        if lang != "en" and translator:
            try:
                translated_answer = translator.translate(text=answer, dest=lang)
                return translated_answer
            except Exception:
                return f"Sorry, translation to {lang} failed. English response: {answer}"''',
    '''        lang = session.preferred_lang
        if lang != "en":
            try:
                translated_answer = GoogleTranslator(source='auto', target=lang).translate(answer)
                return translated_answer
            except Exception:
                return f"Sorry, translation to {lang} failed. English response: {answer}"'''
)

# 8. Add TTS speaking after response
old_return = '''    # Default to AI reply
    response = jai_reply(command, session)
    try:
        session.memory.add_short_term({"user": command, "response": response})
    except Exception as e:
        logging.error("Memory storage error: %s", e, extra=logging_extra)
    return response'''

new_return = '''    # Default to AI reply
    response = jai_reply(command, session)
    try:
        session.memory.add_short_term({"user": command, "response": response})
    except Exception as e:
        logging.error("Memory storage error: %s", e, extra=logging_extra)
    
    # Optionally speak the response
    if SPEAK_RESPONSES and tts:
        try:
            tts.speak(response, voice=TTS_VOICE)
        except Exception as e:
            logging.error("TTS speak error: %s", e, extra=logging_extra)
    
    return response'''

content = content.replace(old_return, new_return)

# Write the updated content
with open('jai_assistant.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully applied all fixes to jai_assistant.py")
