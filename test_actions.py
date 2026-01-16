#!/usr/bin/env python3
"""
Test if JAI server can perform actions
"""
import requests
import json

def test_server_actions():
    """Test various commands to see what works"""
    print("🧪 Testing JAI Server Actions...")
    print("=" * 50)
    
    test_commands = [
        "hello",
        "what time is it", 
        "tell me a joke",
        "what's the weather like",
        "open calculator",
        "play music",
        "set a reminder for 5 minutes",
        "search for python programming"
    ]
    
    for cmd in test_commands:
        print(f"\n📝 Testing: '{cmd}'")
        try:
            response = requests.post(
                "http://localhost:8080/command",
                json={"command": cmd, "suppress_tts": True},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('response', 'No response')
                print(f"✅ Response: {result[:100]}...")
            else:
                print(f"❌ Error {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)

def test_voice_client_action():
    """Test voice client with a simple command"""
    print("\n🎤 Testing Voice Client Action...")
    try:
        from voice_client_simple import main as voice_main
        # We'll test the send_command method directly
        from voice_client import JAIVoiceClient
        
        client = JAIVoiceClient(
            server_url="http://localhost:8080",
            username="user1",
            password="pass1",
            wake_word="hello"
        )
        
        # Test a few commands
        test_cmds = ["what time is it", "hello", "tell me something interesting"]
        
        for cmd in test_cmds:
            print(f"\n🎤 Voice Client Test: '{cmd}'")
            response = client.send_command(cmd)
            print(f"🤖 Response: {response[:100]}...")
            
    except Exception as e:
        print(f"❌ Voice client test error: {e}")

def check_server_logs():
    """Check if there are any server errors"""
    print("\n📋 Checking for server logs...")
    try:
        import os
        log_files = ['jai_assistant.log', 'voice_client.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"\n📄 {log_file} (last 5 lines):")
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:
                        print(f"   {line.strip()}")
            else:
                print(f"📄 {log_file}: Not found")
                
    except Exception as e:
        print(f"❌ Log check error: {e}")

if __name__ == "__main__":
    test_server_actions()
    test_voice_client_action()
    check_server_logs()
