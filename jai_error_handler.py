"""
JAI Advanced Error Handling and Recovery System
Provides intelligent error handling, recovery strategies, and retry mechanisms
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import traceback
import functools

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    RESOURCE = "resource"
    SYNTAX = "syntax"
    LOGIC = "logic"
    EXTERNAL_SERVICE = "external_service"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """Detailed error information"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    original_exception: Exception
    timestamp: datetime
    context: Dict[str, Any]
    retry_count: int = 0
    can_retry: bool = True
    recovery_suggestions: List[str] = None

class RecoveryStrategy:
    """Base class for error recovery strategies"""
    
    def __init__(self, name: str):
        self.name = name
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> bool:
        """Attempt to recover from error"""
        raise NotImplementedError

class RetryStrategy(RecoveryStrategy):
    """Retry with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        super().__init__("exponential_backoff")
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> bool:
        """Retry with exponential backoff"""
        if error_info.retry_count >= self.max_retries:
            return False
        
        delay = min(self.base_delay * (2 ** error_info.retry_count), self.max_delay)
        await asyncio.sleep(delay)
        return True

class RefreshTokenStrategy(RecoveryStrategy):
    """Refresh authentication tokens"""
    
    def __init__(self):
        super().__init__("refresh_token")
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> bool:
        """Attempt to refresh authentication token"""
        try:
            # This would integrate with actual auth system
            if error_info.category == ErrorCategory.AUTHENTICATION:
                # Placeholder for token refresh logic
                logging.info("Attempting to refresh authentication token")
                # In real implementation, this would refresh OAuth tokens, API keys, etc.
                return True
        except Exception as e:
            logging.error(f"Token refresh failed: {e}")
        return False

class FallbackServiceStrategy(RecoveryStrategy):
    """Switch to fallback service"""
    
    def __init__(self, fallback_services: Dict[str, str]):
        super().__init__("fallback_service")
        self.fallback_services = fallback_services
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> bool:
        """Switch to fallback service"""
        service_name = context.get('service')
        if service_name and service_name in self.fallback_services:
            logging.info(f"Switching to fallback service for {service_name}")
            context['service'] = self.fallback_services[service_name]
            return True
        return False

class ResourceCleanupStrategy(RecoveryStrategy):
    """Clean up resources and retry"""
    
    def __init__(self):
        super().__init__("resource_cleanup")
    
    async def recover(self, error_info: ErrorInfo, context: Dict[str, Any]) -> bool:
        """Clean up resources and retry"""
        try:
            # Clean up temporary files, connections, etc.
            if error_info.category == ErrorCategory.RESOURCE:
                logging.info("Performing resource cleanup")
                # Placeholder for cleanup logic
                return True
        except Exception as e:
            logging.error(f"Resource cleanup failed: {e}")
        return False

class IntelligentErrorHandler:
    """Intelligent error handling system"""
    
    def __init__(self):
        self.logger = logging.getLogger('JAIErrorHandler')
        self.error_patterns = {
            ErrorCategory.NETWORK: [
                'connection', 'network', 'timeout', 'unreachable', 'dns', 'socket'
            ],
            ErrorCategory.AUTHENTICATION: [
                'unauthorized', 'authentication', 'login', 'credentials', 'token', '401'
            ],
            ErrorCategory.PERMISSION: [
                'permission', 'forbidden', 'access denied', '403', 'unauthorized'
            ],
            ErrorCategory.RESOURCE: [
                'memory', 'disk', 'space', 'quota', 'limit', 'resource'
            ],
            ErrorCategory.SYNTAX: [
                'syntax', 'parse', 'invalid', 'malformed', 'format'
            ],
            ErrorCategory.LOGIC: [
                'logic', 'validation', 'constraint', 'conflict'
            ],
            ErrorCategory.EXTERNAL_SERVICE: [
                'api', 'service', 'external', 'third party', 'dependency'
            ],
            ErrorCategory.TIMEOUT: [
                'timeout', 'timed out', 'deadline', 'slow'
            ]
        }
        
        self.recovery_strategies = {
            ErrorCategory.NETWORK: [RetryStrategy(max_retries=3), FallbackServiceStrategy({})],
            ErrorCategory.AUTHENTICATION: [RefreshTokenStrategy(), RetryStrategy(max_retries=2)],
            ErrorCategory.PERMISSION: [RetryStrategy(max_retries=1)],
            ErrorCategory.RESOURCE: [ResourceCleanupStrategy(), RetryStrategy(max_retries=2)],
            ErrorCategory.SYNTAX: [RetryStrategy(max_retries=1)],
            ErrorCategory.LOGIC: [RetryStrategy(max_retries=1)],
            ErrorCategory.EXTERNAL_SERVICE: [FallbackServiceStrategy({}), RetryStrategy(max_retries=3)],
            ErrorCategory.TIMEOUT: [RetryStrategy(max_retries=2, base_delay=2.0)]
        }
        
        self.error_history: List[ErrorInfo] = []
        self.recovery_stats = {}
    
    def categorize_error(self, exception: Exception, message: str) -> ErrorCategory:
        """Categorize error based on exception and message"""
        message_lower = message.lower()
        exception_str = str(exception).lower()
        combined_text = f"{message_lower} {exception_str}"
        
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if pattern in combined_text:
                    return category
        
        return ErrorCategory.UNKNOWN
    
    def determine_severity(self, category: ErrorCategory, exception: Exception) -> ErrorSeverity:
        """Determine error severity"""
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.PERMISSION]:
            return ErrorSeverity.HIGH
        elif category == ErrorCategory.RESOURCE:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.NETWORK:
            return ErrorSeverity.MEDIUM
        elif category == ErrorCategory.CRITICAL:
            return ErrorSeverity.CRITICAL
        else:
            return ErrorSeverity.LOW
    
    def generate_recovery_suggestions(self, error_info: ErrorInfo) -> List[str]:
        """Generate recovery suggestions based on error type"""
        suggestions = []
        
        if error_info.category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Check internet connection",
                "Verify service availability",
                "Try again in a few moments"
            ])
        elif error_info.category == ErrorCategory.AUTHENTICATION:
            suggestions.extend([
                "Refresh authentication tokens",
                "Verify credentials",
                "Check API key validity"
            ])
        elif error_info.category == ErrorCategory.PERMISSION:
            suggestions.extend([
                "Check user permissions",
                "Verify access rights",
                "Contact administrator"
            ])
        elif error_info.category == ErrorCategory.RESOURCE:
            suggestions.extend([
                "Free up system resources",
                "Check disk space",
                "Close unused applications"
            ])
        elif error_info.category == ErrorCategory.TIMEOUT:
            suggestions.extend([
                "Increase timeout duration",
                "Check network stability",
                "Try with smaller data"
            ])
        
        return suggestions
    
    async def handle_error(self, exception: Exception, context: Dict[str, Any] = None) -> ErrorInfo:
        """Handle error with intelligent recovery"""
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(exception)}"
        message = str(exception)
        
        # Categorize and determine severity
        category = self.categorize_error(exception, message)
        severity = self.determine_severity(category, exception)
        
        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            category=category,
            severity=severity,
            message=message,
            original_exception=exception,
            timestamp=datetime.now(),
            context=context or {},
            recovery_suggestions=self.generate_recovery_suggestions(error_info)
        )
        
        self.logger.error(f"Error {error_id}: {message} (Category: {category.value}, Severity: {severity.value})")
        
        # Store error
        self.error_history.append(error_info)
        
        return error_info
    
    async def attempt_recovery(self, error_info: ErrorInfo, context: Dict[str, Any]) -> bool:
        """Attempt to recover from error"""
        strategies = self.recovery_strategies.get(error_info.category, [])
        
        for strategy in strategies:
            try:
                self.logger.info(f"Attempting recovery strategy: {strategy.name}")
                success = await strategy.recover(error_info, context)
                
                if success:
                    self.logger.info(f"Recovery successful using {strategy.name}")
                    self._update_recovery_stats(strategy.name, True)
                    return True
                else:
                    self.logger.warning(f"Recovery failed using {strategy.name}")
                    self._update_recovery_stats(strategy.name, False)
                    
            except Exception as e:
                self.logger.error(f"Recovery strategy {strategy.name} failed: {e}")
                self._update_recovery_stats(strategy.name, False)
        
        return False
    
    def _update_recovery_stats(self, strategy_name: str, success: bool):
        """Update recovery statistics"""
        if strategy_name not in self.recovery_stats:
            self.recovery_stats[strategy_name] = {'attempts': 0, 'successes': 0}
        
        self.recovery_stats[strategy_name]['attempts'] += 1
        if success:
            self.recovery_stats[strategy_name]['successes'] += 1
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        total_errors = len(self.error_history)
        category_counts = {}
        severity_counts = {}
        
        for error in self.error_history:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
        
        return {
            'total_errors': total_errors,
            'by_category': category_counts,
            'by_severity': severity_counts,
            'recovery_stats': self.recovery_stats,
            'recent_errors': [
                {
                    'error_id': error.error_id,
                    'category': error.category.value,
                    'severity': error.severity.value,
                    'message': error.message,
                    'timestamp': error.timestamp.isoformat()
                }
                for error in self.error_history[-10:]
            ]
        }

def autonomous_error_handler(max_retries: int = 3, fallback_result: Any = None):
    """Decorator for autonomous error handling"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            error_handler = IntelligentErrorHandler()
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    context = {
                        'function': func.__name__,
                        'attempt': attempt + 1,
                        'args': str(args)[:100],  # Limit length
                        'kwargs': str(kwargs)[:100]
                    }
                    
                    error_info = await error_handler.handle_error(e, context)
                    
                    if attempt < max_retries:
                        recovery_success = await error_handler.attempt_recovery(error_info, context)
                        if recovery_success:
                            error_info.retry_count += 1
                            continue
                    else:
                        logging.error(f"All recovery attempts failed for {func.__name__}")
                        if fallback_result is not None:
                            return fallback_result
                        raise
            
            return fallback_result
        return wrapper
    return decorator

# Global error handler instance
error_handler = IntelligentErrorHandler()
