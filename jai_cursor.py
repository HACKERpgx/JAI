# jai_cursor.py
# Mouse control for JAI using PyAutoGUI with failsafe, auth gating, and action logging.

import time
import re
import logging
from typing import Optional, Tuple

try:
    import pyautogui as pag
except Exception:
    pag = None

# Configure PyAutoGUI (failsafe + small pause between actions)
if pag is not None:
    pag.FAILSAFE = True        # Move mouse to any screen corner to abort
    pag.PAUSE = 0.05

# Dedicated logger for cursor actions
_cursor_logger = logging.getLogger("jai_cursor")
if not _cursor_logger.handlers:
    _cursor_logger.setLevel(logging.INFO)
    _fh = logging.FileHandler("jai_cursor_log.txt", encoding="utf-8")
    _fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    _cursor_logger.addHandler(_fh)
    _cursor_logger.propagate = False


def _is_authorized(session) -> bool:
    """
    Reuse JAI's existing memory unlock window as authorization (PIN/password).
    Returns True if session.memory_auth_until is in the future.
    """
    try:
        return int(time.time()) <= int(getattr(session, "memory_auth_until", 0) or 0)
    except Exception:
        return False


def _screen_size() -> Tuple[int, int]:
    if pag is None:
        return (0, 0)
    try:
        w, h = pag.size()
        return int(w), int(h)
    except Exception:
        return (0, 0)


def _clamp(x: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, x))


def _move_to(x: int, y: int, duration: float = 0.2) -> str:
    w, h = _screen_size()
    x2 = _clamp(x, 0, max(0, w - 1))
    y2 = _clamp(y, 0, max(0, h - 1))
    pag.moveTo(x2, y2, duration=duration)
    _cursor_logger.info("moveTo(%d, %d, duration=%.2f)", x2, y2, duration)
    return f"Moved cursor to ({x2}, {y2})."


def _move_rel(dx: int, dy: int, duration: float = 0.2) -> str:
    pag.moveRel(dx, dy, duration=duration)
    _cursor_logger.info("moveRel(%d, %d, duration=%.2f)", dx, dy, duration)
    return f"Moved cursor by ({dx}, {dy})."


def _click(button: str = "left", clicks: int = 1) -> str:
    pag.click(button=button, clicks=clicks, interval=0.08)
    _cursor_logger.info("click(button=%s, clicks=%d)", button, clicks)
    if clicks == 2:
        return f"Double-clicked ({button}) at current position."
    return f"Clicked ({button}) at current position."


def _position() -> str:
    x, y = pag.position()
    _cursor_logger.info("position() -> (%d, %d)", x, y)
    return f"Cursor is at ({x}, {y})."


def _scroll(amount: int) -> str:
    pag.scroll(amount)
    _cursor_logger.info("scroll(%d)", amount)
    direction = "up" if amount > 0 else "down"
    return f"Scrolled {direction} by {abs(amount)}."


