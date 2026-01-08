from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import base64
import os

# Scopes allow reading, modifying, labeling, and sending email
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def read_emails(service, max_results=10):
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject']
        ).execute()
        headers = msg_data.get('payload', {}).get('headers', [])
        subject = next((h.get('value') for h in headers if h.get('name', '').lower() == 'subject'), 'No subject')
        print(f"Subject: {subject}")  # JAI can classify here (e.g., simple rules or AI model)

def send_reply(service, thread_id, reply_text):
    message = f"To: sender@example.com\nSubject: Re: Original\n\n{reply_text}"
    raw = base64.urlsafe_b64encode(message.encode()).decode()
    service.users().messages().send(userId='me', body={'raw': raw, 'threadId': thread_id}).execute()

if __name__ == '__main__':
    # Usage in JAI
    service = authenticate_gmail()
    read_emails(service)  # JAI handles: categorize, prioritize
    # send_reply(service, 'threadId', 'Automated reply from JAI')  # Extend with AI logic
