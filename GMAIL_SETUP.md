# Gmail OAuth Setup Guide for JAI Assistant

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install google-auth==2.25.2 google-auth-oauthlib==1.2.0 google-auth-httplib2==0.2.0 google-api-python-client==2.108.0
```

### 2. Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable **Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Select "Desktop app"
   - Click "Create"
5. Download the JSON file and save it as `credentials.json` in the JAI_Assistant directory

### 3. Configure Credentials
Copy `credentials.json.template` to `credentials.json` and fill in your details:
```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID_HERE",
    "project_id": "YOUR_PROJECT_ID_HERE", 
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET_HERE",
    "redirect_uris": ["http://localhost"]
  }
}
```

## 📧 Usage Examples

### Send Email
```
"send email to user@example.com"
"send email to john@company.com with subject Meeting Update"
"email sarah@gmail.com about project status"
```

### Test Connection
```
"test gmail"
"check gmail connection"
"verify gmail"
```

## 🔐 First-Time Authentication

1. Run JAI Assistant
2. Say: "test gmail"
3. A browser window will open for Google OAuth
4. Sign in with your Google account
5. Grant permission to send emails
6. Authentication token will be saved as `token.pickle`

## 🛠️ Troubleshooting

### Common Issues

**"Gmail functionality is not available"**
- Install the required packages (see step 1)
- Restart JAI Assistant

**"credentials.json not found"**
- Download credentials from Google Cloud Console
- Save as `credentials.json` in JAI_Assistant directory

**"Insufficient Permission" error**
- Delete `token.pickle` file
- Run "test gmail" again
- Re-authorize with correct scopes

**OAuth flow doesn't complete**
- Make sure redirect URIs include `http://localhost`
- Check that Gmail API is enabled in Google Cloud Console

### Test the Setup
```bash
python test_gmail_simple.py
```

## 🔒 Security Notes

- `credentials.json` contains sensitive information - keep it secure
- `token.pickle` stores your authentication token - don't share it
- OAuth tokens expire and will refresh automatically
- Only Gmail send permission is requested (no read access)

## 📱 Features Implemented

✅ **OAuth 2.0 Authentication** - Secure Google authentication  
✅ **Email Sending** - Send emails via Gmail API  
✅ **Intent Recognition** - Natural language email commands  
✅ **Error Handling** - Comprehensive error messages  
✅ **Token Management** - Automatic token refresh  
✅ **Email Validation** - Basic email format checking  
✅ **Connection Testing** - Verify Gmail connectivity  

## 🎯 Example Commands

```bash
# Basic email
"send email to friend@example.com"

# With subject
"send email to boss@company.com with subject Project Update"

# Test connection
"test gmail"

# Check if Gmail is working
"check gmail connection"
```

The Gmail integration is now fully functional and ready to use! 🎉
