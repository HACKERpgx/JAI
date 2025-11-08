import os
import sqlite3
import time
import secrets
import logging
from typing import Optional, Tuple, Dict, List

import bcrypt
import pyotp
from cryptography.fernet import Fernet
from itsdangerous import URLSafeSerializer, BadSignature


def _now() -> int:
    return int(time.time())


logger = logging.getLogger("jai.auth")


class AuthConfig:
    def __init__(self) -> None:
        self.secret_key = os.getenv("JAI_SECRET_KEY", "dev_secret_change_me")
        self.db_path = os.getenv("AUTH_DB_PATH", "./.secure/auth.db")
        self.bcrypt_rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))
        self.password_min_len = int(os.getenv("PASSWORD_MIN_LEN", "12"))
        self.pin_len = int(os.getenv("PIN_LEN", "6"))
        self.login_rate_window = int(os.getenv("LOGIN_RATE_WINDOW_SEC", "300"))
        self.login_rate_max = int(os.getenv("LOGIN_RATE_MAX_ATTEMPTS", "20"))
        self.lockout_threshold = int(os.getenv("ACCOUNT_LOCKOUT_THRESHOLD", "5"))
        self.lockout_window = int(os.getenv("ACCOUNT_LOCKOUT_WINDOW_SEC", "900"))
        self.lockout_duration = int(os.getenv("ACCOUNT_LOCKOUT_DURATION_SEC", "900"))
        self.session_idle_timeout = int(os.getenv("SESSION_IDLE_TIMEOUT_SEC", "900"))
        self.session_absolute_timeout = int(os.getenv("SESSION_ABSOLUTE_TIMEOUT_SEC", "86400"))
        self.session_cookie_name = os.getenv("SESSION_COOKIE_NAME", "jai_session")
        self.session_secure_cookies = os.getenv("SESSION_SECURE_COOKIES", "false").lower() == "true"
        self.require_mfa = os.getenv("REQUIRE_MFA", "false").lower() == "true"
        self.mfa_enc_key = os.getenv("MFA_ENC_KEY", None)
        self.recovery_code_count = int(os.getenv("RECOVERY_CODE_COUNT", "10"))


