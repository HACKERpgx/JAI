from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

try:
    from sklearn.ensemble import IsolationForest
except Exception:  # pragma: no cover
    IsolationForest = None  # type: ignore

try:  # Optional deep learning path
    from tensorflow import keras  # type: ignore
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    keras = None  # type: ignore
    np = None  # type: ignore


@dataclass
class DetectionResult:
    is_anomaly: bool
    score: float
    reason: str
    model: str


class BaseDetector:
    def fit(self, X: List[List[float]]) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def predict(self, x: List[float]) -> DetectionResult:  # pragma: no cover - interface
        raise NotImplementedError


class IsolationForestDetector(BaseDetector):
    def __init__(self, contamination: float = 0.01, random_state: int = 42):
        if IsolationForest is None:
            raise RuntimeError("scikit-learn is required for IsolationForestDetector")
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=200,
            max_samples="auto",
            random_state=random_state,
            n_jobs=1,
        )
        self.trained = False

    def fit(self, X: List[List[float]]) -> None:
        if not X:
            return
        self.model.fit(X)
        self.trained = True

    def predict(self, x: List[float]) -> DetectionResult:
        if not self.trained:
            # During warmup, do not flag anomalies to minimize false positives
            return DetectionResult(False, 0.0, "warmup", "isoforest")
        # decision_function: higher -> more normal; negative -> anomalies
        score = float(self.model.decision_function([x])[0])
        pred = int(self.model.predict([x])[0])  # -1 = anomaly, 1 = normal
        is_anom = pred == -1 or score < -0.05  # be conservative
        reason = "iforest_pred=-1" if pred == -1 else ("low_decision_score" if score < -0.05 else "normal")
        return DetectionResult(is_anom, score, reason, "isoforest")


class AutoencoderDetector(BaseDetector):
    def __init__(self, input_dim: int, threshold_quantile: float = 0.995):
        if keras is None or np is None:
            raise RuntimeError("TensorFlow/Keras not available")
        self.input_dim = input_dim
        self.threshold_quantile = threshold_quantile
        self.model = self._build_model(input_dim)
        self.threshold: Optional[float] = None

    def _build_model(self, d: int):
        model = keras.Sequential([
            keras.layers.Input(shape=(d,)),
            keras.layers.Dense(max(8, d // 2), activation="relu"),
            keras.layers.Dense(max(4, d // 4), activation="relu"),
            keras.layers.Dense(max(8, d // 2), activation="relu"),
            keras.layers.Dense(d, activation="linear"),
        ])
        model.compile(optimizer="adam", loss="mse")
        return model

    def fit(self, X: List[List[float]]) -> None:
        if not X:
            return
        arr = np.array(X, dtype="float32")
        # Simple early-stopping-free quick fit
        self.model.fit(arr, arr, epochs=5, batch_size=32, verbose=0)
        recon = self.model.predict(arr, verbose=0)
        errs = np.mean((arr - recon) ** 2, axis=1)
        self.threshold = float(np.quantile(errs, self.threshold_quantile))

    def predict(self, x: List[float]) -> DetectionResult:
        if self.threshold is None:
            return DetectionResult(False, 0.0, "warmup", "autoencoder")
        arr = np.array([x], dtype="float32")
        recon = self.model.predict(arr, verbose=0)
        err = float(((arr - recon) ** 2).mean())
        is_anom = err > self.threshold
        score = -err  # lower is worse, invert for consistency
        reason = "reconstruction_error" if is_anom else "normal"
        return DetectionResult(is_anom, score, reason, "autoencoder")


class BasicStatsDetector(BaseDetector):
    def __init__(self, threshold: float = 4.5):
        self.threshold = float(threshold)
        self.center: Optional[List[float]] = None
        self.scale: Optional[List[float]] = None
        self.trained = False

    def _median(self, v: List[float]) -> float:
        s = sorted(v)
        n = len(s)
        if n == 0:
            return 0.0
        m = n // 2
        if n % 2:
            return float(s[m])
        return float((s[m - 1] + s[m]) / 2.0)

    def _mad(self, v: List[float], med: float) -> float:
        d = [abs(x - med) for x in v]
        m = self._median(d)
        return float(m) * 1.4826

    def fit(self, X: List[List[float]]) -> None:
        if not X:
            return
        d = len(X[0])
        cols = [[row[i] for row in X] for i in range(d)]
        centers: List[float] = []
        scales: List[float] = []
        for col in cols:
            med = self._median(col)
            mad = self._mad(col, med)
            centers.append(med)
            scales.append(mad if mad > 1e-6 else 1.0)
        self.center = centers
        self.scale = scales
        self.trained = True

    def predict(self, x: List[float]) -> DetectionResult:
        if not self.trained or self.center is None or self.scale is None:
            return DetectionResult(False, 0.0, "warmup", "basicstats")
        zs = [abs((xi - c) / s) for xi, c, s in zip(x, self.center, self.scale)]
        maxz = max(zs) if zs else 0.0
        count_extreme = sum(1 for z in zs if z > self.threshold)
        is_anom = bool(maxz > (self.threshold + 1.0) or count_extreme >= 3)
        score = -maxz
        reason = "high_zscore" if is_anom else "normal"
        return DetectionResult(is_anom, score, reason, "basicstats")
