#!/usr/bin/env python3
"""
Quick Gmail OAuth test - triggers authentication flow
"""

import sys
import os
sys.path.insert(0, '.')

from gmail_oauth import test_gmail_connection

def main():
    print("🔧 Testing Gmail OAuth Connection...")
    print("📝 If browser opens, complete the authentication")
    print("=" * 50)
    
    result = test_gmail_connection()
    
    if result['success']:
        print("\n🎉 SUCCESS! Gmail connection established!")
        print(f"📧 Connected as: {result.get('email_address', 'Unknown')}")
        print(f"📨 Total messages: {result.get('messages_total', 'Unknown')}")
        print("\n✅ Gmail is ready to use in JAI Assistant!")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Gmail API is enabled in Google Cloud Console")
        print("2. Check that credentials.json is correctly configured")
        print("3. Try running this test again")

if __name__ == "__main__":
    main()
