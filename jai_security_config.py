"""
JAI Security Configuration
Security settings and environment setup for JAI
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

class SecurityConfiguration:
    """Central security configuration management"""
    
    # Security levels
    SECURITY_LEVELS = {
        'low': {
            'token_expiry_hours': 24,
            'require_encryption': False,
            'audit_logging': False,
            'scope_validation': 'basic'
        },
        'medium': {
            'token_expiry_hours': 8,
            'require_encryption': True,
            'audit_logging': True,
            'scope_validation': 'strict'
        },
        'high': {
            'token_expiry_hours': 1,
            'require_encryption': True,
            'audit_logging': True,
            'scope_validation': 'minimal',
            'rate_limiting': True,
            'content_scanning': True
        }
    }
    
    # Minimal required scopes for each service
    MINIMAL_REQUIRED_SCOPES = {
        'gmail': ['https://www.googleapis.com/auth/gmail.readonly'],
        'gmail_send': ['https://www.googleapis.com/auth/gmail.send'],
        'gmail_basic': ['https://www.googleapis.com/auth/gmail.compose'],
        'openai': [],  # No scopes needed for API key
        'groq': [],  # No scopes needed for API key
        'weather': [],  # No scopes needed for API key
        'news': [],  # No scopes needed for API key
        'nasa': [],  # No scopes needed for API key
        'math_solver': []  # No scopes needed for API key
    }
    
    # Dangerous scopes that should never be requested
    DANGEROUS_SCOPES = [
        'https://www.googleapis.com/auth/gmail.delete',
        'https://www.googleapis.com/auth/gmail.modify',
        'https://www.googleapis.com/auth/gmail.settings.basic',
        'https://mail.google.com/mail/full',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    
    # Content security patterns
    SUSPICIOUS_PATTERNS = [
        'password', 'secret', 'token', 'key', 'hack', 'exploit',
        '<script>', 'javascript:', 'data:text/html',
        'DROP TABLE', 'DELETE FROM', 'UPDATE SET',
        'exec(', 'eval(', 'system(', 'shell_exec',
        '../', '..\\', 'file://', 'http://', 'https://'
    ]
    
    # Rate limiting configuration
    RATE_LIMITS = {
        'gmail': {'requests_per_minute': 10, 'requests_per_hour': 100},
        'openai': {'requests_per_minute': 60, 'requests_per_day': 1000},
        'groq': {'requests_per_minute': 20, 'requests_per_hour': 500},
        'weather': {'requests_per_minute': 5, 'requests_per_hour': 100},
        'news': {'requests_per_minute': 10, 'requests_per_hour': 200}
    }
    
    def __init__(self):
        self.config_file = Path.home() / '.jai' / 'security_config.json'
        self.security_level = os.environ.get('JAI_SECURITY_LEVEL', 'medium')
        self.load_config()
    
    def load_config(self):
        """Load security configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.security_level = config.get('security_level', 'medium')
                    logging.info(f"Security config loaded: {self.security_level}")
        except Exception as e:
            logging.error(f"Failed to load security config: {e}")
    
    def save_config(self):
        """Save security configuration to file"""
        try:
            config = {
                'security_level': self.security_level,
                'last_updated': str(Path(__file__).stat().st_mtime),
                'version': '1.0'
            }
            
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set secure permissions
            os.chmod(self.config_file, 0o600)
            logging.info("Security configuration saved")
            
        except Exception as e:
            logging.error(f"Failed to save security config: {e}")
    
    def get_security_settings(self) -> Dict:
        """Get current security settings"""
        level_config = self.SECURITY_LEVELS.get(self.security_level, self.SECURITY_LEVELS['medium'])
        
        return {
            'security_level': self.security_level,
            'token_expiry_hours': level_config['token_expiry_hours'],
            'require_encryption': level_config['require_encryption'],
            'audit_logging': level_config['audit_logging'],
            'scope_validation': level_config['scope_validation'],
            'rate_limiting': level_config.get('rate_limiting', False),
            'content_scanning': level_config.get('content_scanning', False),
            'minimal_scopes': self.MINIMAL_REQUIRED_SCOPES,
            'dangerous_scopes': self.DANGEROUS_SCOPES,
            'suspicious_patterns': self.SUSPICIOUS_PATTERNS,
            'rate_limits': self.RATE_LIMITS
        }
    
    def validate_scopes(self, service: str, requested_scopes: List[str]) -> tuple[bool, List[str]]:
        """Validate requested scopes against security policy"""
        minimal_scopes = self.MINIMAL_REQUIRED_SCOPES.get(service, [])
        dangerous_scopes = self.DANGEROUS_SCOPES
        
        # Check for dangerous scopes
        dangerous_found = [scope for scope in requested_scopes if scope in dangerous_scopes]
        if dangerous_found:
            return False, [f"Dangerous scope not allowed: {scope}" for scope in dangerous_found]
        
        # Check if requested scopes exceed minimal required
        if not set(requested_scopes).issubset(set(minimal_scopes)):
            excess_scopes = set(requested_scopes) - set(minimal_scopes)
            return False, [f"Excessive scope: {scope}" for scope in excess_scopes]
        
        return True, []
    
    def check_content_security(self, content: str) -> tuple[bool, List[str]]:
        """Check content for security issues"""
        issues = []
        content_lower = content.lower()
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in content_lower:
                issues.append(f"Suspicious pattern detected: {pattern}")
        
        # Check for potential injection attacks
        injection_patterns = [
            'union select', 'drop table', 'insert into', 
            'exec(', 'eval(', 'system(', 'alert(',
            '<script', 'javascript:', 'vbscript:'
        ]
        
        for pattern in injection_patterns:
            if pattern in content_lower:
                issues.append(f"Potential injection: {pattern}")
        
        return len(issues) == 0, issues
    
    def get_rate_limit(self, service: str) -> Dict:
        """Get rate limit for service"""
        return self.RATE_LIMITS.get(service, {'requests_per_minute': 10})
    
    def is_encryption_required(self) -> bool:
        """Check if encryption is required"""
        level_config = self.SECURITY_LEVELS.get(self.security_level, {})
        return level_config.get('require_encryption', True)
    
    def get_token_expiry_hours(self) -> int:
        """Get token expiry time"""
        level_config = self.SECURITY_LEVELS.get(self.security_level, {})
        return level_config.get('token_expiry_hours', 8)
    
    def set_security_level(self, level: str):
        """Set security level"""
        if level in self.SECURITY_LEVELS:
            self.security_level = level
            self.save_config()
            logging.info(f"Security level set to: {level}")
        else:
            logging.error(f"Invalid security level: {level}")

# Global security configuration
security_config = SecurityConfiguration()

def initialize_security():
    """Initialize security system"""
    global security_config
    security_config = SecurityConfiguration()
    logging.info("Security configuration initialized")

def get_security_config() -> Dict:
    """Get global security configuration"""
    global security_config
    return security_config.get_security_settings()

def validate_api_scopes(service: str, requested_scopes: List[str]) -> tuple[bool, List[str]]:
    """Validate API scopes globally"""
    global security_config
    return security_config.validate_scopes(service, requested_scopes)

def check_content_security(content: str) -> tuple[bool, List[str]]:
    """Check content security globally"""
    global security_config
    return security_config.check_content_security(content)

def get_rate_limit(service: str) -> Dict:
    """Get rate limit globally"""
    global security_config
    return security_config.get_rate_limit(service)
