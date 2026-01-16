#!/usr/bin/env python3
"""
Restart JAI server with voice client feature
"""
import subprocess
import time
import requests
import sys

def restart_jai_server():
    print("🔄 Restarting JAI Server with Voice Client Feature")
    print("=" * 60)
    
    try:
        # Check if server is running and stop it
        print("🛑 Stopping current server...")
        try:
            response = requests.get("http://localhost:8080/api/health", timeout=2)
            print("✅ Server was running, stopping...")
        except:
            print("ℹ️ Server was not running")
        
        # Start new server
        print("🚀 Starting JAI server with voice client feature...")
        print("This will start in the background...")
        
        # Start server in background
        subprocess.Popen([
            sys.executable, "jai_assistant.py"
        ], cwd=".", creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(10):
            time.sleep(2)
            try:
                response = requests.get("http://localhost:8080/api/health", timeout=3)
                if response.status_code == 200:
                    print("✅ Server started successfully!")
                    break
            except:
                print(f"   Waiting... ({i+1}/10)")
        else:
            print("❌ Server failed to start")
            return False
        
        # Test voice client feature
        print("\n🎤 Testing voice client feature...")
        response = requests.get("http://localhost:8080/", timeout=5)
        html_content = response.text
        
        features = [
            ("Voice client section", "voice-client-section" in html_content),
            ("Talk to JAI button", "Talk to JAI" in html_content),
            ("Voice client JavaScript", "toggleVoiceClient" in html_content),
            ("Microphone status", "micStatus" in html_content)
        ]
        
        all_good = True
        for feature, found in features:
            status = "✅" if found else "❌"
            print(f"  {status} {feature}")
            if not found:
                all_good = False
        
        if all_good:
            print("\n🎉 Voice client feature is ready!")
            print("\n📱 How to use:")
            print("1. Open browser: http://localhost:8080/")
            print("2. Scroll to '🎙️ Voice Client Mode' section")
            print("3. Click the green 'Talk to JAI' button")
            print("4. Allow microphone permissions")
            print("5. Speak your command clearly")
            print("6. Click button again to stop recording")
            print("7. See JAI's response in the chat")
            print("\n🔥 Features:")
            print("- Instant voice interaction")
            print("- Visual feedback (green/red button)")
            print("- Real-time status updates")
            print("- Error handling")
            print("- Works alongside existing recording")
        else:
            print("\n⚠️ Some features may not be working properly")
            print("Try refreshing the browser (Ctrl+F5)")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error restarting server: {e}")
        return False

if __name__ == "__main__":
    restart_jai_server()
