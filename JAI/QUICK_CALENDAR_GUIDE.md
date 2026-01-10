# Quick Calendar & Reminder Guide

## 🚀 Getting Started

### 1. Ensure Dependencies are Installed
```bash
pip install -r requirements.txt
```

### 2. Test the Calendar System
```bash
python test_calendar.py
```

### 3. Start JAI Assistant
```bash
python jai_assistant.py
```

## 📝 Common Commands

### Set Reminders
| Command | What It Does |
|---------|-------------|
| `remind me to call mom in 5 minutes` | Sets a reminder 5 minutes from now |
| `remind me to take medicine in 2 hours` | Sets a reminder 2 hours from now |
| `set a reminder for meeting tomorrow at 3pm` | Sets a reminder for tomorrow at 3 PM |
| `remind me to submit report in 30 seconds` | Quick test reminder |

### View Your Schedule
| Command | What It Does |
|---------|-------------|
| `list reminders` | Shows all pending reminders |
| `show my reminders` | Same as above |
| `what are my reminders` | Same as above |
| `list events` | Shows upcoming calendar events |
| `show events` | Same as above |
| `what's on my calendar` | Shows your calendar |

## ⏰ Time Formats

### Relative Time (from now)
- `in 30 seconds`
- `in 5 minutes`
- `in 2 hours`
- `in 3 days`

### Absolute Time
- `tomorrow at 3pm`
- `tomorrow at 9am`

## 🔔 How Reminders Work

1. **You set a reminder**: "remind me to call John in 10 minutes"
2. **JAI confirms**: "Reminder set: 'call John' at 2025-10-06 22:35"
3. **JAI waits**: The reminder is stored in the database
4. **Time arrives**: JAI triggers the alert
5. **You get notified**: 
   - Console: 🔔 Reminder: call John
   - TTS (if enabled): JAI speaks the reminder
   - Log: Entry added to jai_assistant.log

## 🎯 Example Session

```
You: "remind me to take a break in 15 minutes"
JAI: "Reminder set: 'take a break' at 2025-10-06 22:40"

You: "list my reminders"
JAI: "Pending reminders:
     - take a break at 2025-10-06 22:40:00"

[15 minutes later]
JAI: 🔔 Reminder: take a break

You: "list my reminders"
JAI: "No pending reminders"
```

## 🛠️ Troubleshooting

### "Calendar system is not available"
**Solution**: Install APScheduler
```bash
pip install apscheduler
```

### Reminders not triggering
**Check**:
1. Is JAI running? (reminders only trigger while JAI is active)
2. Is the time in the future?
3. Check logs: `jai_assistant.log`

### Want voice alerts?
**Enable TTS** in `.env`:
```
SPEAK_RESPONSES=true
```

## 💡 Pro Tips

1. **Test with short times**: Use "in 10 seconds" to test quickly
2. **Check your reminders**: Use "list reminders" to see what's scheduled
3. **Multiple reminders**: You can set as many as you want
4. **Persistent**: Reminders survive JAI restarts (they're in the database)
5. **Shared calendar**: All users share the same calendar in multi-user mode

## 📊 What's Stored

### Database: `jai_calendar.db`
- All reminders (with completion status)
- All calendar events
- Timestamps in ISO format

### Logs: `jai_assistant.log`
- Reminder creation
- Reminder triggers
- Any errors

## 🎓 Advanced Usage

### Via API (FastAPI)
```bash
curl -X POST http://localhost:8001/command \
  -u user1:pass1 \
  -H "Content-Type: application/json" \
  -d '{"command": "remind me to check email in 5 minutes"}'
```

### Via Voice Client
Just speak naturally:
- "remind me to call Sarah in 30 minutes"
- "what's on my calendar"

## ✅ Feature Checklist

- [x] Set reminders with natural language
- [x] Automatic alerts at scheduled times
- [x] TTS notifications (optional)
- [x] Persistent storage
- [x] List pending reminders
- [x] View calendar events
- [x] Relative time parsing (in X minutes/hours)
- [x] Absolute time parsing (tomorrow at Xpm)
- [ ] Recurring reminders (coming soon)
- [ ] Snooze functionality (coming soon)
- [ ] Calendar sync (coming soon)

## 📚 More Information

See `CALENDAR_FEATURES.md` for detailed documentation.
