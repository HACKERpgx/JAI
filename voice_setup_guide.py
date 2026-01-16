#!/usr/bin/env python3
"""
JAI Voice Mode Setup Guide and Tester
"""
import os
import sys
import time
import requests
import subprocess
from threading import Thread
import signal

def check_server_running():
    """Check if JAI server is running"""
    try:
        response = requests.get("http://localhost:8080/healthz", timeout=3)
        return response.status_code == 200
    except:
        return False

def start_server():
    """Start JAI server in background"""
    print("🚀 Starting JAI server...")
    try:
        # Start server in background
        process = subprocess.Popen(
            [sys.executable, "jai_assistant.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Wait for server to start
        for i in range(30):  # Wait up to 30 seconds
            if check_server_running():
                print("✅ Server started successfully!")
                return process
            time.sleep(1)
            print(f"⏳ Waiting for server... ({i+1}/30)")
        
        print("❌ Server failed to start within 30 seconds")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return None

def test_voice_client():
    """Test voice client connection"""
    print("\n🎤 Testing voice client connection...")
    try:
        # Import and test voice client
        from voice_client import JAIVoiceClient
        
        client = JAIVoiceClient(
            server_url="http://localhost:8080",
            username="user1", 
            password="pass1",
            wake_word="test"
        )
        
        # Test server connection
        response = client.send_command("test connection")
        if "Cannot connect" in response:
            print("❌ Voice client cannot connect to server")
            return False
        else:
            print("✅ Voice client connected successfully!")
            print(f"Server response: {response}")
            return True
            
    except Exception as e:
        print(f"❌ Voice client test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("JAI VOICE MODE SETUP GUIDE")
    print("=" * 60)
    
    # Check if server is already running
    if check_server_running():
        print("✅ JAI server is already running!")
        server_process = None
    else:
        print("❌ JAI server is not running")
        server_process = start_server()
        if not server_process:
            print("\n❌ Failed to start server. Please check:")
            print("1. All dependencies are installed: pip install -r requirements.txt")
            print("2. Port 8080 is not blocked by firewall")
            print("3. No other application is using port 8080")
            return 1
    
    # Test voice client connection
    if test_voice_client():
        print("\n🎉 SUCCESS! Voice mode is ready to use!")
        print("\n📋 NEXT STEPS:")
        print("1. Open a NEW terminal window")
        print("2. Run: python voice_client.py")
        print("3. Say the wake word: 'Activate aj'")
        print("4. Start asking questions!")
        
        print("\n🌐 ALTERNATIVE - Web Interface:")
        print("1. Open browser to: http://localhost:3000")
        print("2. Click the microphone button")
        print("3. Allow microphone access")
        print("4. Speak your command")
        
        if server_process:
            print(f"\n💡 Server is running in background (PID: {server_process.pid})")
            print("   Press Ctrl+C in this window to stop the server")
            
            try:
                # Keep server running
                server_process.wait()
            except KeyboardInterrupt:
                print("\n👋 Stopping server...")
                server_process.terminate()
                server_process.wait()
                print("✅ Server stopped")
        
        return 0
    else:
        print("\n❌ Voice client test failed")
        if server_process:
            server_process.terminate()
        return 1

if __name__ == "__main__":
    sys.exit(main())
