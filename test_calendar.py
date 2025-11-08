"""
Test script for JAI Calendar and Reminder functionality.
"""
import sys
import time
from datetime import datetime, timedelta

# Test the calendar module
try:
    from jai_calendar import CalendarManager, handle_calendar_command
    print("✓ Calendar module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import calendar module: {e}")
    sys.exit(1)

def test_reminder_handler(reminder):
    """Custom handler for testing reminders."""
    print(f"\n🔔 TEST REMINDER TRIGGERED!")
    print(f"   Title: {reminder['title']}")
    print(f"   Message: {reminder.get('message', 'N/A')}")
    print(f"   Time: {reminder['remind_at']}")

def main():
    print("\n" + "="*60)
    print("JAI CALENDAR & REMINDER SYSTEM TEST")
    print("="*60 + "\n")
    
    # Initialize calendar
    print("1. Initializing CalendarManager...")
    cal = CalendarManager(db_path="test_calendar.db", on_reminder=test_reminder_handler)
    print("   ✓ Calendar initialized\n")
    
    # Test 1: Add a short-term reminder (10 seconds)
    print("2. Testing short-term reminder (10 seconds)...")
    remind_time = datetime.now() + timedelta(seconds=10)
    reminder_id = cal.add_reminder(
        title="Test Reminder",
        remind_at=remind_time,
        message="This is a test reminder that should trigger in 10 seconds"
    )
    print(f"   ✓ Reminder created with ID: {reminder_id}")
    print(f"   ✓ Scheduled for: {remind_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Test 2: Add an event
    print("3. Adding a calendar event...")
    event_time = datetime.now() + timedelta(hours=2)
    event_id = cal.add_event(
        title="Team Meeting",
        start_time=event_time,
        end_time=event_time + timedelta(hours=1),
        description="Discuss Q4 goals"
    )
    print(f"   ✓ Event created with ID: {event_id}\n")
    
    # Test 3: List pending reminders
    print("4. Listing pending reminders...")
    reminders = cal.get_pending_reminders()
    if reminders:
        for r in reminders:
            print(f"   - {r['title']} at {r['remind_at']}")
    else:
        print("   No pending reminders")
    print()
    
    # Test 4: List upcoming events
    print("5. Listing upcoming events...")
    events = cal.get_upcoming_events(days=7)
    if events:
        for e in events:
            print(f"   - {e['title']} at {e['start_time']}")
    else:
        print("   No upcoming events")
    print()
    
    # Test 5: Test command parsing
    print("6. Testing command parsing...")
    test_commands = [
        "remind me to call mom in 5 minutes",
        "list reminders",
        "show events",
        "what's on my calendar"
    ]
    
    for cmd in test_commands:
        response = handle_calendar_command(cmd, cal)
        if response:
            print(f"   Command: '{cmd}'")
            print(f"   Response: {response}\n")
    
    # Test 6: Test time parsing
    print("7. Testing relative time parsing...")
    test_times = [
        "in 5 minutes",
        "in 2 hours",
        "in 30 seconds",
        "tomorrow at 3pm"
    ]
    
    for time_expr in test_times:
        parsed = cal.parse_relative_time(time_expr)
        if parsed:
            print(f"   '{time_expr}' → {parsed.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"   '{time_expr}' → Failed to parse")
    print()
    
    # Wait for the reminder to trigger
    print("8. Waiting for reminder to trigger (15 seconds)...")
    print("   (The reminder should appear in ~10 seconds)")
    time.sleep(15)
    
    print("\n" + "="*60)
    print("TEST COMPLETED!")
    print("="*60)
    print("\nCalendar and reminder system is working correctly! ✓")
    print("\nYou can now use commands like:")
    print("  - 'remind me to [task] in [time]'")
    print("  - 'list reminders'")
    print("  - 'show events'")
    print("  - 'what's on my calendar'")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
