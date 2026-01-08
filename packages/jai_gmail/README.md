# jai-gmail

Gmail OAuth integration for JAI Assistant. Provides simple helpers to authenticate via Google OAuth and send emails using the Gmail API.

## Installation

```bash
pip install jai-gmail
```

Or from source:

```bash
pip install -e .
```

## Quick Start

```python
from jai_gmail import send_gmail_email, test_gmail_connection

# First time will prompt OAuth in your browser
result = test_gmail_connection()
print(result)

send_gmail_email("you@example.com", "Hello", "This is a test from JAI Gmail")
```

## Google Cloud Setup

1. Enable Gmail API in Google Cloud Console
2. Create OAuth 2.0 Client ID (Desktop app) and download the JSON
3. Save the file as `credentials.json` in your working directory

## Notes

- This package stores tokens in `token.pickle` by default (same dir)
- Scopes used: `gmail.send`, `gmail.compose`
- Do not commit `credentials.json` or `token.pickle`

## Requirements

- google-auth==2.25.2
- google-auth-oauthlib==1.2.0
- google-auth-httplib2==0.2.0
- google-api-python-client==2.108.0

## License

MIT
