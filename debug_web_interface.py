#!/usr/bin/env python3
"""
Debug the web interface microphone issue
"""
import webbrowser
import time

def main():
    print("🌐 JAI Web Interface Debug")
    print("=" * 50)
    
    print("📋 Checking web interface setup...")
    
    # Check if web server is running
    try:
        import requests
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Web server running on port 3000")
        else:
            print(f"❌ Web server error: {response.status_code}")
    except:
        print("❌ Web server not running on port 3000")
        return
    
    # Check if JAI server is running
    try:
        response = requests.get("http://localhost:8080/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ JAI server running on port 8080")
        else:
            print(f"❌ JAI server error: {response.status_code}")
    except:
        print("❌ JAI server not running on port 8080")
        return
    
    print("\n🔧 Troubleshooting Steps:")
    print("1. Open browser to: http://localhost:3000")
    print("2. Press F12 to open Developer Tools")
    print("3. Click Console tab")
    print("4. Click the microphone button")
    print("5. Check for any error messages in console")
    
    print("\n🎯 Expected Behavior:")
    print("- Button should turn red when recording")
    print("- Status should show 'Recording...'")
    print("- After stopping, should show 'Processing...'")
    print("- Then show response from JAI")
    
    print("\n⚠️ Common Issues:")
    print("- Microphone permission denied")
    print("- Browser blocking microphone access")
    print("- API endpoint mismatch")
    print("- JavaScript errors")
    
    # Open browser automatically
    try:
        print("\n🌐 Opening web interface...")
        webbrowser.open("http://localhost:3000")
        print("✅ Browser opened to http://localhost:3000")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print("Please manually open: http://localhost:3000")

if __name__ == "__main__":
    main()
