#!/usr/bin/env python3
# test_integration.py
"""
Integration test suite for JAI Assistant.
Tests all major components and their interactions.
"""
import sys
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_imports():
    """Test that all modules can be imported."""
    print("\n" + "="*60)
    print("Testing Module Imports")
    print("="*60)
    
    modules = [
        ('personality', 'Personality system'),
        ('tts', 'Text-to-Speech'),
        ('stt', 'Speech-to-Text'),
        ('memory', 'Memory system'),
        ('jai_controls', 'PC controls'),
        ('jai_media', 'Media controls'),
        ('jai_calendar', 'Calendar & reminders'),
    ]
    
    results = []
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"[OK] {description:30} OK")
            results.append(True)
        except ImportError as e:
            print(f"[FAIL] {description:30} FAILED: {e}")
            results.append(False)
    
    return all(results)


def test_personality():
    """Test personality module."""
    print("\n" + "="*60)
    print("Testing Personality Module")
    print("="*60)
    
    try:
        from personality import build_system_prompt, time_greeting
        
        prompt = build_system_prompt("Abdul")
        assert "Abdul" in prompt
        assert "JAI" in prompt
        print(f"[OK] System prompt generated: {len(prompt)} chars")
        
        greeting = time_greeting("Abdul")
        assert "Abdul" in greeting
        print(f"[OK] Time greeting: {greeting}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Personality test failed: {e}")
        return False


def test_tts():
    """Test text-to-speech."""
    print("\n" + "="*60)
    print("Testing Text-to-Speech")
    print("="*60)
    
    try:
        from tts import speak
        
        # Test with a short phrase (non-blocking)
        result = speak("Testing JAI speech system", timeout=5)
        if result:
            print("[OK] TTS working - you should hear audio")
        else:
            print("[WARN] TTS completed but may have issues")
        
        return True
    except Exception as e:
        print(f"[FAIL] TTS test failed: {e}")
        return False


def test_memory():
    """Test memory system."""
    print("\n" + "="*60)
    print("Testing Memory System")
    print("="*60)
    
    try:
        from memory import JAIMemory
        
        mem = JAIMemory(db_path="test_memory.db")
        
        # Test short-term memory
        mem.add_short_term({"user": "test", "response": "test response"})
        recent = mem.get_short_term(limit=1)
        assert len(recent) > 0
        print(f"[OK] Short-term memory: {len(recent)} entries")
        
        # Test long-term memory
        mem.remember_long_term("test_key", "test_value", importance=0.8)
        value = mem.recall_long_term("test_key")
        assert value == "test_value"
        print(f"[OK] Long-term memory: stored and retrieved")
        
        # Test search
        results = mem.search_memories("test")
        print(f"[OK] Memory search: {len(results)} results")
        
        # Cleanup
        mem.forget_long_term("test_key")
        
        return True
    except Exception as e:
        print(f"[FAIL] Memory test failed: {e}")
        return False


def test_calendar():
    """Test calendar and reminder system."""
    print("\n" + "="*60)
    print("Testing Calendar & Reminders")
    print("="*60)
    
    try:
        from jai_calendar import CalendarManager
        
        def test_reminder_handler(reminder):
            print(f"  → Reminder triggered: {reminder['title']}")
        
        cal = CalendarManager(db_path="test_calendar.db", on_reminder=test_reminder_handler)
        
        # Test adding event
        tomorrow = datetime.now() + timedelta(days=1)
        event_id = cal.add_event("Test Event", tomorrow, description="Integration test")
        print(f"[OK] Event created: ID {event_id}")
        
        # Test adding reminder
        future = datetime.now() + timedelta(seconds=5)
        reminder_id = cal.add_reminder("Test Reminder", future, "This is a test")
        print(f"[OK] Reminder created: ID {reminder_id}")
        
        # Test parsing relative time
        parsed = cal.parse_relative_time("in 30 minutes")
        assert parsed is not None
        print(f"[OK] Time parsing: 'in 30 minutes' → {parsed.strftime('%H:%M')}")
        
        # Test listing
        events = cal.get_upcoming_events()
        reminders = cal.get_pending_reminders()
        print(f"[OK] Upcoming events: {len(events)}")
        print(f"[OK] Pending reminders: {len(reminders)}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Calendar test failed: {e}")
        return False


def test_media():
    """Test media controls."""
    print("\n" + "="*60)
    print("Testing Media Controls")
    print("="*60)
    
    try:
        from jai_media import MediaController, YouTubeController
        
        media = MediaController()
        
        # Test volume (non-destructive)
        current_vol = media.get_volume()
        if current_vol is not None:
            print(f"[OK] Current volume: {current_vol}%")
            print(f"[OK] Muted: {media.is_muted()}")
        else:
            print("[WARN] Volume control not available (pycaw may not be installed)")
        
        youtube = YouTubeController()
        print("[OK] YouTube controller initialized")
        
        return True
    except Exception as e:
        print(f"[FAIL] Media test failed: {e}")
        return False


def test_jai_server():
    """Test JAI server can be imported and initialized."""
    print("\n" + "="*60)
    print("Testing JAI Server")
    print("="*60)
    
    try:
        from jai_assistant import app, execute_command, UserSession
        
        print("[OK] JAI server imported successfully")
        
        # Test creating a session
        session = UserSession("test_user")
        print(f"[OK] User session created: {session.username}")
        
        # Test a simple command (without actually running server)
        response = execute_command("hello", session)
        print(f"[OK] Command executed: {len(response)} chars response")
        
        return True
    except Exception as e:
        print(f"[FAIL] JAI server test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("JAI INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Module Imports", test_imports),
        ("Personality", test_personality),
        ("Text-to-Speech", test_tts),
        ("Memory System", test_memory),
        ("Calendar & Reminders", test_calendar),
        ("Media Controls", test_media),
        ("JAI Server", test_jai_server),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n[FAIL] {name} crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status:10} {name}")
    
    print("="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! JAI is ready to go!")
        return 0
    else:
        print(f"\n[WARN] {total - passed} test(s) failed. Check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
