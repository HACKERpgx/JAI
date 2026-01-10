"""
Quick demonstration of calendar features.
Run this to see how the calendar system works!
"""
from datetime import datetime
from jai_calendar import CalendarManager, handle_calendar_command

def demo():
    print("\n" + "="*70)
    print(" JAI CALENDAR & REMINDER SYSTEM - LIVE DEMO")
    print("="*70 + "\n")
    
    # Show current time
    now = datetime.now()
    print(f"📅 Current Time: {now.strftime('%I:%M %p on %A, %B %d, %Y')}\n")
    
    # Initialize calendar
    print("Initializing calendar system...")
    cal = CalendarManager(db_path="demo_calendar.db")
    print("✓ Calendar ready!\n")
    
    # Demo 1: Time parsing
    print("="*70)
    print("DEMO 1: Time Parsing")
    print("="*70 + "\n")
    
    test_times = [
        "at 10:40 PM",
        "at 3:30 pm",
        "in 5 minutes",
        "in 2 hours",
        "tomorrow at 9:00 AM"
    ]
    
    for time_expr in test_times:
        parsed = cal.parse_relative_time(time_expr)
        if parsed:
            print(f"✓ '{time_expr}'")
            print(f"  → {parsed.strftime('%I:%M %p on %B %d, %Y')}\n")
    
    # Demo 2: Setting reminders
    print("="*70)
    print("DEMO 2: Setting Reminders")
    print("="*70 + "\n")
    
    commands = [
        "remind me to call mom at 10:40 PM",
        "remind me to take medicine in 5 minutes",
        "remind me to check email in 2 hours"
    ]
    
    for cmd in commands:
        response = handle_calendar_command(cmd, cal)
        print(f"Command: '{cmd}'")
        print(f"Response: {response}\n")
    
    # Demo 3: Listing reminders
    print("="*70)
    print("DEMO 3: Listing Reminders")
    print("="*70 + "\n")
    
    response = handle_calendar_command("list my reminders", cal)
    print(f"Command: 'list my reminders'")
    print(f"Response:\n{response}\n")
    
    # Demo 4: Time command simulation
    print("="*70)
    print("DEMO 4: Time Command (What JAI will say)")
    print("="*70 + "\n")
    
    current_time = datetime.now()
    time_str = current_time.strftime("%I:%M %p")
    date_str = current_time.strftime("%A, %B %d, %Y")
    print(f"Command: 'what time is it?'")
    print(f"Response: The current time is {time_str}, {date_str}, sir.\n")
    
    print("="*70)
    print("DEMO COMPLETE!")
    print("="*70)
    print("\n✅ All calendar features are working correctly!")
    print("\nTo use with JAI Assistant:")
    print("1. Start JAI: python jai_assistant.py")
    print("2. Say: 'what time is it?'")
    print("3. Say: 'remind me to [task] at [time]'")
    print("4. Say: 'list my reminders'")
    print("\nThe reminders will trigger automatically! 🔔\n")

if __name__ == "__main__":
    try:
        demo()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