def _parse_mouse_command(text: str) -> Optional[Tuple[str, tuple]]:
    """
    Returns a tuple (action, args) or None if not a mouse command.
    Supported actions:
      - move_to (x, y)
      - move_to_center ()
      - move_to_corner (name) where name in {"top-left","top-right","bottom-left","bottom-right"}
      - move_rel (dx, dy)
      - click (button, clicks)
      - position ()
      - scroll (amount)
    """
    s = (text or "").strip().lower()

    # Position query
    if re.search(r"\b(cursor\s+)?position\b|where\s+is\s+(the\s+)?cursor", s):
        return ("position", ())

    # Center
    if re.search(r"\b(move|go)\s+(the\s+)?(mouse|cursor)\s+to\s+(center|middle)\b", s):
        return ("move_to_center", ())

    # Corners
    m = re.search(r"\b(move|go)\s+(the\s+)?(mouse|cursor)\s+to\s+(top[-\s]?left|top[-\s]?right|bottom[-\s]?left|bottom[-\s]?right)\b", s)
    if m:
        corner = m.group(4).replace(" ", "-")
        return ("move_to_corner", (corner,))

    # Move to x, y
    m = re.search(r"\b(move|go)\s+(the\s+)?(mouse|cursor)\s+to\s+(\d+)\s*,\s*(\d+)\b", s)
    if m:
        x = int(m.group(4))
        y = int(m.group(5))
        return ("move_to", (x, y))

    # Relative move: left/right/up/down by N (px)
    # e.g. "move cursor left 200", "go up by 50 pixels"
    m = re.search(r"\b(move|go)\s+(the\s+)?(mouse|cursor)?\s*(left|right|up|down)\s*(?:by\s*)?(\d+)\s*(?:px|pixels)?\b", s)
    if m:
        dir_ = m.group(4)
        amt = int(m.group(5))
        dx = dy = 0
        if dir_ == "left":
            dx = -amt
        elif dir_ == "right":
            dx = amt
        elif dir_ == "up":
            dy = -amt
        elif dir_ == "down":
            dy = amt
        return ("move_rel", (dx, dy))

    # Click variants
    if re.search(r"\b(double\s+click|double-click)\b", s):
        return ("click", ("left", 2))
    if re.search(r"\b(right\s+click|right-click)\b", s):
        return ("click", ("right", 1))
    if re.search(r"\b(click)\b", s):
        return ("click", ("left", 1))

    # Scroll
    m = re.search(r"\bscroll\s+(up|down)\s*(\d+)?\b", s)
    if m:
        direction = m.group(1)
        amount = int(m.group(2)) if m.group(2) else 500
        if direction == "up":
            return ("scroll", (abs(amount),))
        else:
            return ("scroll", (-abs(amount),))

    # Move keywords without numbers: "move cursor up", assume default step
    m = re.search(r"\b(move|go)\s+(the\s+)?(mouse|cursor)?\s*(left|right|up|down)\b", s)
    if m:
        dir_ = m.group(4)
        step = 100
        dx = dy = 0
        if dir_ == "left":
            dx = -step
        elif dir_ == "right":
            dx = step
        elif dir_ == "up":
            dy = -step
        elif dir_ == "down":
            dy = step
        return ("move_rel", (dx, dy))

    return None


def handle_mouse_command(command: str, session) -> Optional[str]:
    """
    Main entry callable from JAI. Returns:
      - A user-facing status string if this was a mouse command (success or error),
      - None if not a mouse command (so caller can continue other handlers).
    Security: requires JAI's memory password (session.memory_auth_until) to be active.
    """
    # Not available
    if pag is None:
        return "Mouse control unavailable. Install pyautogui: pip install pyautogui"

    parsed = _parse_mouse_command(command)
    if not parsed:
        return None  # Not a mouse-related command

    # Security gate
    if not _is_authorized(session):
        return "Mouse control is locked. Provide the memory password to unlock for 15 minutes."

    action, args = parsed
    try:
        if action == "position":
            return _position()
        if action == "move_to_center":
            w, h = _screen_size()
            if w <= 0 or h <= 0:
                return "Could not determine screen size."
            return _move_to(w // 2, h // 2)
        if action == "move_to_corner":
            corner = (args[0] or "").replace(" ", "-")
            w, h = _screen_size()
            if w <= 0 or h <= 0:
                return "Could not determine screen size."
            corners = {
                "top-left": (0, 0),
                "top-right": (w - 1, 0),
                "bottom-left": (0, h - 1),
                "bottom-right": (w - 1, h - 1),
            }
            target = corners.get(corner, (w // 2, h // 2))
            return _move_to(target[0], target[1])
        if action == "move_to":
            x, y = int(args[0]), int(args[1])
            return _move_to(x, y)
        if action == "move_rel":
            dx, dy = int(args[0]), int(args[1])
            return _move_rel(dx, dy)
        if action == "click":
            button, clicks = args[0], int(args[1])
            return _click(button=button, clicks=clicks)
        if action == "scroll":
            amount = int(args[0])
            return _scroll(amount)
        return "Mouse command parsed but not implemented."
    except pag.FailSafeException:
        _cursor_logger.warning("PyAutoGUI FailSafe triggered (user moved mouse to corner).")
        return "Action aborted by failsafe (mouse moved to screen corner)."
    except Exception as e:
        _cursor_logger.error("Error handling mouse command '%s': %s", command, e)
        return f"Failed to execute mouse command: {e}"S