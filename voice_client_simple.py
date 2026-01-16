#!/usr/bin/env python3
"""
Simple voice client with easier wake word
"""
import os
import sys
from voice_client import JAIVoiceClient

def main():
    print("🎤 JAI Voice Client - Simple Wake Word")
    print("=" * 50)
    print("Wake word: 'hello' (easier to detect)")
    print("Or try: 'computer'")
    print("Or try: 'assistant'")
    print("=" * 50)
    
    try:
        # Try with simpler wake word
        client = JAIVoiceClient(
            server_url="http://localhost:8080",
            username="user1",
            password="pass1",
            wake_word="hello"  # Much simpler wake word
        )
        client.run(continuous=True)
        
    except KeyboardInterrupt:
        print("\n👋 Voice client stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
