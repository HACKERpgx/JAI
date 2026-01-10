"""
Quick test for time parsing functionality.
"""
from datetime import datetime
from jai_calendar import CalendarManager

def test_time_parsing():
    print("\n" + "="*60)
    print("TIME PARSING TEST")
    print("="*60 + "\n")
    
    cal = CalendarManager(db_path="test_calendar.db")
    
    # Get current time for reference
    now = datetime.now()
    print(f"Current time: {now.strftime('%I:%M %p on %A, %B %d, %Y')}\n")
    
    # Test cases
    test_cases = [
        "remind me to call mom at 10:40 PM",
        "at 3:30 pm",
        "at 11:59 PM",
        "in 5 minutes",
        "in 2 hours",
        "tomorrow at 9:00 AM",
        "tomorrow at 3:30 pm"
    ]
    
    print("Testing time expressions:\n")
    for test in test_cases:
        parsed = cal.parse_relative_time(test)
        if parsed:
            print(f"✓ '{test}'")
            print(f"  → {parsed.strftime('%I:%M %p on %A, %B %d, %Y')}")
            
            # Calculate time difference
            diff = parsed - now
            hours = diff.total_seconds() / 3600
            if hours < 1:
                minutes = diff.total_seconds() / 60
                print(f"  → In {minutes:.1f} minutes\n")
            elif hours < 24:
                print(f"  → In {hours:.1f} hours\n")
            else:
                days = hours / 24
                print(f"  → In {days:.1f} days\n")
        else:
            print(f"✗ '{test}' - Failed to parse\n")
    
    print("="*60)
    print("Test complete!")

if __name__ == "__main__":
    test_time_parsing()
