"""
JAI External Integration Agent System
Provides integration capabilities with external services, APIs, and platforms
for extending JAI's autonomous capabilities.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import hashlib
import hmac
from urllib.parse import urlencode, urlparse
import base64

class IntegrationType(Enum):
    WEBHOOK = "webhook"
    REST_API = "rest_api"
    WEBSOCKET = "websocket"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"

class AuthType(Enum):
    NONE = "none"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC_AUTH = "basic_auth"
    BEARER_TOKEN = "bearer_token"
    CUSTOM = "custom"

@dataclass
class IntegrationConfig:
    """Configuration for external integration"""
    integration_id: str
    name: str
    type: IntegrationType
    auth_type: AuthType
    endpoint: str
    auth_data: Dict[str, Any]
    headers: Dict[str, str]
    enabled: bool = True
    rate_limit: int = 100  # requests per minute
    timeout: int = 30
    retry_count: int = 3
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class IntegrationEvent:
    """Event from external integration"""
    event_id: str
    integration_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: datetime
    processed: bool = False
    error: Optional[str] = None

@dataclass
class IntegrationAction:
    """Action to be executed by integration"""
    action_id: str
    integration_id: str
    action_type: str
    parameters: Dict[str, Any]
    target_endpoint: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class AuthenticationManager:
    """Manages authentication for external integrations"""
    
    @staticmethod
    def apply_auth(config: IntegrationConfig, session: aiohttp.ClientSession) -> Dict[str, str]:
        """Apply authentication to request headers"""
        headers = config.headers.copy()
        
        if config.auth_type == AuthType.API_KEY:
            key_name = config.auth_data.get('key_name', 'X-API-Key')
            headers[key_name] = config.auth_data.get('api_key')
        
        elif config.auth_type == AuthType.BEARER_TOKEN:
            headers['Authorization'] = f"Bearer {config.auth_data.get('token')}"
        
        elif config.auth_type == AuthType.BASIC_AUTH:
            credentials = base64.b64encode(
                f"{config.auth_data.get('username')}:{config.auth_data.get('password')}".encode()
            ).decode()
            headers['Authorization'] = f"Basic {credentials}"
        
        elif config.auth_type == AuthType.OAUTH2:
            # OAuth2 token management would go here
            headers['Authorization'] = f"Bearer {config.auth_data.get('access_token')}"
        
        elif config.auth_type == AuthType.CUSTOM:
            # Custom authentication logic
            custom_headers = config.auth_data.get('headers', {})
            headers.update(custom_headers)
        
        return headers

class WebhookIntegration:
    """Handles webhook integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.logger = logging.getLogger(f'WebhookIntegration-{config.integration_id}')
    
    async def send_webhook(self, data: Dict[str, Any]) -> bool:
        """Send webhook notification"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = AuthenticationManager.apply_auth(self.config, session)
                
                async with session.post(
                    self.config.endpoint,
                    json=data,
                    headers=headers
                ) as response:
                    if response.status < 400:
                        self.logger.info(f"Webhook sent successfully: {response.status}")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Webhook failed: {response.status} - {error_text}")
                        return False
        
        except Exception as e:
            self.logger.error(f"Webhook error: {e}")
            return False
    
    async def verify_webhook(self, payload: str, signature: str, secret: str) -> bool:
        """Verify incoming webhook signature"""
        try:
            expected_signature = hmac.new(
                secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception as e:
            self.logger.error(f"Webhook verification error: {e}")
            return False

class RestAPIIntegration:
    """Handles REST API integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.logger = logging.getLogger(f'RestAPIIntegration-{config.integration_id}')
        self.rate_limiter = RateLimiter(config.rate_limit)
    
    async def make_request(self, method: str, endpoint: str = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make REST API request"""
        if not await self.rate_limiter.acquire():
            raise Exception("Rate limit exceeded")
        
        try:
            url = endpoint or self.config.endpoint
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = AuthenticationManager.apply_auth(self.config, session)
                
                async with session.request(
                    method.upper(),
                    url,
                    json=data if method.upper() in ['POST', 'PUT', 'PATCH'] else None,
                    headers=headers
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    if response.status < 400:
                        self.logger.info(f"API request successful: {method} {url}")
                        return {
                            'success': True,
                            'status': response.status,
                            'data': response_data
                        }
                    else:
                        self.logger.error(f"API request failed: {response.status}")
                        return {
                            'success': False,
                            'status': response.status,
                            'error': response_data
                        }
        
        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class WebSocketIntegration:
    """Handles WebSocket integrations"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.logger = logging.getLogger(f'WebSocketIntegration-{config.integration_id}')
        self.websocket = None
        self.connected = False
    
    async def connect(self):
        """Connect to WebSocket"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = AuthenticationManager.apply_auth(self.config, session)
                
                self.websocket = await session.ws_connect(
                    self.config.endpoint,
                    headers=headers
                )
                self.connected = True
                self.logger.info("WebSocket connected")
                
                # Start listening for messages
                await self.listen()
        
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
            self.connected = False
    
    async def listen(self):
        """Listen for WebSocket messages"""
        try:
            async for message in self.websocket:
                if message.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(message.data)
                    await self.handle_message(data)
                elif message.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {message.data}")
                    break
        
        except Exception as e:
            self.logger.error(f"WebSocket listening error: {e}")
        finally:
            self.connected = False
    
    async def handle_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket message"""
        # This would integrate with the autonomous system
        event = IntegrationEvent(
            event_id=f"ws_{datetime.now().timestamp()}",
            integration_id=self.config.integration_id,
            event_type=data.get('type', 'message'),
            data=data,
            timestamp=datetime.now()
        )
        
        # Process event through autonomous system
        await self.process_event(event)
    
    async def send_message(self, data: Dict[str, Any]):
        """Send message through WebSocket"""
        if self.connected and self.websocket:
            try:
                await self.websocket.send_json(data)
            except Exception as e:
                self.logger.error(f"WebSocket send error: {e}")
    
    async def process_event(self, event: IntegrationEvent):
        """Process WebSocket event"""
        # Integration with autonomous system would go here
        self.logger.info(f"Processing event: {event.event_type}")
        pass

class RateLimiter:
    """Simple rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []
    
    async def acquire(self) -> bool:
        """Check if request is allowed"""
        now = datetime.now()
        
        # Remove old requests (older than 1 minute)
        self.requests = [req_time for req_time in self.requests if now - req_time < timedelta(minutes=1)]
        
        # Check if under limit
        if len(self.requests) < self.requests_per_minute:
            self.requests.append(now)
            return True
        
        return False

class IntegrationAgent:
    """Main integration agent managing all external integrations"""
    
    def __init__(self):
        self.logger = logging.getLogger('IntegrationAgent')
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.webhooks: Dict[str, WebhookIntegration] = {}
        self.rest_apis: Dict[str, RestAPIIntegration] = {}
        self.websockets: Dict[str, WebSocketIntegration] = {}
        self.events: List[IntegrationEvent] = []
        self.actions: List[IntegrationAction] = []
        
        # Load integrations from file
        self.load_integrations()
    
    def load_integrations(self):
        """Load integrations from configuration file"""
        try:
            config_file = "jai_integrations.json"
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    
                for integration_data in data.get('integrations', []):
                    config = IntegrationConfig(**integration_data)
                    self.integrations[config.integration_id] = config
                    
                    # Create appropriate integration handler
                    if config.type == IntegrationType.WEBHOOK:
                        self.webhooks[config.integration_id] = WebhookIntegration(config)
                    elif config.type == IntegrationType.REST_API:
                        self.rest_apis[config.integration_id] = RestAPIIntegration(config)
                    elif config.type == IntegrationType.WEBSOCKET:
                        self.websockets[config.integration_id] = WebSocketIntegration(config)
                
                self.logger.info(f"Loaded {len(self.integrations)} integrations")
        
        except Exception as e:
            self.logger.error(f"Error loading integrations: {e}")
    
    def save_integrations(self):
        """Save integrations to configuration file"""
        try:
            data = {
                'integrations': [asdict(config) for config in self.integrations.values()]
            }
            
            with open("jai_integrations.json", 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info("Integrations saved successfully")
        
        except Exception as e:
            self.logger.error(f"Error saving integrations: {e}")
    
    def add_integration(self, config: IntegrationConfig) -> bool:
        """Add new integration"""
        try:
            self.integrations[config.integration_id] = config
            
            # Create appropriate handler
            if config.type == IntegrationType.WEBHOOK:
                self.webhooks[config.integration_id] = WebhookIntegration(config)
            elif config.type == IntegrationType.REST_API:
                self.rest_apis[config.integration_id] = RestAPIIntegration(config)
            elif config.type == IntegrationType.WEBSOCKET:
                self.websockets[config.integration_id] = WebSocketIntegration(config)
            
            self.save_integrations()
            self.logger.info(f"Added integration: {config.name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error adding integration: {e}")
            return False
    
    def remove_integration(self, integration_id: str) -> bool:
        """Remove integration"""
        try:
            if integration_id in self.integrations:
                del self.integrations[integration_id]
            
            if integration_id in self.webhooks:
                del self.webhooks[integration_id]
            
            if integration_id in self.rest_apis:
                del self.rest_apis[integration_id]
            
            if integration_id in self.websockets:
                # Disconnect WebSocket if connected
                ws = self.websockets[integration_id]
                if ws.connected:
                    # WebSocket disconnection logic would go here
                    pass
                del self.websockets[integration_id]
            
            self.save_integrations()
            self.logger.info(f"Removed integration: {integration_id}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error removing integration: {e}")
            return False
    
    async def send_webhook(self, integration_id: str, data: Dict[str, Any]) -> bool:
        """Send webhook through specified integration"""
        if integration_id not in self.webhooks:
            self.logger.error(f"Webhook integration not found: {integration_id}")
            return False
        
        return await self.webhooks[integration_id].send_webhook(data)
    
    async def make_api_request(self, integration_id: str, method: str, endpoint: str = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request through specified integration"""
        if integration_id not in self.rest_apis:
            return {'success': False, 'error': f'API integration not found: {integration_id}'}
        
        return await self.rest_apis[integration_id].make_request(method, endpoint, data)
    
    async def connect_websocket(self, integration_id: str) -> bool:
        """Connect to WebSocket integration"""
        if integration_id not in self.websockets:
            self.logger.error(f"WebSocket integration not found: {integration_id}")
            return False
        
        try:
            await self.websockets[integration_id].connect()
            return True
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
            return False
    
    async def process_autonomous_action(self, action: IntegrationAction) -> bool:
        """Process action from autonomous system"""
        try:
            integration = self.integrations.get(action.integration_id)
            if not integration:
                self.logger.error(f"Integration not found: {action.integration_id}")
                return False
            
            if integration.type == IntegrationType.WEBHOOK:
                return await self.send_webhook(action.integration_id, action.parameters)
            
            elif integration.type == IntegrationType.REST_API:
                method = action.action_type.upper()
                result = await self.make_api_request(
                    action.integration_id,
                    method,
                    action.target_endpoint,
                    action.parameters
                )
                return result.get('success', False)
            
            elif integration.type == IntegrationType.WEBSOCKET:
                if action.integration_id in self.websockets:
                    await self.websockets[action.integration_id].send_message(action.parameters)
                    return True
            
            return False
        
        except Exception as e:
            self.logger.error(f"Error processing autonomous action: {e}")
            return False
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations"""
        status = {
            'total_integrations': len(self.integrations),
            'enabled_integrations': len([i for i in self.integrations.values() if i.enabled]),
            'by_type': {
                'webhooks': len(self.webhooks),
                'rest_apis': len(self.rest_apis),
                'websockets': len(self.websockets)
            },
            'integrations': []
        }
        
        for integration_id, config in self.integrations.items():
            integration_status = {
                'id': integration_id,
                'name': config.name,
                'type': config.type.value,
                'enabled': config.enabled,
                'endpoint': config.endpoint,
                'auth_type': config.auth_type.value
            }
            
            # Add WebSocket connection status
            if integration_id in self.websockets:
                integration_status['connected'] = self.websockets[integration_id].connected
            
            status['integrations'].append(integration_status)
        
        return status
    
    async def start_all_websockets(self):
        """Start all WebSocket connections"""
        for integration_id, ws in self.websockets.items():
            if self.integrations[integration_id].enabled:
                try:
                    await self.connect_websocket(integration_id)
                except Exception as e:
                    self.logger.error(f"Failed to connect WebSocket {integration_id}: {e}")

# Global integration agent instance
integration_agent = IntegrationAgent()
