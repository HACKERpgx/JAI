#!/usr/bin/env python3
"""
Simple Gmail test for JAI Assistant
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, '.')

def test_gmail_import():
    """Test if Gmail modules can be imported"""
    try:
        from gmail_oauth import GmailOAuth, send_gmail_email, test_gmail_connection
        print("✅ Gmail OAuth module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Gmail OAuth module: {e}")
        return False

def test_jai_gmail_integration():
    """Test JAI assistant Gmail integration"""
    try:
        import jai_assistant
        
        # Check if Gmail is available
        if hasattr(jai_assistant, 'GMAIL_AVAILABLE'):
            if jai_assistant.GMAIL_AVAILABLE:
                print("✅ Gmail integration available in JAI Assistant")
                
                # Test intent classification
                test_commands = [
                    "send email to test@example.com",
                    "test gmail",
                    "check gmail"
                ]
                
                for cmd in test_commands:
                    intent, args = jai_assistant.classify_intent(cmd)
                    print(f"   📝 '{cmd}' -> Intent: {intent}, Args: {args}")
                
                return True
            else:
                print("❌ Gmail integration not available in JAI Assistant")
                return False
        else:
            print("❌ GMAIL_AVAILABLE attribute not found in JAI Assistant")
            return False
            
    except Exception as e:
        print(f"❌ Error testing JAI integration: {e}")
        return False

def check_credentials():
    """Check if credentials file exists"""
    if os.path.exists('credentials.json'):
        print("✅ credentials.json found")
        return True
    else:
        print("❌ credentials.json not found")
        print("📋 Please copy credentials.json.template to credentials.json")
        print("   and fill in your Google Cloud OAuth credentials")
        return False

def main():
    """Main test function"""
    print("🔧 JAI Assistant Gmail Integration Test")
    print("=" * 40)
    
    # Test imports
    import_ok = test_gmail_import()
    
    # Check credentials
    creds_ok = check_credentials()
    
    # Test JAI integration
    if import_ok:
        jai_ok = test_jai_gmail_integration()
    else:
        jai_ok = False
    
    print("\n📊 Results:")
    print(f"   Gmail Import: {'✅' if import_ok else '❌'}")
    print(f"   Credentials: {'✅' if creds_ok else '❌'}")
    print(f"   JAI Integration: {'✅' if jai_ok else '❌'}")
    
    if import_ok and creds_ok and jai_ok:
        print("\n🎉 Gmail integration is ready!")
        print("\n📖 Usage:")
        print('   "send email to user@example.com"')
        print('   "test gmail"')
        print('   "check gmail connection"')
        print("\n🔐 First-time setup:")
        print("   1. Run JAI Assistant")
        print('   2. Say "test gmail"')
        print("   3. Complete OAuth in browser")
        print("   4. Start sending emails!")
    else:
        print("\n⚠️  Some issues found. Please check above.")

if __name__ == "__main__":
    main()
