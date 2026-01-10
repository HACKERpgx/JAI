# Calendar & Reminder Setup Guide

## ✅ Dependencies Already Installed

Good news! All required dependencies are already installed:
- ✓ APScheduler 3.10.4 (for scheduling reminders)
- ✓ SQLite (built-in with Python)

## 🚀 Quick Start

### 1. Test the Calendar System
```bash
python test_time_parsing.py
```

This will show you how JAI parses different time formats.

### 2. Start JAI Assistant
```bash
python jai_assistant.py
```

### 3. Try These Commands

**Ask for the time:**
```
"what time is it?"
"tell me the time"
"what's the time"
```

**Set reminders:**
```
"remind me to call mom at 10:40 PM"
"remind me to take medicine at 3:30 PM"
"remind me to check email in 15 minutes"
"remind me to attend meeting at 2:00 PM"
```

**Check your reminders:**
```
"list my reminders"
"show reminders"
"what are my reminders"
```

## 🎯 What Was Fixed

### 1. **Time Command Added**
JAI now knows the current time and can tell you:
- Command: `"what time is it?"`
- Response: `"The current time is 10:45 PM, Monday, October 06, 2025, sir."`

### 2. **Enhanced Time Parsing**
JAI can now understand:
- ✅ `"at 10:40 PM"` - Specific time today (or tomorrow if passed)
- ✅ `"at 3:30 pm"` - Specific time with minutes
- ✅ `"at 3 PM"` - Specific hour
- ✅ `"in 5 minutes"` - Relative time
- ✅ `"in 2 hours"` - Relative time
- ✅ `"tomorrow at 9:00 AM"` - Tomorrow with specific time

### 3. **Smart Scheduling**
- If you say "remind me at 10:40 PM" and it's already past 10:40 PM today, JAI schedules it for 10:40 PM tomorrow
- Reminders persist across restarts (stored in database)
- Automatic alerts with voice (if TTS enabled)

## 📋 Testing Your Setup

### Test 1: Check Current Time
```bash
# Start JAI
python jai_assistant.py

# In another terminal, send command:
curl -X POST http://localhost:8001/command -u user1:pass1 -H "Content-Type: application/json" -d "{\"command\": \"what time is it\"}"
```

Expected response: Current time with date

### Test 2: Set a Quick Reminder
```bash
curl -X POST http://localhost:8001/command -u user1:pass1 -H "Content-Type: application/json" -d "{\"command\": \"remind me to test in 30 seconds\"}"
```

Wait 30 seconds - you should see a reminder alert in JAI's console!

### Test 3: Set Reminder for Specific Time
```bash
curl -X POST http://localhost:8001/command -u user1:pass1 -H "Content-Type: application/json" -d "{\"command\": \"remind me to call mom at 11:00 PM\"}"
```

### Test 4: List Reminders
```bash
curl -X POST http://localhost:8001/command -u user1:pass1 -H "Content-Type: application/json" -d "{\"command\": \"list my reminders\"}"
```

## 🔧 Troubleshooting

### Issue: "Reminder didn't trigger"

**Check 1: Is JAI running?**
Reminders only trigger while JAI is running. Keep `python jai_assistant.py` active.

**Check 2: Was the time in the future?**
```bash
python test_time_parsing.py
```
This shows exactly when JAI scheduled your reminder.

**Check 3: Check the logs**
```bash
type jai_assistant.log | Select-String "REMINDER"
```

### Issue: "JAI doesn't know the time"

**Solution:** The fix is already applied! Try:
```
"what time is it?"
"tell me the time"
```

### Issue: "Time parsing not working"

**Test it:**
```bash
python test_time_parsing.py
```

This will show you exactly how JAI interprets different time formats.

## 📱 Using with Voice Client

If you're using the voice client (`voice_client.py`):

1. Start JAI: `python jai_assistant.py`
2. Start voice client: `python voice_client.py`
3. Say: "JAI, what time is it?"
4. Say: "JAI, remind me to call mom at 10:40 PM"
5. Say: "JAI, list my reminders"

## 🎤 Enable Voice Alerts

To hear reminders spoken aloud:

1. Edit `.env` file:
```
SPEAK_RESPONSES=true
```

2. Restart JAI:
```bash
python jai_assistant.py
```

Now when reminders trigger, JAI will speak them!

## 📊 Example Session

```
You: "what time is it?"
JAI: "The current time is 10:42 PM, Monday, October 06, 2025, sir."

You: "remind me to call mom at 10:45 PM"
JAI: "Reminder set: 'call mom' at 2025-10-06 22:45"

You: "list my reminders"
JAI: "Pending reminders:
     - call mom at 2025-10-06 22:45:00"

[3 minutes later at 10:45 PM]
JAI: 🔔 Reminder: call mom

You: "list my reminders"
JAI: "No pending reminders"
```

## 🎯 Summary

**What's Working:**
- ✅ Time command ("what time is it?")
- ✅ Reminders with specific times ("at 10:40 PM")
- ✅ Reminders with relative times ("in 5 minutes")
- ✅ List reminders
- ✅ Automatic alerts
- ✅ Voice alerts (if enabled)
- ✅ Persistent storage

**No Additional Installation Needed:**
All dependencies are already installed!

**Next Steps:**
1. Test: `python test_time_parsing.py`
2. Start JAI: `python jai_assistant.py`
3. Try: "what time is it?"
4. Try: "remind me to test in 30 seconds"
5. Wait and watch the reminder trigger!
