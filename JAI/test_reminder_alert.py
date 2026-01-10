"""
Test automatic reminder alerts - demonstrates how JAI will speak when time arrives.
This creates a reminder for 10 seconds from now and waits for it to trigger.
"""
import time
from datetime import datetime, timedelta
from jai_calendar import CalendarManager

def demo_alert_handler(reminder):
    """This simulates what JAI will do when reminder triggers."""
    title = reminder['title']
    current_time = datetime.now().strftime('%I:%M %p')
    
    print(f"\n{'='*60}")
    print(f"🔔 REMINDER ALERT 🔔")
    print(f"{'='*60}")
    print(f"Time: {current_time}")
    print(f"Task: {title}")
    print(f"{'='*60}")
    print(f"\n💬 JAI SPEAKS: 'Sir, it's time to {title}. Your reminder has triggered.'\n")
    print("(With TTS enabled, you would HEAR this spoken aloud!)")
    print(f"{'='*60}\n")

def main():
    print("\n" + "="*60)
    print("AUTOMATIC REMINDER ALERT TEST")
    print("="*60 + "\n")
    
    print("This demonstrates how JAI will automatically alert you")
    print("when a reminder time arrives.\n")
    
    # Initialize calendar with our demo handler
    cal = CalendarManager(db_path="test_reminder_alert.db", on_reminder=demo_alert_handler)
    
    # Set a reminder for 10 seconds from now
    remind_time = datetime.now() + timedelta(seconds=10)
    task = "open WhatsApp"
    
    print(f"Current time: {datetime.now().strftime('%I:%M:%S %p')}")
    print(f"Setting reminder: '{task}'")
    print(f"Reminder time: {remind_time.strftime('%I:%M:%S %p')}")
    print(f"\n⏳ Waiting 10 seconds for reminder to trigger...\n")
    
    cal.add_reminder(task, remind_time)
    
    # Wait for the reminder to trigger
    time.sleep(12)
    
    print("\n" + "="*60)
    print("TEST COMPLETE!")
    print("="*60)
    print("\n✅ This is exactly what will happen when you use JAI:")
    print("\n1. You say: 'JAI, remind me to open WhatsApp in 10 minutes'")
    print("2. JAI responds: 'Reminder set: open WhatsApp at [time], sir.'")
    print("3. After 10 minutes, JAI automatically:")
    print("   - Shows the alert on screen (🔔)")
    print("   - SPEAKS: 'Sir, it's time to open WhatsApp. Your reminder has triggered.'")
    print("\n🎤 With SPEAK_RESPONSES=true, you will HEAR JAI speak!")
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