class AuthDB:
    def __init__(self, cfg: AuthConfig) -> None:
        self.cfg = cfg
        base_dir = os.path.dirname(self.cfg.db_path)
        if base_dir:
            os.makedirs(base_dir, exist_ok=True)
        self.conn = sqlite3.connect(self.cfg.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        c = self.conn.cursor()
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB,
            pin_hash BLOB,
            totp_secret BLOB,
            is_mfa_enabled INTEGER NOT NULL DEFAULT 0,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            first_failed_at INTEGER,
            lock_until INTEGER,
            created_at INTEGER NOT NULL
        )
        """
        )
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS sessions(
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            last_activity INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            mfa_verified INTEGER NOT NULL DEFAULT 0,
            revoked INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
        )
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS recovery_codes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code_hash BLOB NOT NULL,
            used_at INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
        )
        self.conn.commit()

    def execute(self, sql: str, args: tuple = ()) -> sqlite3.Cursor:
        cur = self.conn.cursor()
        cur.execute(sql, args)
        self.conn.commit()
        return cur

    def query_one(self, sql: str, args: tuple = ()) -> Optional[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(sql, args)
        return cur.fetchone()

    def query_all(self, sql: str, args: tuple = ()) -> List[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(sql, args)
        return cur.fetchall()


def _bcrypt_hash(plaintext: str, rounds: int) -> bytes:
    salt = bcrypt.gensalt(rounds)
    return bcrypt.hashpw(plaintext.encode("utf-8"), salt)


def _bcrypt_verify(plaintext: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(plaintext.encode("utf-8"), hashed)
    except Exception:
        return False


class SessionManager:
    def __init__(self, db: AuthDB, cfg: AuthConfig) -> None:
        self.db = db
        self.cfg = cfg

    def create(self, user_id: int, mfa_verified: bool) -> str:
        now = _now()
        sid = secrets.token_urlsafe(32)
        expires_at = now + self.cfg.session_absolute_timeout
        self.db.execute(
            "INSERT INTO sessions(id,user_id,created_at,last_activity,expires_at,mfa_verified,revoked) VALUES(?,?,?,?,?,?,0)",
            (sid, user_id, now, now, expires_at, 1 if mfa_verified else 0),
        )
        return sid

    def get_valid(self, sid: str) -> Optional[sqlite3.Row]:
        s = self.db.query_one("SELECT * FROM sessions WHERE id=? AND revoked=0", (sid,))
        if not s:
            return None
        now = _now()
        if s["expires_at"] < now:
            self.revoke(sid)
            return None
        if now - s["last_activity"] > self.cfg.session_idle_timeout:
            self.revoke(sid)
            return None
        self.db.execute("UPDATE sessions SET last_activity=? WHERE id=?", (now, sid))
        return self.db.query_one("SELECT * FROM sessions WHERE id= ?", (sid,))

    def require(self, sid: str, require_mfa: bool) -> Optional[sqlite3.Row]:
        s = self.get_valid(sid)
        if not s:
            return None
        if require_mfa and s["mfa_verified"] == 0:
            return None
        return s

    def revoke(self, sid: str) -> None:
        self.db.execute("UPDATE sessions SET revoked=1 WHERE id=?", (sid,))


class AuthService:
    def __init__(self, db: AuthDB, cfg: AuthConfig) -> None:
        self.db = db
        self.cfg = cfg
        self.serializer = URLSafeSerializer(self.cfg.secret_key)
        self.fernet = Fernet(self.cfg.mfa_enc_key) if self.cfg.mfa_enc_key else None
        self.ip_attempts: Dict[str, List[int]] = {}

    def create_initial_user(self, username: str, password: Optional[str], pin: Optional[str]) -> int:
        if self.db.query_one("SELECT id FROM users LIMIT 1"):
            raise ValueError("Already initialized")
        now = _now()
        pw_hash = _bcrypt_hash(password, self.cfg.bcrypt_rounds) if password else None
        pin_hash = _bcrypt_hash(pin, self.cfg.bcrypt_rounds) if pin else None
        cur = self.db.execute(
            "INSERT INTO users(username,password_hash,pin_hash,is_mfa_enabled,created_at) VALUES(?,?,?,?,?)",
            (username, pw_hash, pin_hash, 0, now),
        )
        return cur.lastrowid

    def _get_user(self, username: str) -> Optional[sqlite3.Row]:
        return self.db.query_one("SELECT * FROM users WHERE username=?", (username,))

    def set_password(self, username: str, password: str) -> None:
        pw_hash = _bcrypt_hash(password, self.cfg.bcrypt_rounds)
        self.db.execute("UPDATE users SET password_hash=? WHERE username= ?", (pw_hash, username))

    def set_pin(self, username: str, pin: str) -> None:
        pin_hash = _bcrypt_hash(pin, self.cfg.bcrypt_rounds)
        self.db.execute("UPDATE users SET pin_hash=? WHERE username=?", (pin_hash, username))

    def _rate_key(self, ip: str, username: str) -> str:
        return f"{ip}:{username}"

    def _allow_attempt(self, key: str) -> bool:
        now = _now()
        window = self.cfg.login_rate_window
        bucket = self.ip_attempts.get(key, [])
        bucket = [t for t in bucket if now - t <= window]
        allowed = len(bucket) < self.cfg.login_rate_max
        if allowed:
            bucket.append(now)
        self.ip_attempts[key] = bucket
        return allowed

    def _within_lockout(self, u: sqlite3.Row) -> bool:
        now = _now()
        return bool(u["lock_until"] and u["lock_until"] > now)

    def _record_failure(self, user_id: int) -> None:
        now = _now()
        u = self.db.query_one("SELECT failed_attempts, first_failed_at FROM users WHERE id=?", (user_id,))
        if not u or not u["first_failed_at"] or now - u["first_failed_at"] > self.cfg.lockout_window:
            self.db.execute("UPDATE users SET failed_attempts=?, first_failed_at=? WHERE id=?", (1, now, user_id))
            return
        fa = u["failed_attempts"] + 1
        if fa >= self.cfg.lockout_threshold:
            lock_until = now + self.cfg.lockout_duration
            self.db.execute(
                "UPDATE users SET failed_attempts=?, first_failed_at=?, lock_until=? WHERE id=?",
                (0, None, lock_until, user_id),
            )
        else:
            self.db.execute("UPDATE users SET failed_attempts=? WHERE id=?", (fa, user_id))

    def _reset_failures(self, user_id: int) -> None:
        self.db.execute("UPDATE users SET failed_attempts=0, first_failed_at=NULL, lock_until=NULL WHERE id=?", (user_id,))

    def begin_password_or_pin_login(self, username: str, secret: str, use_pin: bool, ip: str, request_id: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        key = self._rate_key(ip, username)
        if not self._allow_attempt(key):
            logger.warning("auth.rate_limited", extra={"request_id": request_id, "username": username, "ip": ip})
            return None, None, "rate_limited"
        u = self._get_user(username)
        if not u:
            time.sleep(0.25)
            return None, None, "invalid"
        if self._within_lockout(u):
            return None, None, "locked"
        ok = False
        if use_pin and u["pin_hash"]:
            ok = _bcrypt_verify(secret, u["pin_hash"])
        if not use_pin and u["password_hash"]:
            ok = _bcrypt_verify(secret, u["password_hash"])
        if not ok:
            self._record_failure(u["id"])
            logger.info("auth.login_failed", extra={"request_id": request_id, "username": username, "ip": ip})
            time.sleep(0.25)
            return None, None, "invalid"
        self._reset_failures(u["id"])
        needs_mfa = self.cfg.require_mfa or bool(u["is_mfa_enabled"])
        if needs_mfa:
            token = self.serializer.dumps({"username": username, "ts": _now()})
            return u["id"], token, "mfa_required"
        return u["id"], None, None

    def enable_mfa(self, username: str) -> Tuple[str, str]:
        u = self._get_user(username)
        if not u:
            raise ValueError("user not found")
        secret = pyotp.random_base32()
        data = secret.encode("utf-8")
        if self.fernet:
            data = self.fernet.encrypt(data)
        self.db.execute("UPDATE users SET totp_secret=?, is_mfa_enabled=1 WHERE id=?", (data, u["id"]))
        issuer = "JAI"
        uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)
        return secret, uri

    def _get_totp_secret(self, u: sqlite3.Row) -> Optional[str]:
        raw = u["totp_secret"]
        if not raw:
            return None
        data = raw
        if self.fernet:
            try:
                data = self.fernet.decrypt(raw)
            except Exception:
                return None
        return data.decode("utf-8")

    def verify_mfa(self, pending_token: str, code: Optional[str], recovery_code: Optional[str], request_id: str) -> Optional[int]:
        try:
            payload = self.serializer.loads(pending_token)
        except BadSignature:
            return None
        username = payload.get("username")
        u = self._get_user(username)
        if not u:
            return None
        if code:
            secret = self._get_totp_secret(u)
            if not secret:
                return None
            totp = pyotp.TOTP(secret)
            if not totp.verify(code, valid_window=1):
                return None
            return u["id"]
        if recovery_code:
            rows = self.db.query_all(
                "SELECT id, code_hash FROM recovery_codes WHERE user_id=? AND used_at IS NULL",
                (u["id"],),
            )
            for r in rows:
                if _bcrypt_verify(recovery_code, r["code_hash"]):
                    self.db.execute("UPDATE recovery_codes SET used_at=? WHERE id=?", (_now(), r["id"]))
                    return u["id"]
        return None

    def generate_recovery_codes(self, username: str, count: int) -> List[str]:
        u = self._get_user(username)
        if not u:
            raise ValueError("user not found")
        codes = []
        for _ in range(count):
            code = secrets.token_urlsafe(10)
            ch = _bcrypt_hash(code, self.cfg.bcrypt_rounds)
            self.db.execute("INSERT INTO recovery_codes(user_id, code_hash) VALUES(?,?)", (u["id"], ch))
            codes.append(code)
        return codes

    def reset_password_local_console(self, username: str, new_password: str) -> None:
        self.set_password(username, new_password)


def get_client_ip(headers: Dict[str, str], client_host: Optional[str]) -> str:
    xf = None
    try:
        xf = headers.get("x-forwarded-for")
    except Exception:
        pass
    if xf:
        return xf.split(",")[0].strip()
    return client_host or "unknown"
