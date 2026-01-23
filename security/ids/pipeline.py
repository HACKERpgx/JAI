from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Optional

from .features import extract_features
from .models import IsolationForestDetector, AutoencoderDetector, DetectionResult, BasicStatsDetector


class RealTimeIDS:
    def __init__(
        self,
        warmup_samples: int = 400,
        contamination: float = 0.02,
        use_autoencoder: bool = False,
        max_buffer: int = 5000,
    ) -> None:
        self.lock = threading.Lock()
        try:
            self.detector = IsolationForestDetector(contamination=contamination)
        except Exception:
            self.detector = BasicStatsDetector()
        self.autoencoder: Optional[AutoencoderDetector] = None
        self.use_autoencoder = use_autoencoder
        self.warmup_samples = max(50, int(warmup_samples))
        self.max_buffer = max_buffer
        self._train_X: List[List[float]] = []
        self._event_times: Deque[float] = deque()
        self._event_times_5m: Deque[float] = deque()
        self._trained = False
        self._last_alerts: Deque[Dict[str, Any]] = deque(maxlen=50)
        self._total_events = 0
        self._anomaly_events = 0
        self._callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def register_callback(self, cb: Callable[[Dict[str, Any]], None]) -> None:
        with self.lock:
            self._callbacks.append(cb)

    def _update_rates(self, now: float) -> Dict[str, float]:
        one_min = now - 60.0
        while self._event_times and self._event_times[0] < one_min:
            self._event_times.popleft()
        five_min = now - 300.0
        while self._event_times_5m and self._event_times_5m[0] < five_min:
            self._event_times_5m.popleft()
        self._event_times.append(now)
        self._event_times_5m.append(now)
        return {
            "per_min": float(len(self._event_times)),
            "per_5min": float(len(self._event_times_5m)),
        }

    def _maybe_train(self, x: List[float]) -> None:
        if self._trained:
            return
        if len(self._train_X) < self.warmup_samples:
            return
        self.detector.fit(self._train_X)
        self._trained = True
        if self.use_autoencoder:
            try:
                self.autoencoder = AutoencoderDetector(input_dim=len(x))
                self.autoencoder.fit(self._train_X)
            except Exception:
                self.autoencoder = None

    def process_event(self, kind: str, event: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        with self.lock:
            rates = self._update_rates(now)
            core_text = event.get("text") or event.get("message") or event.get("input_text") or ""
            event["core_text"] = core_text
            x = extract_features(event, kind, rates)
            if len(self._train_X) < self.max_buffer:
                self._train_X.append(x)
            else:
                self._train_X.pop(0)
                self._train_X.append(x)
            self._maybe_train(x)
            res: DetectionResult = self.detector.predict(x)
            if self._trained and self.autoencoder is not None:
                try:
                    ae_res = self.autoencoder.predict(x)
                    if ae_res.is_anomaly and not res.is_anomaly:
                        res = ae_res
                except Exception:
                    pass
            self._total_events += 1
            alert = {
                "ts": now,
                "kind": kind,
                "is_anomaly": res.is_anomaly,
                "score": res.score,
                "reason": res.reason,
                "model": res.model,
            }
            if res.is_anomaly:
                self._anomaly_events += 1
                self._last_alerts.append(alert)
                for cb in list(self._callbacks):
                    try:
                        cb(alert)
                    except Exception:
                        pass
            return alert

    def stats(self) -> Dict[str, Any]:
        with self.lock:
            trained = self._trained
            model = "autoencoder" if (trained and self.autoencoder is not None and self.use_autoencoder) else "isoforest"
            return {
                "trained": trained,
                "model": model,
                "warmup": max(0, self.warmup_samples - len(self._train_X)),
                "buffer_size": len(self._train_X),
                "total_events": self._total_events,
                "anomalies": self._anomaly_events,
                "recent_alerts": list(self._last_alerts),
            }
