# How Automatic Reminders Work 🔔

## 📖 Complete Flow

### Step 1: You Set a Reminder
```
You: "JAI, remind me to open WhatsApp in 10 minutes"
```

### Step 2: JAI Confirms
```
JAI: "Reminder set: 'open WhatsApp' at 2025-10-06 23:10, sir."
```
- JAI stores the reminder in the database
- JAI schedules the alert for exactly 10 minutes from now

### Step 3: You Continue Your Work
- JAI is running in the background
- The reminder is waiting silently
- You can do other things

### Step 4: Time Arrives (After 10 Minutes)
**JAI AUTOMATICALLY:**

**On Screen:**
```
============================================================
🔔 REMINDER ALERT 🔔
============================================================
Time: 11:10 PM
Task: open WhatsApp
============================================================
```

**JAI SPEAKS (with voice):**
```
"Sir, it's time to open WhatsApp. Your reminder has triggered."
```

### Step 5: Reminder Complete
- The reminder is marked as completed
- It won't trigger again
- You can set new reminders anytime

---

## 🎯 Example Scenarios

### Scenario 1: Quick Reminder
```
10:50 PM - You: "remind me to call mom in 10 minutes"
10:50 PM - JAI: "Reminder set: 'call mom' at 2025-10-06 23:00, sir."
[10 minutes pass...]
11:00 PM - JAI: 🔔 "Sir, it's time to call mom. Your reminder has triggered."
```

### Scenario 2: Specific Time
```
10:50 PM - You: "remind me to take medicine at 11:30 PM"
10:50 PM - JAI: "Reminder set: 'take medicine' at 2025-10-06 23:30, sir."
[40 minutes pass...]
11:30 PM - JAI: 🔔 "Sir, it's time to take medicine. Your reminder has triggered."
```

### Scenario 3: Tomorrow
```
10:50 PM - You: "remind me to attend meeting tomorrow at 9 AM"
10:50 PM - JAI: "Reminder set: 'attend meeting' at 2025-10-07 09:00, sir."
[next day at 9 AM]
09:00 AM - JAI: 🔔 "Sir, it's time to attend meeting. Your reminder has triggered."
```

---

## ⚙️ Configuration

### Enable Voice Alerts
Your `.env` file is now set to:
```
SPEAK_RESPONSES=true
TTS_VOICE=David
```

This means:
- ✅ JAI will SPEAK all responses
- ✅ JAI will SPEAK reminder alerts
- ✅ You will HEAR JAI's voice when reminders trigger

### How It Works Technically

1. **APScheduler** runs in the background
2. When you set a reminder, it's added to the scheduler
3. At the exact time, the scheduler triggers the `reminder_alert_handler`
4. The handler:
   - Prints the alert to console
   - Logs it to `jai_assistant.log`
   - Calls `tts.speak()` to speak the message
   - Marks the reminder as completed

---

## 🧪 Test It Now!

### Quick Test (30 seconds)
```bash
# Start JAI
python jai_assistant.py

# In voice client or API, say:
"remind me to test in 30 seconds"

# Wait 30 seconds...
# JAI will automatically alert you!
```

### Test via API
```bash
# Terminal 1: Start JAI
python jai_assistant.py

# Terminal 2: Set reminder
curl -X POST http://localhost:8001/command -u admin:adminpass -H "Content-Type: application/json" -d "{\"command\": \"remind me to check this in 30 seconds\"}"

# Wait 30 seconds and watch Terminal 1 for the alert!
```

---

## 📱 Using with Voice Client

### Full Voice Experience
```bash
# Terminal 1: Start JAI
python jai_assistant.py

# Terminal 2: Start voice client
python voice_client.py

# Speak to JAI:
You: "JAI, remind me to open WhatsApp in 1 minute"
JAI: "Reminder set: 'open WhatsApp' at 11:01 PM, sir."

[1 minute later]
JAI: 🔔 "Sir, it's time to open WhatsApp. Your reminder has triggered."
```

You will HEAR JAI speak both:
1. The confirmation when you set the reminder
2. The alert when the time arrives

---

## ✅ What's Working Now

- ✅ **Automatic alerts** - JAI speaks when time arrives
- ✅ **Voice enabled** - SPEAK_RESPONSES=true
- ✅ **Natural language** - "Sir, it's time to..."
- ✅ **Visual alerts** - Big 🔔 banner in console
- ✅ **Persistent** - Reminders survive restarts
- ✅ **Accurate timing** - Triggers at exact time
- ✅ **Multiple reminders** - Set as many as you want

---

## 🎤 Voice Output Examples

When a reminder triggers, JAI will say:

```
"Sir, it's time to open WhatsApp. Your reminder has triggered."
"Sir, it's time to call mom. Your reminder has triggered."
"Sir, it's time to take medicine. Your reminder has triggered."
"Sir, it's time to attend meeting. Your reminder has triggered."
```

---

## 💡 Important Notes

1. **JAI must be running** for reminders to trigger
   - Keep `python jai_assistant.py` active
   - If you stop JAI, reminders won't trigger
   - When you restart JAI, pending reminders reload automatically

2. **Voice requires TTS**
   - `tts.py` must be working
   - Test with: `python test_tts.py`
   - If TTS fails, you'll still see the visual alert

3. **Reminders are persistent**
   - Stored in `jai_calendar.db`
   - Survive JAI restarts
   - Automatically reload when JAI starts

---

## 🔧 Troubleshooting

### "I don't hear JAI speak"
1. Check `.env`: `SPEAK_RESPONSES=true` ✓
2. Test TTS: `python test_tts.py`
3. Check volume on your computer
4. Check `jai_assistant.log` for TTS errors

### "Reminder didn't trigger"
1. Is JAI running? Check the terminal
2. Check logs: `type jai_assistant.log | Select-String "REMINDER"`
3. List reminders: "list my reminders"
4. Check the time was in the future

### "JAI set the wrong time"
1. Test time parsing: `python test_time_parsing.py`
2. Be specific: "at 11:30 PM" not "at 11:30"
3. Check current time: "what time is it?"

---

## 🎉 Summary

**Everything is working!**

1. ✅ Set reminder: "remind me to [task] in/at [time]"
2. ✅ JAI confirms and stores it
3. ✅ JAI waits in the background
4. ✅ **At the exact time, JAI automatically alerts you**
5. ✅ **JAI SPEAKS the reminder aloud**
6. ✅ You hear: "Sir, it's time to [task]"

**Just start JAI and try it!** 🚀
