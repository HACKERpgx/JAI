"""
JAI Gmail: OAuth authentication and email sending helpers using Gmail API.
"""

import os
import pickle
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any

try:
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_APIS_AVAILABLE = True
except ImportError:
    GOOGLE_APIS_AVAILABLE = False

__all__ = [
    "GmailOAuth",
    "send_gmail_email",
    "test_gmail_connection",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

class GmailOAuth:
    """Handles Gmail OAuth authentication and email sending"""

    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.pickle'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        # Use broader Gmail scopes to avoid permission issues
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.compose'
        ]
        self.service = None
        self.creds = None

        if not GOOGLE_APIS_AVAILABLE:
            raise ImportError("Google APIs not available. Install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail using OAuth 2.0 flow
        Returns True if authentication successful, False otherwise
        """
        try:
            # Load existing credentials if available
            creds_valid = True
            if os.path.exists(self.token_file):
                with open(self.token_file, 'rb') as token:
                    self.creds = pickle.load(token)

                # Check if credentials have the right scopes
                if self.creds and hasattr(self.creds, 'scopes'):
                    required_scopes = self.scopes
                    token_scopes = self.creds.scopes

                    # Check if any required scope is missing
                    missing_scopes = [scope for scope in required_scopes if scope not in token_scopes]
                    if missing_scopes:
                        logger.warning(f"Existing token missing required scopes: {missing_scopes}")
                        creds_valid = False
                        self.creds = None
                        # Remove invalid token
                        try:
                            os.remove(self.token_file)
                        except Exception:
                            pass

            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid or not creds_valid:
                if self.creds and getattr(self.creds, 'expired', False) and getattr(self.creds, 'refresh_token', None) and creds_valid:
                    logger.info("Refreshing expired credentials")
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"Credentials file not found: {self.credentials_file}")
                        logger.error("Please download credentials.json from Google Cloud Console")
                        return False

                    logger.info("Starting OAuth flow - browser will open for authentication")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    self.creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.creds, token)

            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail authentication successful")
            return True

        except Exception as e:
            logger.error(f"Gmail authentication failed: {str(e)}")
            # If authentication fails, try to remove token to force re-auth
            try:
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)
                    logger.info("Removed invalid token file")
            except Exception:
                pass
            return False

    def send_email(self, to_email: str, subject: str, body: str,
                   cc_emails: Optional[List[str]] = None,
                   bcc_emails: Optional[List[str]] = None,
                   is_html: bool = False) -> Dict[str, Any]:
        """
        Send an email using Gmail API

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            cc_emails: List of CC recipients (optional)
            bcc_emails: List of BCC recipients (optional)
            is_html: Whether body content is HTML (default: False)

        Returns:
            Dictionary with success status and message or error details
        """
        if not self.service:
            if not self.authenticate():
                return {
                    'success': False,
                    'error': 'Gmail authentication failed'
                }

        try:
            # Create email message
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['Subject'] = subject

            if cc_emails:
                message['Cc'] = ', '.join(cc_emails)
            if bcc_emails:
                message['Bcc'] = ', '.join(bcc_emails)

            # Add body
            if is_html:
                html_part = MIMEText(body, 'html')
                message.attach(html_part)
            else:
                text_part = MIMEText(body, 'plain')
                message.attach(text_part)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Build the request
            send_request = {
                'raw': raw_message
            }

            # Send the message
            result = self.service.users().messages().send(
                userId='me',
                body=send_request
            ).execute()

            logger.info(f"Email sent successfully. Message ID: {result.get('id')}")
            return {
                'success': True,
                'message_id': result.get('id'),
                'message': 'Email sent successfully'
            }

        except HttpError as e:
            error_msg = f"Gmail API error: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def test_connection(self) -> Dict[str, Any]:
        """Test Gmail connection and authentication"""
        try:
            if not self.authenticate():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }

            # Get user profile to test connection
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'success': True,
                'email_address': profile.get('emailAddress'),
                'messages_total': profile.get('messagesTotal'),
                'history_id': profile.get('historyId')
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Connection test failed: {str(e)}"
            }

    def revoke_credentials(self) -> bool:
        """Revoke stored credentials"""
        try:
            if os.path.exists(self.token_file):
                os.remove(self.token_file)
                logger.info("Gmail credentials revoked")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to revoke credentials: {str(e)}")
            return False

# Global Gmail instance
_gmail_client = None

def get_gmail_client() -> GmailOAuth:
    """Get or create Gmail client instance"""
    global _gmail_client
    if _gmail_client is None:
        _gmail_client = GmailOAuth()
    return _gmail_client

def send_gmail_email(to_email: str, subject: str, body: str,
                     cc_emails: Optional[List[str]] = None,
                     bcc_emails: Optional[List[str]] = None,
                     is_html: bool = False) -> Dict[str, Any]:
    """
    Convenience function to send Gmail email

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        cc_emails: List of CC recipients (optional)
        bcc_emails: List of BCC recipients (optional)
        is_html: Whether body content is HTML (default: False)

    Returns:
        Dictionary with success status and message or error details
    """
    gmail = get_gmail_client()
    return gmail.send_email(to_email, subject, body, cc_emails, bcc_emails, is_html)

def test_gmail_connection() -> Dict[str, Any]:
    """Test Gmail connection"""
    gmail = get_gmail_client()
    return gmail.test_connection()
