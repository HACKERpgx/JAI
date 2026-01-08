#!/usr/bin/env python3
"""
Test sending an email via JAI Assistant Gmail integration
"""

import sys
sys.path.insert(0, '.')

from gmail_oauth import send_gmail_email

def main():
    print("📧 Testing Gmail Email Sending...")
    print("=" * 40)
    
    # Ask for recipient
    recipient = input("Enter your email address to send a test email: ").strip()
    if not recipient:
        print("❌ No recipient provided")
        return
    
    if '@' not in recipient:
        print("❌ Invalid email address")
        return
    
    # Send test email
    subject = "✅ JAI Assistant Gmail Test - SUCCESS!"
    body = f"""🎉 Congratulations!

JAI Assistant Gmail OAuth integration is now fully functional!

📧 This email was sent using:
   ✅ Google's official OAuth libraries
   ✅ Secure Gmail API integration  
   ✅ Natural language commands
   ✅ Proper authentication flow

🔗 Integration Details:
   - Gmail API: Connected
   - OAuth: Authenticated
   - Scopes: gmail.send + gmail.compose
   - Status: READY TO USE

📖 Next Steps:
   1. Start JAI Assistant
   2. Say: "send email to someone@example.com"
   3. Enjoy email automation!

Sent at: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Best regards,
JAI Assistant 🤖
"""
    
    print(f"📤 Sending test email to {recipient}...")
    result = send_gmail_email(recipient, subject, body)
    
    if result['success']:
        print("🎉 EMAIL SENT SUCCESSFULLY!")
        print(f"📧 Message ID: {result.get('message_id', 'N/A')}")
        print("\n✅ Gmail integration is COMPLETE and WORKING!")
        print("\n📖 Usage Examples in JAI Assistant:")
        print('   "send email to friend@example.com"')
        print('   "send email to boss@company.com with subject Meeting Update"')
        print('   "test gmail"')
    else:
        print(f"❌ Failed to send email: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
