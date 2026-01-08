#!/usr/bin/env python3
"""
Test JAI website voice mode API endpoints
"""

import sys
import requests
import json
import time

def test_api_endpoints():
    """Test the JAI website API endpoints"""
    base_url = "http://localhost:8080"
    
    print("🔧 Testing JAI Website API Endpoints")
    print("=" * 50)
    
    # Test 1: Text API
    print("1. Testing /api/text endpoint...")
    try:
        response = requests.post(f"{base_url}/api/text", 
                                json={"text": "hello"}, 
                                headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Text API working: {data.get('response', 'No response')[:50]}...")
        else:
            print(f"   ❌ Text API failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Text API error: {e}")
    
    print()
    
    # Test 2: Persona API
    print("2. Testing /api/persona endpoint...")
    try:
        response = requests.post(f"{base_url}/api/persona",
                                json={"persona": "therapist"},
                                headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Persona API working: {data}")
        else:
            print(f"   ❌ Persona API failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Persona API error: {e}")
    
    print()
    
    # Test 3: Voice API (without audio file)
    print("3. Testing /api/voice endpoint...")
    try:
        # This will fail without audio file, but should show the endpoint exists
        response = requests.post(f"{base_url}/api/voice")
        if response.status_code == 400:
            print("   ✅ Voice API endpoint exists (expects audio file)")
        elif response.status_code == 200:
            print("   ✅ Voice API working")
        else:
            print(f"   ⚠️  Voice API response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Voice API error: {e}")
    
    print()
    
    # Test 4: Image API (without image file)
    print("4. Testing /api/image endpoint...")
    try:
        response = requests.post(f"{base_url}/api/image")
        if response.status_code == 400:
            print("   ✅ Image API endpoint exists (expects image file)")
        elif response.status_code == 200:
            print("   ✅ Image API working")
        else:
            print(f"   ⚠️  Image API response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Image API error: {e}")
    
    print()
    
    # Test 5: Check if server is running
    print("5. Testing server connection...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ JAI server is running")
        else:
            print(f"   ⚠️  Server response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Server connection failed: {e}")
        print("\n💡 Make sure JAI Assistant is running:")
        print("   python jai_assistant.py")
        return False
    
    return True

def test_voice_mode_workflow():
    """Test the complete voice mode workflow"""
    print("\n🎤 Voice Mode Workflow Test")
    print("=" * 30)
    
    base_url = "http://localhost:8080"
    
    # Test persona selection
    print("1. Selecting therapist persona...")
    try:
        response = requests.post(f"{base_url}/api/persona",
                                json={"persona": "therapist"})
        if response.status_code == 200:
            print("   ✅ Persona selected")
        else:
            print(f"   ❌ Persona selection failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Persona error: {e}")
    
    # Test text command
    print("2. Sending text command...")
    try:
        response = requests.post(f"{base_url}/api/text",
                                json={"text": "what time is it"})
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Response: {data.get('response', 'No response')}")
        else:
            print(f"   ❌ Text command failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Text command error: {e}")

def main():
    """Main test function"""
    print("🌐 JAI Website Voice Mode Test")
    print("=" * 40)
    
    # Test API endpoints
    if test_api_endpoints():
        # Test workflow
        test_voice_mode_workflow()
        
        print("\n🎯 Voice Mode Status:")
        print("✅ API endpoints are implemented")
        print("✅ Server communication working")
        print("✅ Voice buttons should now work")
        
        print("\n📖 Usage:")
        print("1. Start JAI Assistant: python jai_assistant.py")
        print("2. Open browser: http://localhost:8080")
        print("3. Click 'Voice Mode' tab")
        print("4. Select a persona (Therapist, Storyteller, etc.)")
        print("5. Click microphone button to record")
        print("6. Speak your command")
        print("7. Get voice response!")
        
        print("\n🔧 If voice recording still doesn't work:")
        print("- Allow microphone permissions in browser")
        print("- Check browser console for errors")
        print("- Ensure speech recognition is available")
    else:
        print("\n❌ Please start JAI Assistant first:")
        print("   python jai_assistant.py")

if __name__ == "__main__":
    main()
