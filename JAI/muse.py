import os
import io
import base64
import uuid
from pathlib import Path
from typing import List, Tuple, Optional

import requests
from PIL import Image, ImageDraw, ImageFont

try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None

try:
    from duckduckgo_search import DDGS
except Exception:
    DDGS = None

OUTPUT_DIR = Path(os.environ.get("MUSE_OUTPUT_DIR", "muse_outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(prefix: str, ext: str) -> Path:
    return OUTPUT_DIR / f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"


def _placeholder_image(prompt: str, size: str = "1024x1024") -> Path:
    try:
        w, h = [int(x) for x in size.lower().split("x", 1)]
    except Exception:
        w, h = 1024, 1024
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = int(40 + (215 * y) / h)
        g = int(60 + (195 * y) / h)
        b = int(90 + (165 * y) / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    text = (prompt or "Muse").strip()
    try:
        font = ImageFont.truetype("arial.ttf", size=max(16, w // 24))
    except Exception:
        font = ImageFont.load_default()
    tw, th = draw.textlength(text, font=font), font.size + 6
    draw.rectangle([(20, h - th - 40), (min(w - 20, 20 + int(tw) + 24), h - 20)], fill=(0, 0, 0, 160))
    draw.text((30, h - th - 30), text[:100], fill=(255, 255, 255), font=font)
    out = _safe_filename("muse", "png")
    img.save(out)
    return out


def generate_image(prompt: str, size: str = "1024x1024") -> Path:
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.images.generate(model="gpt-image-1", prompt=prompt, size=size)
            b64 = resp.data[0].b64_json
            raw = base64.b64decode(b64)
            img = Image.open(io.BytesIO(raw))
            out = _safe_filename("muse", "png")
            img.save(out)
            return out
        except Exception:
            pass
    return _placeholder_image(prompt, size)


def transcribe_audio_file(file_path: str, language: str = "en-US") -> str:
    if not sr:
        return "Transcription not available"
    p = Path(file_path)
    if not p.exists():
        return "File not found"
    try:
        r = sr.Recognizer()
        with sr.AudioFile(str(p)) as source:
            audio = r.record(source)
        try:
            return r.recognize_google(audio, language=language)
        except Exception:
            return "Could not transcribe"
    except Exception:
        return "Transcription error"


def detect_objects_in_image(file_path: str) -> Tuple[Optional[Path], List[str]]:
    if not cv2:
        return None, []
    p = Path(file_path)
    if not p.exists():
        return None, []
    img = cv2.imread(str(p))
    if img is None:
        return None, []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    try:
        face_xml = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(face_xml)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        labels = [f"faces:{len(faces)}"]
    except Exception:
        labels = []
    out = _safe_filename("detected", "png")
    cv2.imwrite(str(out), img)
    return out, labels


def image_search(query: str, max_results: int = 5) -> List[Path]:
    if not DDGS:
        return []
    results = []
    try:
        with DDGS() as ddgs:
            for i, r in enumerate(ddgs.images(keywords=query, max_results=max_results)):
                url = r.get("image") or r.get("thumbnail") or r.get("url")
                if not url:
                    continue
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200 and resp.content:
                        ext = "jpg"
                        out = _safe_filename("search", ext)
                        out.write_bytes(resp.content)
                        results.append(out)
                except Exception:
                    continue
                if len(results) >= max_results:
                    break
    except Exception:
        return results
    return results
