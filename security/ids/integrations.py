import os
import json
import time
import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from .pipeline import RealTimeIDS

_ids_instance: Optional[RealTimeIDS] = None


def get_ids_instance() -> RealTimeIDS:
    global _ids_instance
    if _ids_instance is None:
        warmup = int(os.environ.get("JAI_IDS_WARMUP", "400") or 400)
        contamination = float(os.environ.get("JAI_IDS_CONTAMINATION", "0.02") or 0.02)
        use_ae = (os.environ.get("JAI_IDS_AUTOENCODER", "0") == "1")
        _ids_instance = RealTimeIDS(
            warmup_samples=warmup,
            contamination=contamination,
            use_autoencoder=use_ae,
        )
    return _ids_instance


class IDSHTTPMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.ids = get_ids_instance()

    async def dispatch(self, request: Request, call_next):
        t0 = time.time()
        path = request.url.path or "/"
        method = request.method
        ua = request.headers.get("user-agent", "")
        hdrs = len(request.headers or {})
        size = 0.0
        user_text: Optional[str] = None
        try:
            cl = request.headers.get("content-length")
            if cl:
                size = float(cl)
        except Exception:
            size = 0.0
        # Do not read request body here to avoid consuming it before FastAPI parses.
        try:
            response = await call_next(request)
            status = getattr(response, "status_code", 200)
            dt = (time.time() - t0) * 1000.0
            try:
                self.ids.process_event("http", {
                    "path": path,
                    "method": method,
                    "user_agent": ua,
                    "headers": hdrs,
                    "status": status,
                    "size": size,
                    "duration_ms": dt,
                })
                if user_text is not None:
                    self.ids.process_event("user_behavior", {
                        "text": user_text,
                        "size": float(len(user_text)),
                        "duration_ms": 0.0,
                    })
                if path in ("/api/text", "/api/voice"):
                    try:
                        body_bytes = getattr(response, "body", b"")
                        if isinstance(body_bytes, (bytes, bytearray)) and body_bytes:
                            j = json.loads(body_bytes)
                            in_text = user_text or str(j.get("transcript", ""))
                            out_text = str(j.get("response", ""))
                            self.ids.process_event("model_io", {
                                "input_text": in_text,
                                "output_text": out_text,
                                "size": float(len(out_text)),
                                "duration_ms": dt,
                            })
                    except Exception:
                        pass
            except Exception:
                pass
            return response
        except Exception as e:
            dt = (time.time() - t0) * 1000.0
            try:
                self.ids.process_event("http", {
                    "path": path,
                    "method": method,
                    "user_agent": ua,
                    "headers": hdrs,
                    "status": 500,
                    "size": size,
                    "duration_ms": dt,
                })
            except Exception:
                pass
            raise e


class IDSLogHandler(logging.Handler):
    def __init__(self, level: int = logging.WARNING) -> None:
        super().__init__(level)
        self.ids = get_ids_instance()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record) if self.formatter else record.getMessage()
            sev = record.levelname
            self.ids.process_event("system_log", {
                "severity": sev,
                "message": (msg[:2000] if isinstance(msg, str) else str(msg)),
                "size": float(len(msg) if isinstance(msg, str) else 0),
                "duration_ms": 0.0,
            })
        except Exception:
            pass


def mount_ids_routes(app: FastAPI) -> None:
    ids = get_ids_instance()

    @app.get("/api/security/ids/status")
    async def ids_status():
        return ids.stats()


_DEF_ATTACHED = False


def init_ids(app: FastAPI, attach_logging: bool = True) -> RealTimeIDS:
    global _DEF_ATTACHED
    ids_enabled = os.environ.get("JAI_IDS_ENABLED", "1") == "1"
    ids = get_ids_instance()
    if not ids_enabled:
        return ids
    if not _DEF_ATTACHED:
        try:
            app.add_middleware(IDSHTTPMiddleware)
        except Exception:
            pass
        try:
            mount_ids_routes(app)
        except Exception:
            pass
        if attach_logging:
            try:
                handler = IDSLogHandler(level=logging.WARNING)
                root = logging.getLogger()
                root.addHandler(handler)
            except Exception:
                pass
        _DEF_ATTACHED = True
    return ids
