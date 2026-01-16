#!/usr/bin/env python3
"""
Test API connections and token status
"""
import os
import sys
from dotenv import load_dotenv
import requests
import json

# Load environment variables
load_dotenv()

def test_groq_api():
    """Test Groq API connection"""
    print("🧠 Testing GROQ API...")
    try:
        from groq import Groq
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            print("❌ GROQ_API_KEY not found")
            return False
        
        client = Groq(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        if response and response.choices:
            print("✅ GROQ API working - Response:", response.choices[0].message.content[:50])
            return True
        else:
            print("❌ GROQ API - No response")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        if "rate limit" in error_msg or "quota" in error_msg or "token" in error_msg:
            print("❌ GROQ API - Rate limit/quota issue:", e)
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            print("❌ GROQ API - Authentication issue:", e)
        else:
            print("❌ GROQ API - Error:", e)
        return False

def test_openai_api():
    """Test OpenAI API connection"""
    print("\n🤖 Testing OPENAI API...")
    try:
        import openai
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return False
        
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        if response and response.choices:
            print("✅ OPENAI API working - Response:", response.choices[0].message.content[:50])
            return True
        else:
            print("❌ OPENAI API - No response")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        if "rate limit" in error_msg or "quota" in error_msg or "token" in error_msg:
            print("❌ OPENAI API - Rate limit/quota issue:", e)
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            print("❌ OPENAI API - Authentication issue:", e)
        else:
            print("❌ OPENAI API - Error:", e)
        return False

def test_nasa_api():
    """Test NASA API connection"""
    print("\n🚀 Testing NASA API...")
    try:
        api_key = os.environ.get("NASA_API_KEY")
        if not api_key:
            print("❌ NASA_API_KEY not found")
            return False
        
        url = "https://api.nasa.gov/planetary/apod"
        params = {"api_key": api_key}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ NASA API working - Title:", data.get("title", "N/A"))
            return True
        elif response.status_code == 403:
            print("❌ NASA API - Forbidden (invalid API key)")
            return False
        else:
            print(f"❌ NASA API - Status {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        print("❌ NASA API - Error:", e)
        return False

def test_news_api():
    """Test News API connection"""
    print("\n📰 Testing NEWS API...")
    try:
        api_key = os.environ.get("NEWS_API_KEY")
        if not api_key:
            print("❌ NEWS_API_KEY not found")
            return False
        
        url = "https://newsapi.org/v2/top-headlines"
        params = {"country": "us", "apiKey": api_key}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok":
                print("✅ NEWS API working - Found", len(data.get("articles", [])), "articles")
                return True
            else:
                print("❌ NEWS API - Status not ok:", data.get("message", "Unknown error"))
                return False
        elif response.status_code == 401:
            print("❌ NEWS API - Unauthorized (invalid API key)")
            return False
        elif response.status_code == 429:
            print("❌ NEWS API - Rate limit exceeded")
            return False
        else:
            print(f"❌ NEWS API - Status {response.status_code}: {response.text[:100]}")
            return False
            
    except Exception as e:
        print("❌ NEWS API - Error:", e)
        return False

def test_server_health():
    """Test JAI server health"""
    print("\n🏥 Testing JAI Server Health...")
    try:
        response = requests.get("http://localhost:8080/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ JAI Server healthy - Response:", response.json())
            return True
        else:
            print(f"❌ JAI Server - Status {response.status_code}")
            return False
    except Exception as e:
        print("❌ JAI Server - Error:", e)
        return False

def test_server_command():
    """Test JAI server command endpoint"""
    print("\n💬 Testing JAI Server Command...")
    try:
        response = requests.post(
            "http://localhost:8080/command",
            json={"command": "hello", "suppress_tts": True},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ JAI Server Command working - Response:", data.get("response", "N/A")[:100])
            return True
        else:
            print(f"❌ JAI Server Command - Status {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        print("❌ JAI Server Command - Error:", e)
        return False

def main():
    print("=" * 60)
    print("JAI API AND SERVER DIAGNOSTIC")
    print("=" * 60)
    
    results = {}
    
    # Test all APIs
    results["GROQ"] = test_groq_api()
    results["OPENAI"] = test_openai_api()
    results["NASA"] = test_nasa_api()
    results["NEWS"] = test_news_api()
    results["JAI_SERVER"] = test_server_health()
    results["JAI_COMMAND"] = test_server_command()
    
    # Summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:15} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL SYSTEMS OPERATIONAL!")
        print("\nVoice mode should work. If it still fails, check:")
        print("• Microphone permissions")
        print("• Browser microphone access (for web interface)")
        print("• Network connectivity")
    else:
        print("⚠️ SOME SYSTEMS FAILED!")
        print("\n🔧 Troubleshooting:")
        if not results.get("GROQ", False):
            print("• Check GROQ_API_KEY - may be expired or hit quota")
            print("• Visit https://console.groq.com/ to check usage")
        if not results.get("OPENAI", False):
            print("• Check OPENAI_API_KEY - may be expired or hit quota")
            print("• Visit https://platform.openai.com/usage to check usage")
        if not results.get("JAI_SERVER", False):
            print("• Start JAI server: python jai_assistant.py")
        if not results.get("JAI_COMMAND", False):
            print("• Server is running but command endpoint failed")
            print("• Check server logs for errors")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
