"""
Supabase Auth Integration for JAI Website
Handles authentication middleware and user session management
"""
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

security = HTTPBearer(auto_error=False)


class User(BaseModel):
    id: str
    email: str
    user_metadata: Dict[str, Any] = {}


class AuthResponse(BaseModel):
    user: Optional[User] = None
    session: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    user_metadata: Dict[str, Any] = {}


def verify_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a Supabase JWT token; fail closed when verification is unconfigured."""
    if not SUPABASE_URL or not SUPABASE_JWT_SECRET or not token:
        return None
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            issuer=f"{SUPABASE_URL.rstrip('/')}/auth/v1",
            options={"require": ["exp", "sub", "aud", "iss"]},
        )
        if not isinstance(payload.get("sub"), str) or not payload["sub"]:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def is_allowed_admin(payload: Optional[Dict[str, Any]], allowed_user_ids: Optional[str] = None) -> bool:
    """Return true only for Supabase subjects explicitly configured as JAI admins."""
    if not payload or not isinstance(payload.get("sub"), str):
        return False
    configured = os.environ.get("JAI_ADMIN_USER_IDS", "") if allowed_user_ids is None else allowed_user_ids
    allowed = {item.strip() for item in configured.split(",") if item.strip()}
    return bool(allowed and payload["sub"] in allowed)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """Dependency to get current authenticated user"""
    if not credentials:
        return None

    payload = verify_supabase_token(credentials.credentials)
    if not payload:
        return None

    return User(
        id=payload.get("sub", ""),
        email=payload.get("email", ""),
        user_metadata=payload.get("user_metadata", {})
    )


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Dependency that requires authentication"""
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = verify_supabase_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return User(
        id=payload.get("sub", ""),
        email=payload.get("email", ""),
        user_metadata=payload.get("user_metadata", {})
    )


class AuthMiddleware:
    """Middleware to handle auth context for all requests"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)

            # Extract token from Authorization header
            auth_header = request.headers.get("authorization", "")
            user = None

            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                payload = verify_supabase_token(token)
                if payload:
                    user = User(
                        id=payload.get("sub", ""),
                        email=payload.get("email", ""),
                        user_metadata=payload.get("user_metadata", {})
                    )

            # Store user in request state
            request.state.user = user
            request.state.authenticated = user is not None

        await self.app(scope, receive, send)


def get_supabase_js_html() -> str:
    """Generate HTML for Supabase client initialization"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return ""

    return f"""
    <!-- Supabase JS Client -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.47.10/dist/umd/supabase.min.js"></script>
    <script>
        // Initialize Supabase client
        const supabaseUrl = '{SUPABASE_URL}';
        const supabaseKey = '{SUPABASE_ANON_KEY}';
        const supabase = window.supabase.createClient(supabaseUrl, supabaseKey, {{
            auth: {{
                autoRefreshToken: true,
                persistSession: true,
                detectSessionInUrl: true
            }}
        }});
    </script>
    """
