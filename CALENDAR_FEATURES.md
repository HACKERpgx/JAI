# JAI Calendar & Reminder System

## Overview
JAI Assistant now includes a comprehensive calendar and reminder system with automatic alerts and TTS support.

## Features

### ✅ Reminders
- Set reminders with natural language
- Automatic alerts at scheduled times
- Text-to-speech notifications (if enabled)
- Persistent storage (survives restarts)

### ✅ Calendar Events
- Schedule events with start/end times
- Add descriptions to events
- View upcoming events
- Query your calendar

### ✅ Natural Language Support
- "Remind me to call mom in 5 minutes"
- "Remind me to take medicine in 2 hours"
- "Set a reminder for tomorrow at 3pm"
- "What's on my calendar?"
- "List my reminders"

## Commands

### Setting Reminders
```
remind me to [task] in [time]
set a reminder for [task]
reminder for [task] in [time]
```

**Examples:**
- "remind me to call John in 30 minutes"
- "remind me to take a break in 1 hour"
- "set a reminder for meeting tomorrow at 2pm"

### Viewing Reminders
```
list reminders
show reminders
what are my reminders
my reminders
```

### Viewing Calendar Events
```
list events
show events
what's on my calendar
my calendar
upcoming events
```

## Time Expressions Supported

### Relative Time
- `in X seconds` - e.g., "in 30 seconds"
- `in X minutes` - e.g., "in 15 minutes"
- `in X hours` - e.g., "in 2 hours"
- `in X days` - e.g., "in 3 days"

### Absolute Time
- `tomorrow at [time]` - e.g., "tomorrow at 3pm"
- More formats coming soon!

## Technical Details

### Database
- Uses SQLite for persistent storage
- Database file: `jai_calendar.db`
- Stores events and reminders separately

### Scheduler
- Uses APScheduler for background task scheduling
- Reminders trigger automatically even if assistant is idle
- Survives application restarts (pending reminders are reloaded)

### Alert System
- Visual alerts in console (🔔 emoji)
- Text-to-speech notifications (if `SPEAK_RESPONSES=true` in .env)
- Logged to `jai_assistant.log`

## Installation

The calendar system requires APScheduler:
```bash
pip install apscheduler==3.10.4
```

This is already included in `requirements.txt`.

## Testing

Run the test script to verify functionality:
```bash
python test_calendar.py
```

This will:
1. Create a test reminder (triggers in 10 seconds)
2. Add a sample event
3. List reminders and events
4. Test command parsing
5. Test time parsing
6. Wait for reminder to trigger

## API Usage

### Via FastAPI Endpoint
```bash
curl -X POST http://localhost:8001/command \
  -u user1:pass1 \
  -H "Content-Type: application/json" \
  -d '{"command": "remind me to check email in 5 minutes"}'
```

### Programmatic Usage
```python
from jai_calendar import CalendarManager
from datetime import datetime, timedelta

# Initialize
cal = CalendarManager()

# Add reminder
remind_time = datetime.now() + timedelta(minutes=30)
cal.add_reminder("Call client", remind_time, "Discuss project timeline")

# Add event
event_time = datetime.now() + timedelta(hours=2)
cal.add_event("Team Meeting", event_time, description="Q4 Planning")

# List reminders
reminders = cal.get_pending_reminders()
for r in reminders:
    print(f"{r['title']} at {r['remind_at']}")
```

## Configuration

### Enable TTS for Reminders
In your `.env` file:
```
SPEAK_RESPONSES=true
TTS_VOICE=  # Optional: specify voice
```

### Custom Reminder Handler
```python
def my_handler(reminder):
    # Custom logic here
    print(f"Alert: {reminder['title']}")

cal = CalendarManager(on_reminder=my_handler)
```

## Troubleshooting

### Reminders Not Triggering
1. Check if APScheduler is installed: `pip install apscheduler`
2. Verify the reminder time is in the future
3. Check logs: `jai_assistant.log`

### Database Issues
- Delete `jai_calendar.db` to reset
- Check file permissions
- Ensure SQLite is available (built-in with Python)

### TTS Not Working
- Verify `SPEAK_RESPONSES=true` in `.env`
- Check if `tts.py` module is working
- Test with: `python test_tts.py`

## Future Enhancements
- [ ] Recurring reminders (daily, weekly, monthly)
- [ ] Snooze functionality
- [ ] Calendar sync with Google Calendar/Outlook
- [ ] More natural language parsing
- [ ] Reminder priorities
- [ ] Event notifications (alerts before events)
- [ ] Time zone support

## Examples

### Quick Reminder
```
User: "remind me to take a break in 15 minutes"
JAI: "Reminder set: 'take a break' at 2025-10-06 22:39"
```

### Check Schedule
```
User: "what's on my calendar?"
JAI: "Upcoming events:
- Team Meeting at 2025-10-07 10:00
- Lunch with Sarah at 2025-10-07 12:30"
```

### List Reminders
```
User: "show my reminders"
JAI: "Pending reminders:
- Call John at 2025-10-06 15:30
- Submit report at 2025-10-07 09:00"
```

## Notes
- All times are stored in ISO format
- Reminders are marked as completed after triggering
- Events remain in the database indefinitely
- The calendar is shared across all users in multi-user mode
