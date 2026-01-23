import math
import re
from collections import Counter

_PATTERNS = [
    "ignore previous", "override instructions", "jailbreak", "system prompt",
    "developer message", "do anything now", "DAN", "bypass"
]

def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    c = Counter(s)
    n = len(s)
    return -sum((cnt / n) * math.log2(cnt / n) for cnt in c.values() if cnt)

def _ratio_digits(s: str) -> float:
    if not s:
        return 0.0
    d = sum(ch.isdigit() for ch in s)
    return d / max(1, len(s))

def _ratio_symbols(s: str) -> float:
    if not s:
        return 0.0
    sym = sum(1 for ch in s if not ch.isalnum() and not ch.isspace())
    return sym / max(1, len(s))

def _method_code(m: str) -> float:
    m = (m or "").upper()
    if m == "GET":
        return 0.0
    if m == "POST":
        return 1.0
    if m == "PUT":
        return 2.0
    if m == "DELETE":
        return 3.0
    return 4.0

def _severity_code(s: str) -> float:
    s = (s or "").upper()
    if s == "DEBUG":
        return 0.0
    if s == "INFO":
        return 1.0
    if s == "WARNING":
        return 2.0
    if s == "ERROR":
        return 3.0
    if s == "CRITICAL":
        return 4.0
    return 1.0

def _inj_score(t: str) -> float:
    if not t:
        return 0.0
    low = t.lower()
    hits = sum(1 for p in _PATTERNS if p in low)
    return min(1.0, hits / 4.0)

def extract_features(event: dict, kind: str, rates: dict | None = None) -> list[float]:
    kind = (kind or "").lower()
    if rates is None:
        rates = {}
    one_hot = [0.0, 0.0, 0.0, 0.0]
    idx = {"http": 0, "user_behavior": 1, "system_log": 2, "model_io": 3}.get(kind, None)
    if idx is not None:
        one_hot[idx] = 1.0
    base_generic = [
        float(event.get("size", 0.0)),
        float(event.get("duration_ms", 0.0)) / 1000.0,
        _shannon_entropy(str(event.get("core_text", ""))),
        float(rates.get("per_min", 0.0)),
        float(rates.get("per_5min", 0.0)),
    ]
    http_feats = [0.0] * 7
    if kind == "http":
        path = str(event.get("path", ""))
        ua = str(event.get("user_agent", ""))
        method = str(event.get("method", ""))
        status = int(event.get("status", 200))
        qpos = path.find("?")
        pcount = 0 if qpos < 0 else path[qpos+1:].count("&") + (1 if qpos >= 0 else 0)
        http_feats = [
            _method_code(method),
            float(len(path)),
            float(pcount),
            float(int(event.get("headers", 0))),
            float(status // 100),
            _shannon_entropy(path),
            _shannon_entropy(ua),
        ]
    user_feats = [0.0] * 5
    if kind == "user_behavior":
        t = str(event.get("text", ""))
        toks = t.split()
        user_feats = [
            float(len(t)),
            float(len(toks)),
            _shannon_entropy(t),
            _ratio_digits(t),
            _ratio_symbols(t),
        ]
    log_feats = [0.0] * 3
    if kind == "system_log":
        sev = str(event.get("severity", "INFO"))
        msg = str(event.get("message", ""))
        log_feats = [
            _severity_code(sev),
            float(len(msg)),
            _shannon_entropy(msg),
        ]
    mio_feats = [0.0] * 5
    if kind == "model_io":
        it = str(event.get("input_text", ""))
        ot = str(event.get("output_text", ""))
        mio_feats = [
            float(len(it)),
            float(len(ot)),
            _shannon_entropy(it),
            _shannon_entropy(ot),
            _inj_score(it),
        ]
    return one_hot + base_generic + http_feats + user_feats + log_feats + mio_feats
