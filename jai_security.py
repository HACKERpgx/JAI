"""
JAI Security Manager
Secure token management and API security measures
"""

import os
import json
import base64
import hashlib
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import logging
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import datetime

class SecurityConfig:
    """Security configuration for JAI"""
    
    # Required scopes for different services
    MINIMAL_SCOPES = {
        'gmail': ['https://www.googleapis.com/auth/gmail.readonly'],
        'gmail_send': ['https://www.googleapis.com/auth/gmail.send'],
        'gmail_basic': ['https://www.googleapis.com/auth/gmail.compose'],
        'openai': [],  # No scopes needed for API key
        'groq': [],  # No scopes needed for API key
        'weather': [],  # No scopes needed for API key
        'news': [],  # No scopes needed for API key
        'nasa': []  # No scopes needed for API key
    }
    
    # Token storage
    TOKEN_DIR = Path.home() / '.jai' / 'tokens'
    CREDENTIALS_DIR = Path.home() / '.jai' / 'credentials'
    
    # Security settings
    TOKEN_EXPIRY_HOURS = 1
    MAX_RETRY_ATTEMPTS = 3
    SESSION_TIMEOUT_MINUTES = 30
    
    @classmethod
    def ensure_secure_dirs(cls):
        """Ensure secure directories exist with proper permissions"""
        try:
            cls.TOKEN_DIR.mkdir(parents=True, exist_ok=True)
            cls.CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Set restrictive permissions (owner read/write/execute only)
            os.chmod(cls.TOKEN_DIR, 0o700)
            os.chmod(cls.CREDENTIALS_DIR, 0o700)
            
            logging.info(f"Secure directories ensured: {cls.TOKEN_DIR}")
            return True
        except Exception as e:
            logging.error(f"Failed to create secure directories: {e}")
            return False

