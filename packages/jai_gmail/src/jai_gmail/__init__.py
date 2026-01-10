"""
JAI Gmail: Secure OAuth authentication and email sending helpers using Gmail API.
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

# Import security manager
try:
    from jai_security import get_secure_token, store_secure_token, validate_api_scopes, SecurityConfig
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

__all__ = [
    "GmailOAuth",
    "send_gmail_email",
    "test_gmail_connection",
]

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

class GmailOAuth:
    """Handles secure Gmail OAuth authentication and email sending"""

    def __init__(self, credentials_file: str = 'credentials.json', token_service: str = 'gmail'):
        self.credentials_file = credentials_file
        self.token_service = token_service
        # Use minimal required scopes for security
        self.scopes = SecurityConfig.MINIMAL_SCOPES.get('gmail', [
            'https://www.googleapis.com/auth/gmail.send'
        ])
        self.service = None
        self.creds = None
        
        if not GOOGLE_APIS_AVAILABLE:
            raise ImportError("Google APIs not available. Install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        
        if not SECURITY_AVAILABLE:
            logger.warning("Security manager not available - using insecure token storage")
            self.use_secure_storage = False
        else:
            self.use_secure_storage = True

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail using secure OAuth 2.0 flow
        Returns True if authentication successful, False otherwise
        """
        try:
            # Try to get existing secure token
            if self.use_secure_storage:
                self.creds = get_secure_token(self.token_service)
            else:
                self.creds = self._get_legacy_token()
            
            # Validate token scopes
            if self.creds:
                is_valid, excess_scopes = validate_api_scopes('gmail', self.scopes)
                if not is_valid:
                    logger.warning(f"Token has excessive scopes: {excess_scopes}")
                    self.creds = None
            
            # Check if credentials are valid and not expired
            creds_valid = True
            if self.creds and hasattr(self.creds, 'scopes'):
                required_scopes = set(self.scopes)
                token_scopes = set(self.creds.scopes)
                missing_scopes = required_scopes - token_scopes
                if missing_scopes:
                    logger.warning(f"Existing token missing required scopes: {missing_scopes}")
                    creds_valid = False
            
            if self.creds and hasattr(self.creds, 'expired') and getattr(self.creds, 'expired', False):
                logger.warning("Token has expired")
                creds_valid = False
            
            # If we have valid credentials, use them
            if self.creds and creds_valid:
                logger.info("Using existing valid credentials")
                self.service = build('gmail', 'v1', credentials=self.creds)
                return True
            
            # If no valid credentials, start OAuth flow
            logger.info("Starting secure OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, 
                scopes=self.scopes,
                redirect_uri='http://localhost:8080/oauth/callback'
            )
            
            self.creds = flow.run_local_server(port=0)
            
            # Store credentials securely
            if self.creds:
                if self.use_secure_storage:
                    token_data = {
                        'access_token': self.creds.token,
                        'refresh_token': self.creds.refresh_token,
                        'scopes': self.scopes,
                        'expires_at': self.creds.expiry.isoformat() if self.creds.expiry else None
                    }
                    store_secure_token(self.token_service, token_data, self.scopes)
                else:
                    self._store_legacy_token()
                
                # Build Gmail service
                self.service = build('gmail', 'v1', credentials=self.creds)
                logger.info("Gmail authentication successful")
                return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {str(e)}")
            # If authentication fails, try to remove invalid token
            try:
                if self.use_secure_storage:
                    from jai_security import TokenManager
                    token_manager = TokenManager(self.token_service)
                    token_manager.delete_token()
                else:
                    self._delete_legacy_token()
            except Exception:
                pass
            return False
    
    def _get_legacy_token(self):
        """Get legacy unencrypted token (for migration)"""
        try:
            token_file = self.credentials_file.replace('.json', '_token.pickle')
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    return pickle.load(token)
        except Exception:
            return None
    
    def _store_legacy_token(self):
        """Store legacy unencrypted token (deprecated)"""
        try:
            token_file = self.credentials_file.replace('.json', '_token.pickle')
            with open(token_file, 'wb') as token:
                pickle.dump(self.creds, token)
            logger.warning("Using legacy unencrypted token storage - migrate to secure storage")
        except Exception as e:
            logger.error(f"Failed to store legacy token: {e}")
    
    def _delete_legacy_token(self):
        """Delete legacy unencrypted token"""
        try:
            token_file = self.credentials_file.replace('.json', '_token.pickle')
            if os.path.exists(token_file):
                os.remove(token_file)
                logger.info("Removed legacy token file")
        except Exception:
            pass

    def send_email(self, to_email: str, subject: str, body: str,
                   cc_emails: Optional[List[str]] = None,
                   bcc_emails: Optional[List[str]] = None,
                   is_html: bool = False) -> Dict[str, Any]:
        """
        Send an email using Gmail API with security validation
        
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
            # Validate email parameters
            if not self._validate_email_params(to_email, subject, body):
                return {
                    'success': False,
                    'error': 'Invalid email parameters'
                }
            
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
            
            # Build send request
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
    
    def _validate_email_params(self, to_email: str, subject: str, body: str) -> bool:
        """Validate email sending parameters for security"""
        # Basic email validation
        if not to_email or '@' not in to_email:
            return False
        
        if not subject or len(subject.strip()) == 0:
            return False
        
        if not body or len(body.strip()) == 0:
            return False
        
        # Check for suspicious content
        suspicious_patterns = [
            'password', 'secret', 'token', 'key', 'hack', 'exploit',
            '<script>', 'javascript:', 'data:text/html'
        ]
        
        content_lower = (subject + ' ' + body).lower()
        for pattern in suspicious_patterns:
            if pattern in content_lower:
                logger.warning(f"Suspicious content detected in email: {pattern}")
                return False
        
        return True
    
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
                'history_id': profile.get('historyId'),
                'storage_type': 'secure' if self.use_secure_storage else 'legacy'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Connection test failed: {str(e)}"
            }
    
    def revoke_credentials(self) -> bool:
        """Revoke stored credentials securely"""
        try:
            if self.use_secure_storage:
                from jai_security import TokenManager
                token_manager = TokenManager(self.token_service)
                success = token_manager.delete_token()
            else:
                success = self._delete_legacy_token()
            
            if success:
                self.creds = None
                self.service = None
                logger.info("Gmail credentials revoked")
            
            return success
            
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
    """
    gmail = get_gmail_client()
    return gmail.send_email(to_email, subject, body, cc_emails, bcc_emails, is_html)

def test_gmail_connection() -> Dict[str, Any]:
    """Test Gmail connection"""
    gmail = get_gmail_client()
    return gmail.test_connection()
