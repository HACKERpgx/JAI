from fastapi import APIRouter, Depends, Request, Response, HTTPException
from pydantic import BaseModel, constr
from typing import Optional
import secrets
import pathlib
try:
    from dotenv import load_dotenv
    _ROOT = pathlib.Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=_ROOT / '.env')
except Exception:
    pass

from security.auth_core import AuthConfig, AuthDB, AuthService, SessionManager, get_client_ip

cfg = AuthConfig()
db = AuthDB(cfg)
auth = AuthService(db, cfg)
sessions = SessionManager(db, cfg)
router = APIRouter(prefix="/auth", tags=["auth"])


class SetupBody(BaseModel):
    username: constr(min_length=3)
    password: Optional[constr(min_length=8)] = None
    pin: Optional[constr(min_length=cfg.pin_len, max_length=cfg.pin_len)] = None


class LoginBody(BaseModel):
    username: constr(min_length=3)
    password: Optional[str] = None
    pin: Optional[str] = None


class MfaVerifyBody(BaseModel):
    pending_token: str
    code: Optional[str] = None
    recovery_code: Optional[str] = None


@router.post("/setup")
def setup(b: SetupBody, request: Request):
    if b.password and len(b.password) < cfg.password_min_len:
        raise HTTPException(400, "password_too_short")
    if b.pin and len(b.pin) != cfg.pin_len:
        raise HTTPException(400, "invalid_pin_length")
    try:
        uid = auth.create_initial_user(b.username, b.password, b.pin)
    except ValueError:
        raise HTTPException(400, "already_initialized")
    return {"ok": True, "user_id": uid}


@router.post("/login")
def login(b: LoginBody, request: Request, response: Response):
    if not b.password and not b.pin:
        raise HTTPException(400, "missing_secret")
    ip = get_client_ip(request.headers, request.client.host if request.client else None)
    req_id = request.headers.get("x-request-id", secrets.token_urlsafe(8))
    use_pin = b.pin is not None
    secret = b.pin if use_pin else b.password
    uid, pending, status = auth.begin_password_or_pin_login(b.username, secret, use_pin, ip, req_id)
    if status == "rate_limited":
        raise HTTPException(429, "rate_limited")
    if status == "locked":
        raise HTTPException(423, "account_locked")
    if status == "invalid" or uid is None:
        raise HTTPException(401, "invalid_credentials")
    if status == "mfa_required":
        return {"mfa_required": True, "pending_token": pending}
    sid = sessions.create(uid, mfa_verified=True)
    response.set_cookie(
        cfg.session_cookie_name,
        sid,
        httponly=True,
        secure=cfg.session_secure_cookies,
        samesite="lax",
        max_age=cfg.session_absolute_timeout,
    )
    return {"mfa_required": False, "session_id": sid}


@router.post("/mfa/verify")
def mfa_verify(b: MfaVerifyBody, request: Request, response: Response):
    req_id = request.headers.get("x-request-id", secrets.token_urlsafe(8))
    uid = auth.verify_mfa(b.pending_token, b.code, b.recovery_code, req_id)
    if not uid:
        raise HTTPException(401, "mfa_invalid")
    sid = sessions.create(uid, mfa_verified=True)
    response.set_cookie(
        cfg.session_cookie_name,
        sid,
        httponly=True,
        secure=cfg.session_secure_cookies,
        samesite="lax",
        max_age=cfg.session_absolute_timeout,
    )
    return {"ok": True, "session_id": sid}


@router.post("/logout")
def logout(request: Request, response: Response):
    sid = request.cookies.get(cfg.session_cookie_name) or request.headers.get("authorization", "").removeprefix("Session ").strip()
    if sid:
        sessions.revoke(sid)
        response.delete_cookie(cfg.session_cookie_name)
    return {"ok": True}


def get_session_id(request: Request) -> Optional[str]:
    # Prefer explicit header to avoid clobbering Bearer token used elsewhere
    h = request.headers.get("x-session-id")
    if h:
        return h.strip()
    sid = request.cookies.get(cfg.session_cookie_name)
    if sid:
        return sid
    header = request.headers.get("authorization", "")
    if header.startswith("Session "):
        return header.removeprefix("Session ").strip()
    return None


def require_auth(request: Request) -> dict:
    sid = get_session_id(request)
    if not sid:
        raise HTTPException(401, "not_authenticated")
    s = sessions.require(sid, require_mfa=False)
    if not s:
        raise HTTPException(401, "session_invalid_or_expired")
    return {"session": s}


def require_sensitive(request: Request) -> dict:
    sid = get_session_id(request)
    if not sid:
        raise HTTPException(401, "not_authenticated")
    s = sessions.require(sid, require_mfa=True)
    if not s:
        raise HTTPException(401, "mfa_required_or_session_invalid")
    return {"session": s}


@router.get("/me")
def me(ctx: dict = Depends(require_auth)):
    s = ctx["session"]
    u = db.query_one("SELECT id, username, is_mfa_enabled FROM users WHERE id=?", (s["user_id"],))
    if not u:
        raise HTTPException(404, "user_not_found")
    return {"id": u["id"], "username": u["username"], "mfa_enabled": bool(u["is_mfa_enabled"]) }


@router.post("/mfa/enable")
def mfa_enable(ctx: dict = Depends(require_auth)):
    s = ctx["session"]
    u = db.query_one("SELECT username FROM users WHERE id=?", (s["user_id"],))
    if not u:
        raise HTTPException(404, "user_not_found")
    secret, uri = auth.enable_mfa(u["username"])
    return {"secret": secret, "otpauth_uri": uri}


@router.post("/mfa/disable")
def mfa_disable(ctx: dict = Depends(require_sensitive)):
    s = ctx["session"]
    db.execute("UPDATE users SET is_mfa_enabled=0, totp_secret=NULL WHERE id=?", (s["user_id"],))
    return {"ok": True}


@router.post("/recovery-codes/regenerate")
def regen_recovery_codes(ctx: dict = Depends(require_sensitive)):
    s = ctx["session"]
    u = db.query_one("SELECT username FROM users WHERE id=?", (s["user_id"],))
    if not u:
        raise HTTPException(404, "user_not_found")
    codes = auth.generate_recovery_codes(u["username"], cfg.recovery_code_count)
    return {"codes": codes}
