#!/usr/bin/env python3
"""
Test script for Gmail OAuth functionality in JAI Assistant
"""

import os
import sys
from gmail_oauth import GmailOAuth, send_gmail_email, test_gmail_connection

def test_gmail_setup():
    """Test Gmail OAuth setup and connection"""
    print("🔧 Testing Gmail OAuth Setup...")
    
    # Check if credentials file exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("📋 Please follow these steps:")
        print("   1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("   2. Create a new project or select existing one")
        print("   3. Enable Gmail API")
        print("   4. Create OAuth 2.0 Client ID credentials")
        print("   5. Download credentials.json and place it in the JAI_Assistant directory")
        print("   6. Copy credentials.json.template to credentials.json and fill in your details")
        return False
    
    print("✅ credentials.json found")
    
    # Test connection
    print("🔗 Testing Gmail connection...")
    result = test_gmail_connection()
    
    if result['success']:
        print(f"✅ Gmail connection successful!")
        print(f"   📧 Email: {result.get('email_address', 'Unknown')}")
        print(f"   📨 Total messages: {result.get('messages_total', 'Unknown')}")
        return True
    else:
        print(f"❌ Gmail connection failed: {result.get('error', 'Unknown error')}")
        return False

def test_send_email():
    """Test sending an email"""
    print("\n📧 Testing Email Sending...")
    
    # Ask for recipient email
    recipient = input("Enter recipient email address (or press Enter to skip): ").strip()
    if not recipient:
        print("⏭️  Email test skipped")
        return True
    
    # Send test email
    subject = "JAI Assistant Gmail Test"
    body = f"""Hello!

This is a test email from JAI Assistant's Gmail OAuth functionality.

If you're receiving this, it means:
✅ OAuth authentication is working
✅ Gmail API integration is successful
✅ Email sending is functional

Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
JAI Assistant
"""
    
    print(f"📤 Sending test email to {recipient}...")
    result = send_gmail_email(recipient, subject, body)
    
    if result['success']:
        print(f"✅ Email sent successfully!")
        print(f"   📧 Message ID: {result.get('message_id', 'N/A')}")
        return True
    else:
        print(f"❌ Failed to send email: {result.get('error', 'Unknown error')}")
        return False

def test_jai_integration():
    """Test JAI assistant integration"""
    print("\n🤖 Testing JAI Assistant Integration...")
    
    try:
        # Import JAI assistant
        sys.path.append('.')
        import jai_assistant
        
        # Check if Gmail is available
        if hasattr(jai_assistant, 'GMAIL_AVAILABLE') and jai_assistant.GMAIL_AVAILABLE:
            print("✅ Gmail integration available in JAI Assistant")
            
            # Test intent classification
            test_commands = [
                "send email to test@example.com with subject Test",
                "test gmail",
                "check gmail connection"
            ]
            
            for cmd in test_commands:
                intent, args = jai_assistant.classify_intent(cmd)
                print(f"   📝 '{cmd}' -> Intent: {intent}, Args: {args}")
            
            return True
        else:
            print("❌ Gmail integration not available in JAI Assistant")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import JAI Assistant: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing JAI integration: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 JAI Assistant Gmail OAuth Test Suite")
    print("=" * 50)
    
    # Test Gmail setup
    setup_ok = test_gmail_setup()
    
    if setup_ok:
        # Test email sending
        email_ok = test_send_email()
        
        # Test JAI integration
        jai_ok = test_jai_integration()
        
        print("\n📊 Test Results:")
        print(f"   Gmail Setup: {'✅' if setup_ok else '❌'}")
        print(f"   Email Sending: {'✅' if email_ok else '❌'}")
        print(f"   JAI Integration: {'✅' if jai_ok else '❌'}")
        
        if setup_ok and email_ok and jai_ok:
            print("\n🎉 All tests passed! Gmail OAuth is ready to use.")
            print("\n📖 Usage Examples:")
            print('   "send email to user@example.com with subject Meeting Update"')
            print('   "test gmail"')
            print('   "check gmail connection"')
        else:
            print("\n⚠️  Some tests failed. Please check the errors above.")
    else:
        print("\n❌ Gmail setup failed. Please configure credentials.json first.")
        print("\n📋 Quick Setup Guide:")
        print("   1. Copy credentials.json.template to credentials.json")
        print("   2. Fill in your Google Cloud OAuth credentials")
        print("   3. Run this test again")

if __name__ == "__main__":
    from datetime import datetime
    main()