class TokenManager:
    """Secure token management with encryption"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.security_config = SecurityConfig()
        self._init_encryption()
        
        # Ensure secure storage
        self.security_config.ensure_secure_dirs()
    
    def _init_encryption(self):
        """Initialize encryption for token storage"""
        try:
            # Get or create encryption key from environment
            encryption_key = os.environ.get('JAI_ENCRYPTION_KEY')
            
            if not encryption_key:
                # Generate a new key and store it securely
                encryption_key = secrets.token_urlsafe(32)
                logging.warning("Generated new encryption key - store it securely in JAI_ENCRYPTION_KEY environment variable")
                
                # For development, show the key (REMOVE IN PRODUCTION)
                if os.environ.get('JAI_ENV') == 'development':
                    print(f"NEW ENCRYPTION KEY (save to JAI_ENCRYPTION_KEY): {encryption_key}")
            
            # Derive encryption key
            key = encryption_key.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'jai_secure_salt',  # In production, use environment-specific salt
                iterations=100000,
                backend=default_backend()
            )
            self.encryption_key = kdf.derive(key)
            self.cipher = Fernet(base64.urlsafe_b64encode(self.encryption_key))
            
        except Exception as e:
            logging.error(f"Failed to initialize encryption: {e}")
            raise SecurityError("Encryption initialization failed")
    
    def _get_token_file(self) -> Path:
        """Get secure token file path"""
        return self.security_config.TOKEN_DIR / f"{self.service_name}_token.enc"
    
    def _get_metadata_file(self) -> Path:
        """Get token metadata file path"""
        return self.security_config.TOKEN_DIR / f"{self.service_name}_metadata.json"
    
    def store_token(self, token_data: Dict, scopes: List[str] = None) -> bool:
        """Securely store encrypted token with metadata"""
        try:
            # Validate scopes
            if scopes:
                minimal_scopes = self.security_config.MINIMAL_SCOPES.get(self.service_name, [])
                if not set(scopes).issubset(set(minimal_scopes)):
                    excess_scopes = set(scopes) - set(minimal_scopes)
                    logging.warning(f"Requested scopes exceed minimum for {self.service_name}: {excess_scopes}")
                    return False
            
            # Prepare token data with metadata
            encrypted_data = {
                'token': token_data.get('access_token', ''),
                'refresh_token': token_data.get('refresh_token', ''),
                'scopes': scopes or [],
                'created_at': datetime.datetime.now().isoformat(),
                'expires_at': token_data.get('expires_at', ''),
                'service': self.service_name,
                'encrypted': True
            }
            
            # Encrypt the data
            encrypted_json = json.dumps(encrypted_data)
            encrypted_bytes = self.cipher.encrypt(encrypted_json.encode())
            
            # Store encrypted token
            token_file = self._get_token_file()
            with open(token_file, 'wb') as f:
                f.write(encrypted_bytes)
            
            # Set secure permissions
            os.chmod(token_file, 0o600)
            
            # Store metadata (unencrypted for quick access)
            metadata = {
                'service': self.service_name,
                'has_token': True,
                'created_at': datetime.datetime.now().isoformat(),
                'scopes_used': scopes or [],
                'token_file': str(token_file),
                'encrypted': True
            }
            
            metadata_file = self._get_metadata_file()
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            os.chmod(metadata_file, 0o600)
            
            logging.info(f"Token securely stored for {self.service_name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to store token for {self.service_name}: {e}")
            return False
    
    def get_token(self) -> Optional[Dict]:
        """Securely retrieve and decrypt token"""
        try:
            token_file = self._get_token_file()
            
            if not token_file.exists():
                return None
            
            # Read and decrypt token
            with open(token_file, 'rb') as f:
                encrypted_bytes = f.read()
            
            decrypted_json = self.cipher.decrypt(encrypted_bytes).decode()
            token_data = json.loads(decrypted_json)
            
            # Check if token is expired
            if self._is_token_expired(token_data):
                logging.warning(f"Token for {self.service_name} has expired")
                self.delete_token()
                return None
            
            logging.info(f"Token retrieved for {self.service_name}")
            return token_data
            
        except Exception as e:
            logging.error(f"Failed to retrieve token for {self.service_name}: {e}")
            return None
    
    def _is_token_expired(self, token_data: Dict) -> bool:
        """Check if token has expired"""
        try:
            expires_at = token_data.get('expires_at')
            if not expires_at:
                return False
            
            expiry_time = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            current_time = datetime.datetime.now()
            
            # Add buffer time
            return current_time >= expiry_time - datetime.timedelta(hours=1)
            
        except Exception:
            return True  # Assume expired if can't parse
    
    def delete_token(self) -> bool:
        """Securely delete stored token"""
        try:
            token_file = self._get_token_file()
            metadata_file = self._get_metadata_file()
            
            if token_file.exists():
                token_file.unlink()
                logging.info(f"Token file deleted for {self.service_name}")
            
            if metadata_file.exists():
                metadata_file.unlink()
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to delete token for {self.service_name}: {e}")
            return False
    
    def validate_scopes(self, requested_scopes: List[str]) -> Tuple[bool, List[str]]:
        """Validate requested scopes against minimum required"""
        minimal_scopes = self.security_config.MINIMAL_SCOPES.get(self.service_name, [])
        
        if not set(requested_scopes).issubset(set(minimal_scopes)):
            excess_scopes = set(requested_scopes) - set(minimal_scopes)
            return False, list(excess_scopes)
        
        return True, []
    
    def get_token_metadata(self) -> Optional[Dict]:
        """Get token metadata without decrypting token"""
        try:
            metadata_file = self._get_metadata_file()
            
            if not metadata_file.exists():
                return None
            
            with open(metadata_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logging.error(f"Failed to get metadata for {self.service_name}: {e}")
            return None

class APIKeyManager:
    """Secure API key management"""
    
    def __init__(self):
        self.security_config = SecurityConfig()
        self.security_config.ensure_secure_dirs()
    
    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key from environment variables"""
        # Priority: Environment variables
        env_keys = {
            'openai': ['OPENAI_API_KEY', 'GROQ_API_KEY'],
            'weather': ['OPENWEATHER_API_KEY'],
            'news': ['NEWS_API_KEY'],
            'nasa': ['NASA_API_KEY'],
            'math_solver': ['RAPIDAPI_KEY', 'MATH_SOLVER_API_KEY']
        }
        
        if service_name in env_keys:
            for key_name in env_keys[service_name]:
                key = os.environ.get(key_name)
                if key:
                    logging.info(f"API key found for {service_name}")
                    return key
        
        logging.warning(f"API key not found for {service_name}")
        return None
    
    def validate_api_key(self, service_name: str, api_key: str) -> bool:
        """Validate API key format and security"""
        if not api_key or len(api_key) < 10:
            return False
        
        # Basic format validation
        if service_name == 'openai':
            return api_key.startswith('sk-') and len(api_key) > 40
        elif service_name == 'groq':
            return len(api_key) > 30
        elif service_name in ['weather', 'news', 'nasa']:
            return len(api_key) > 15
        
        return len(api_key) > 8

