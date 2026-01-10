#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for music and YouTube controls.
Tests all new media functionality without requiring the full JAI server.
"""
import sys
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from jai_media import handle_media_command

def test_command(command: str):
    """Test a single command and print result."""
    print(f"\n{'='*60}")
    print(f"Testing: '{command}'")
    print(f"{'='*60}")
    result = handle_media_command(command)
    if result:
        print(f"✅ Result: {result}")
    else:
        print(f"❌ Command not recognized as media command")
    return result is not None

def main():
    """Run all media control tests."""
    print("\n" + "="*60)
    print("JAI MEDIA CONTROLS TEST SUITE")
    print("="*60)
    
    test_cases = [
        # Volume controls
        ("set volume to 50", "Volume control"),
        ("volume up", "Volume increase"),
        ("volume down", "Volume decrease"),
        ("mute", "Mute audio"),
        ("unmute", "Unmute audio"),
        
        # YouTube controls
        ("play Bohemian Rhapsody on youtube", "YouTube play"),
        ("search youtube for python tutorial", "YouTube search"),
        ("open youtube", "Open YouTube"),
        ("youtube channel MrBeast", "YouTube channel"),
        ("play playlist chill vibes", "YouTube playlist"),
        
        # Music streaming
        ("play The Weeknd on spotify", "Spotify play"),
        ("open spotify", "Open Spotify"),
        ("play Levitating on apple music", "Apple Music"),
        
        # Generic music commands
        ("play music Blinding Lights", "Play music"),
        ("play song Shape of You by Ed Sheeran", "Play song with artist"),
        
        # Playback controls
        ("play", "Play/Pause"),
        ("pause", "Pause"),
        ("next", "Next track"),
        ("previous track", "Previous track"),
        ("skip", "Skip"),
        ("stop", "Stop playback"),
    ]
    
    passed = 0
    failed = 0
    
    for command, description in test_cases:
        print(f"\n📝 Test: {description}")
        if test_command(command):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed}/{len(test_cases)}")
    print(f"❌ Failed: {failed}/{len(test_cases)}")
    print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
    print("="*60)
    
    # Interactive mode
    print("\n💡 Want to test custom commands? (y/n)")
    choice = input("> ").strip().lower()
    
    if choice == 'y':
        print("\n🎮 Interactive Mode - Type 'exit' to quit")
        while True:
            command = input("\n🎤 Command: ").strip()
            if command.lower() in ['exit', 'quit', 'q']:
                break
            test_command(command)
    
    print("\n👋 Test complete!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
