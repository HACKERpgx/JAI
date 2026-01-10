# Facade package to access shared JAI core modules from apps/gui and apps/web
import jai_assistant as jai
from jai_assistant import execute_command, UserSession, request_id_ctx_var, sessions
from jai_calendar import CalendarManager, handle_calendar_command
from jai_media import handle_media_command
import tts
import stt
try:
    import muse
except Exception:  # pragma: no cover
    muse = None

__all__ = [
    "jai",
    "execute_command",
    "UserSession",
    "request_id_ctx_var",
    "sessions",
    "CalendarManager",
    "handle_calendar_command",
    "handle_media_command",
    "tts",
    "stt",
    "muse",
]