class SecurityAuditor:
    """Security audit and monitoring"""
    
    def __init__(self):
        self.security_config = SecurityConfig()
        self.audit_log = []
    
    def audit_token_storage(self) -> Dict:
        """Audit token storage security"""
        audit_results = {
            'secure_directories': self._check_directory_permissions(),
            'token_encryption': self._check_token_encryption(),
            'exposed_tokens': self._check_exposed_tokens(),
            'old_tokens': self._check_old_tokens(),
            'recommendations': []
        }
        
        # Generate recommendations
        if not audit_results['secure_directories']:
            audit_results['recommendations'].append("Fix directory permissions for ~/.jai/tokens/")
        
        if not audit_results['token_encryption']:
            audit_results['recommendations'].append("Enable token encryption")
        
        if audit_results['exposed_tokens']:
            audit_results['recommendations'].append("Remove exposed tokens from code/logs")
        
        if audit_results['old_tokens']:
            audit_results['recommendations'].append("Clean up expired tokens")
        
        return audit_results
    
    def _check_directory_permissions(self) -> bool:
        """Check if secure directories have proper permissions"""
        try:
            token_dir = self.security_config.TOKEN_DIR
            if not token_dir.exists():
                return False
            
            stat_info = token_dir.stat()
            # Check if owner has read/write/execute only (0o700)
            return oct(stat_info.st_mode)[-3:] == '700'
        except Exception:
            return False
    
    def _check_token_encryption(self) -> bool:
        """Check if tokens are encrypted"""
        try:
            token_dir = self.security_config.TOKEN_DIR
            for token_file in token_dir.glob('*.enc'):
                return True
            return False
        except Exception:
            return False
    
    def _check_exposed_tokens(self) -> bool:
        """Check for exposed tokens in code"""
        # This would scan code files for hardcoded tokens
        # For now, return False (implementation would be more complex)
        return False
    
    def _check_old_tokens(self) -> bool:
        """Check for expired tokens"""
        try:
            token_dir = self.security_config.TOKEN_DIR
            current_time = datetime.datetime.now()
            
            for metadata_file in token_dir.glob('*_metadata.json'):
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                created_at = datetime.datetime.fromisoformat(metadata.get('created_at', ''))
                if current_time - created_at > datetime.timedelta(days=30):
                    return True
            
            return False
        except Exception:
            return False

class SecurityError(Exception):
    """Security-related exceptions"""
    pass

# Global security instances
token_manager = None
api_key_manager = APIKeyManager()
security_auditor = SecurityAuditor()

def initialize_security():
    """Initialize security systems"""
    global token_manager, api_key_manager, security_auditor
    
    token_manager = TokenManager("gmail")  # Default to Gmail
    api_key_manager = APIKeyManager()
    security_auditor = SecurityAuditor()
    
    logging.info("Security systems initialized")

def get_secure_token(service_name: str) -> Optional[Dict]:
    """Get secure token for service"""
    global token_manager
    if not token_manager:
        initialize_security()
    
    return token_manager.get_token()

def store_secure_token(service_name: str, token_data: Dict, scopes: List[str] = None) -> bool:
    """Store secure token for service"""
    global token_manager
    if not token_manager:
        initialize_security()
    
    return token_manager.store_token(token_data, scopes)

def get_api_key(service_name: str) -> Optional[str]:
    """Get API key securely"""
    global api_key_manager
    if not api_key_manager:
        initialize_security()
    
    return api_key_manager.get_api_key(service_name)

def run_security_audit() -> Dict:
    """Run security audit"""
    global security_auditor
    if not security_auditor:
        initialize_security()
    
    return security_auditor.audit_token_storage()

def validate_api_scopes(service_name: str, requested_scopes: List[str]) -> Tuple[bool, List[str]]:
    """Validate API scopes"""
    global token_manager
    if not token_manager:
        initialize_security()
    
    return token_manager.validate_scopes(requested_scopes)

# Environment variable setup
def setup_security_environment():
    """Setup secure environment variables"""
    security_env = {
        'JAI_ENCRYPTION_KEY': os.environ.get('JAI_ENCRYPTION_KEY'),
        'JAI_TOKEN_DIR': str(SecurityConfig.TOKEN_DIR),
        'JAI_CREDENTIALS_DIR': str(SecurityConfig.CREDENTIALS_DIR),
        'JAI_SECURITY_LEVEL': 'high'
    }
    
    for key, value in security_env.items():
        if value:
            os.environ[key] = value
    
    logging.info("Security environment configured")
