# jai_calendar.py
"""
Calendar and reminder system for JAI.
Uses SQLite for storage and APScheduler for alerts.
"""
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import re

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.date import DateTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logging.warning("APScheduler not available. Install: pip install apscheduler")


class CalendarManager:
    """Manages events and reminders."""
    
    def __init__(self, db_path: str = "jai_calendar.db", on_reminder: callable = None):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.on_reminder = on_reminder or self._default_reminder_handler
        self._create_tables()
        
        # Initialize scheduler
        if SCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
            self._load_pending_reminders()
        else:
            self.scheduler = None
            logging.warning("Scheduler not available - reminders will not trigger")
    
    def _create_tables(self):
        """Create database tables."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT,
                remind_at TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def _default_reminder_handler(self, reminder: Dict):
        """Default handler for reminder alerts."""
        logging.info("REMINDER: %s - %s", reminder['title'], reminder.get('message', ''))
        print(f"\n🔔 REMINDER: {reminder['title']}")
        if reminder.get('message'):
            print(f"   {reminder['message']}")
    
    def _load_pending_reminders(self):
        """Load and schedule all pending reminders."""
        if not self.scheduler:
            return
        
        now = datetime.now()
        self.cursor.execute(
            "SELECT id, title, message, remind_at FROM reminders WHERE completed = 0 AND remind_at > ?",
            (now.isoformat(),)
        )
        
        for row in self.cursor.fetchall():
            reminder_id, title, message, remind_at = row
            remind_time = datetime.fromisoformat(remind_at)
            
            self.scheduler.add_job(
                self._trigger_reminder,
                trigger=DateTrigger(run_date=remind_time),
                args=[reminder_id],
                id=f"reminder_{reminder_id}",
                replace_existing=True
            )
            logging.info("Scheduled reminder: %s at %s", title, remind_at)
    
    def _trigger_reminder(self, reminder_id: int):
        """Trigger a reminder and mark as completed."""
        self.cursor.execute(
            "SELECT id, title, message, remind_at FROM reminders WHERE id = ?",
            (reminder_id,)
        )
        row = self.cursor.fetchone()
        
        if row:
            reminder = {
                'id': row[0],
                'title': row[1],
                'message': row[2],
                'remind_at': row[3]
            }
            self.on_reminder(reminder)
            
            # Mark as completed
            self.cursor.execute("UPDATE reminders SET completed = 1 WHERE id = ?", (reminder_id,))
            self.conn.commit()
    
    def add_event(self, title: str, start_time: datetime, end_time: Optional[datetime] = None, description: str = "") -> int:
        """
        Add a calendar event.
        
        Args:
            title: Event title
            start_time: Event start time
            end_time: Optional event end time
            description: Optional description
            
        Returns:
            Event ID
        """
        self.cursor.execute(
            "INSERT INTO events (title, description, start_time, end_time) VALUES (?, ?, ?, ?)",
            (title, description, start_time.isoformat(), end_time.isoformat() if end_time else None)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_reminder(self, title: str, remind_at: datetime, message: str = "") -> int:
        """
        Add a reminder.
        
        Args:
            title: Reminder title
            remind_at: When to trigger the reminder
            message: Optional message
            
        Returns:
            Reminder ID
        """
        self.cursor.execute(
            "INSERT INTO reminders (title, message, remind_at) VALUES (?, ?, ?)",
            (title, message, remind_at.isoformat())
        )
        self.conn.commit()
        reminder_id = self.cursor.lastrowid
        
        # Schedule the reminder
        if self.scheduler and remind_at > datetime.now():
            self.scheduler.add_job(
                self._trigger_reminder,
                trigger=DateTrigger(run_date=remind_at),
                args=[reminder_id],
                id=f"reminder_{reminder_id}",
                replace_existing=True
            )
            logging.info("Scheduled reminder: %s at %s", title, remind_at)
        
        return reminder_id
    
    def get_upcoming_events(self, days: int = 7) -> List[Dict]:
        """Get upcoming events within the next N days."""
        now = datetime.now()
        future = now + timedelta(days=days)
        
        self.cursor.execute(
            "SELECT id, title, description, start_time, end_time FROM events WHERE start_time BETWEEN ? AND ? ORDER BY start_time",
            (now.isoformat(), future.isoformat())
        )
        
        events = []
        for row in self.cursor.fetchall():
            events.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'start_time': row[3],
                'end_time': row[4]
            })
        
        return events
    
    def delete_all_reminders(self) -> int:
        """
        Delete all pending reminders.
        
        Returns:
            int: Number of reminders deleted
        """
        self.cursor.execute("SELECT id FROM reminders WHERE completed = 0")
        reminder_ids = [row[0] for row in self.cursor.fetchall()]
        
        if not reminder_ids:
            return 0
            
        # Remove scheduled jobs
        if self.scheduler:
            for reminder_id in reminder_ids:
                job_id = f"reminder_{reminder_id}"
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
        
        # Delete from database
        self.cursor.execute("DELETE FROM reminders WHERE completed = 0")
        self.conn.commit()
        
        return len(reminder_ids)

    def get_pending_reminders(self) -> List[Dict]:
        """Get all pending (not completed) reminders."""
        self.cursor.execute(
            "SELECT id, title, message, remind_at FROM reminders WHERE completed = 0 ORDER BY remind_at"
        )
        
        reminders = []
        for row in self.cursor.fetchall():
            reminders.append({
                'id': row[0],
                'title': row[1],
                'message': row[2],
                'remind_at': row[3]
            })
        
        return reminders
    
    def parse_relative_time(self, text: str) -> Optional[datetime]:
        """
        Parse relative time expressions.
        
        Examples:
            "in 5 minutes"
            "in 2 hours"
            "tomorrow at 3pm"
            "at 10:40 PM"
            "at 3:30 pm"
            "9" (assumes next 9 AM or PM, whichever is closer)
            "9:20 p.m."
        """
        now = datetime.now()
        text = text.lower().strip()
        
        # Handle simple time formats like "9" or "9 p.m." or "9:20 p.m."
        simple_time = re.search(r'^(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)?$', text, re.IGNORECASE)
        if simple_time:
            hour = int(simple_time.group(1))
            minute = int(simple_time.group(2) or 0)
            period = (simple_time.group(3) or '').replace('.', '').lower()
            
            # Convert to 24-hour format
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            # If no period specified, choose the next occurrence of that hour
            if not period:
                # Create both AM and PM times
                am_time = now.replace(hour=hour % 12, minute=minute, second=0, microsecond=0)
                pm_time = now.replace(hour=(hour % 12) + 12, minute=minute, second=0, microsecond=0)
                
                # Find the next occurrence
                if now.hour < hour:  # If hour is in the future today
                    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:  # Otherwise, use the next day
                    target = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                return target
            
            # If we have a period, use that
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:  # If time is in the past, assume next day
                target += timedelta(days=1)
            return target
        
        # Handle "in X minutes/hours"
        match = re.search(r'in\s+(\d+)\s+(second|sec|secs|minute|hour|day|week)s?', text)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            
            if unit.startswith('sec'):
                return now + timedelta(seconds=value)
            elif unit.startswith('minute'):
                return now + timedelta(minutes=value)
            elif unit.startswith('hour'):
                return now + timedelta(hours=value)
            elif unit.startswith('day'):
                return now + timedelta(days=value)
            elif unit.startswith('week'):
                return now + timedelta(weeks=value)
        
        # Pattern: "tomorrow"
        if 'tomorrow' in text:
            tomorrow = now + timedelta(days=1)
            # Try to extract time
            time_match = re.search(r'(\d+):(\d+)\s*(am|pm)', text)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                period = time_match.group(3)
                if period == 'pm' and hour != 12:
                    hour += 12
                elif period == 'am' and hour == 12:
                    hour = 0
                return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            time_match = re.search(r'(\d+)\s*(am|pm)', text)
            if time_match:
                hour = int(time_match.group(1))
                if time_match.group(2) == 'pm' and hour != 12:
                    hour += 12
                return tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
            return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return None
    
    def __del__(self):
        """Cleanup."""
        try:
            if hasattr(self, 'scheduler') and getattr(self, 'scheduler', None):
                try:
                    self.scheduler.shutdown(wait=False)
                except Exception:
                    pass
            if hasattr(self, 'conn') and getattr(self, 'conn', None):
                try:
                    self.conn.close()
                except Exception:
                    pass
        except Exception:
            # Ignore cleanup errors at interpreter shutdown
            pass


def handle_calendar_command(command: str, calendar: CalendarManager) -> Optional[str]:
    """
    Handle calendar and reminder commands.
    
    Args:
        command: User command
        calendar: CalendarManager instance
        
    Returns:
        Response string or None if not a calendar command
    """
    command_lower = command.lower().strip()
    
    # Set reminder
    if command_lower.startswith("remind me") or "set reminder" in command_lower:
        # Extract the reminder details
        # Try pattern: "remind me to [task] at/in [time]"
        match = re.search(r'remind me (?:to\s+)?(.+?)\s+(?:at|in)\s+(.+)', command_lower)
        
        if match:
            title = match.group(1).strip()
            time_expr = match.group(2).strip()
            
            # Parse the full command to get the time (includes "at" or "in")
            remind_time = calendar.parse_relative_time(command_lower)
            if remind_time:
                calendar.add_reminder(title, remind_time)
                return f"Reminder set: '{title}' at {remind_time.strftime('%Y-%m-%d %H:%M')}, sir."
            else:
                return f"Couldn't parse time expression: {time_expr}"
        
        # Fallback: just "remind me [task]" without time
        match = re.search(r'remind me (?:to\s+)?(.+)', command_lower)
        if match:
            return "Please specify when you'd like to be reminded, sir. For example: 'remind me to call mom at 3 PM' or 'remind me to call mom in 30 minutes'"
        
        return "Please specify what to remind you about, sir."
    
    # Delete all reminders
    if "delete all reminders" in command_lower or "clear all reminders" in command_lower:
        count = calendar.delete_all_reminders()
        if count > 0:
            return f"Successfully deleted {count} pending reminder{'s' if count != 1 else ''}."
        return "No pending reminders to delete."
    
    # List reminders
    if "list reminders" in command_lower or "show reminders" in command_lower:
        reminders = calendar.get_pending_reminders()
        if not reminders:
            return "No pending reminders"
        
        result = "Pending reminders:\n"
        for r in reminders:
            result += f"- {r['title']} at {r['remind_at']}\n"
        return result.strip()
    
    # List events
    if "list events" in command_lower or "show events" in command_lower or "what's on my calendar" in command_lower:
        events = calendar.get_upcoming_events()
        if not events:
            return "No upcoming events"
        
        result = "Upcoming events:\n"
        for e in events:
            result += f"- {e['title']} at {e['start_time']}\n"
        return result.strip()
    
    return None


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    def my_reminder_handler(reminder):
        print(f"\n🔔 ALERT: {reminder['title']}")
        if reminder.get('message'):
            print(f"   {reminder['message']}")
    
    cal = CalendarManager(on_reminder=my_reminder_handler)
    
    # Test adding a reminder
    remind_time = datetime.now() + timedelta(seconds=10)
    cal.add_reminder("Test reminder", remind_time, "This is a test")
    print(f"Reminder set for {remind_time}")
    
    # Keep running to see the reminder trigger
    import time
    print("Waiting for reminder...")
    time.sleep(15)
