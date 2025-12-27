from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid
import os
from dotenv import load_dotenv
import re
from jai_assistant import execute_command, sessions as ja_sessions, UserSession as JAUserSession, request_id_ctx_var, detect_language as jai_detect_language
import tempfile
import pathlib
import shutil
import subprocess
import base64
import mimetypes
from fastapi.middleware.cors import CORSMiddleware
try:
    from openai import OpenAI
except Exception:
    OpenAI = None
try:
    import speech_recognition as sr
except Exception:
    sr = None
try:
    from deep_translator import GoogleTranslator as WebTranslator
except Exception:
    WebTranslator = None
try:
    import muse as muse_module
except Exception:
    muse_module = None

load_dotenv()
try:
    load_dotenv('.env.local', override=True)
except Exception:
    pass
app = FastAPI(title="JAI Web API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

 

# CORS (restrict in production by setting JAI_CORS_ORIGINS="https://your.domain")
origins_env = os.environ.get("JAI_CORS_ORIGINS", "*")
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WebTextRequest(BaseModel):
    text: str

class WebPersonaRequest(BaseModel):
    persona: str

class ImageGenRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"

@app.get("/api/health")
async def health_check():
    return {
        "ok": True,
        "time": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    web_id = request.cookies.get("jai_web_id") or str(uuid.uuid4())
    resp = templates.TemplateResponse("index.html", {"request": request})
    if request.cookies.get("jai_web_id") != web_id:
        resp.set_cookie("jai_web_id", web_id, httponly=True, samesite="Lax")
    return resp

@app.get("/manifest.json")
async def manifest():
    path = os.path.join(BASE_DIR, "static", "manifest.json")
    return FileResponse(path)

@app.get("/service-worker.js")
async def service_worker():
    path = os.path.join(BASE_DIR, "static", "service-worker.js")
    return FileResponse(path, media_type="application/javascript")

@app.post("/api/text")
async def api_text(req: WebTextRequest, request: Request):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    token = request_id_ctx_var.set(rid)
    try:
        web_id = request.cookies.get("jai_web_id") or "anon"
        username = f"web:{web_id}"
        if username not in ja_sessions:
            ja_sessions[username] = JAUserSession(username)
        session = ja_sessions[username]
        # Force JAI WEBSITE to English-only responses
        try:
            session.language_mode = "fixed"
            session.preferred_lang = "en"
            session.detected_lang = "en"
        except Exception:
            pass
        desired_lang = "en"
        special = _handle_special_qa(req.text)
        if special is not None:
            result = special
        else:
            result = execute_command(req.text, session, suppress_tts=True)
        result = _ensure_lang(result, desired_lang)
        return {"response": result, "requestId": rid}
    finally:
        try:
            request_id_ctx_var.reset(token)
        except Exception:
            pass

_PERSONA_ALIASES = {
    "story teller": "storyteller",
    "story-teller": "storyteller",
    "trivia game": "trivia",
    "quiz": "trivia",
    "coach": "motivation",
    "meditate": "meditation",
    "counselor": "therapist",
}
_PERSONA_ALLOWED = {"therapist", "storyteller", "trivia", "meditation", "motivation"}

def _normalize_persona(p: str | None) -> str | None:
    if not p:
        return None
    s = (p or "").strip().lower()
    s = _PERSONA_ALIASES.get(s, s)
    return s if s in _PERSONA_ALLOWED else None

_PERSONA_ALIASES = {
    "story teller": "storyteller",
    "story-teller": "storyteller",
    "trivia game": "trivia",
    "quiz": "trivia",
    "coach": "motivation",
    "meditate": "meditation",
    "counselor": "therapist",
}
_PERSONA_ALLOWED = {"therapist", "storyteller", "trivia", "meditation", "motivation"}

def _normalize_persona(p: str | None) -> str | None:
    if not p:
        return None
    s = (p or "").strip().lower()
    s = _PERSONA_ALIASES.get(s, s)
    return s if s in _PERSONA_ALLOWED else None

@app.get("/api/persona")
async def api_get_persona(request: Request):
    web_id = request.cookies.get("jai_web_id") or "anon"
    username = f"web:{web_id}"
    if username not in ja_sessions:
        ja_sessions[username] = JAUserSession(username)
    session = ja_sessions[username]
    cur = getattr(session, "persona", None) or ""
    return {"persona": cur}

@app.post("/api/persona")
async def api_set_persona(req: WebPersonaRequest, request: Request):
    web_id = request.cookies.get("jai_web_id") or "anon"
    username = f"web:{web_id}"
    if username not in ja_sessions:
        ja_sessions[username] = JAUserSession(username)
    session = ja_sessions[username]
    p = _normalize_persona(req.persona)
    if not p:
        return JSONResponse({"error": "Invalid persona"}, status_code=400)
    try:
        session.persona = p
    except Exception:
        setattr(session, "persona", p)
    return {"persona": p}

_IMG_LIMIT = int(os.environ.get("JAI_IMG_DAILY_LIMIT", "4") or "4")
_IMG_QUOTA = {}

def _quota_status(username: str):
    from datetime import timedelta
    now = datetime.utcnow()
    q = _IMG_QUOTA.get(username)
    if not q or not isinstance(q, dict) or not q.get("reset_at"):
        q = {"used": 0, "reset_at": now + timedelta(hours=24)}
        _IMG_QUOTA[username] = q
    else:
        if now >= q["reset_at"]:
            q["used"] = 0
            q["reset_at"] = now + timedelta(hours=24)
    remaining = max(0, _IMG_LIMIT - int(q["used"]))
    secs = max(0.0, (q["reset_at"] - now).total_seconds())
    hours = secs / 3600.0
    return {"used": int(q["used"]), "limit": _IMG_LIMIT, "remaining": remaining, "resetInHours": hours, "resetAt": q["reset_at"].isoformat() + "Z"}

@app.get("/api/image/quota")
async def api_image_quota(request: Request):
    web_id = request.cookies.get("jai_web_id") or "anon"
    username = f"web:{web_id}"
    return _quota_status(username)

@app.post("/api/image/generate")
async def api_image_generate(req: ImageGenRequest, request: Request):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    token = request_id_ctx_var.set(rid)
    try:
        web_id = request.cookies.get("jai_web_id") or "anon"
        username = f"web:{web_id}"
        status = _quota_status(username)
        if status["used"] >= status["limit"]:
            hrs = status.get("resetInHours", 24.0)
            return JSONResponse({"error": f"You've reached your daily limit of {status['limit']}. Your credits will reset in {hrs:.1f} hours."}, status_code=429)
        if muse_module is None or not hasattr(muse_module, "generate_image"):
            return JSONResponse({"error": "Image generation is not available."}, status_code=503)
        prompt = (req.prompt or "").strip()
        if not prompt:
            return JSONResponse({"error": "Please provide a prompt."}, status_code=400)
        size = (req.size or "1024x1024").strip()
        try:
            out_path = muse_module.generate_image(prompt, size=size)
        except Exception:
            return JSONResponse({"error": "Image generation failed."}, status_code=500)
        try:
            data = pathlib.Path(out_path).read_bytes()
            data_url = _image_to_data_url("image/png", data)
        except Exception:
            data_url = ""
        q = _IMG_QUOTA.get(username)
        if q:
            q["used"] = int(q.get("used", 0)) + 1
        out_status = _quota_status(username)
        return {"imageDataUrl": data_url, "status": out_status, "requestId": rid}
    finally:
        try:
            request_id_ctx_var.reset(token)
        except Exception:
            pass

def _ffmpeg_bin() -> str:
    return os.environ.get("FFMPEG_BIN") or "ffmpeg"

def _ffmpeg_exists() -> bool:
    bin_path = _ffmpeg_bin()
    try:
        if os.path.isabs(bin_path) and os.path.exists(bin_path):
            return True
    except Exception:
        pass
    return shutil.which(bin_path) is not None

def _convert_to_wav16k_mono(src_path: str) -> str:
    dst_fd, dst_path = tempfile.mkstemp(suffix=".wav")
    os.close(dst_fd)
    # ffmpeg -i input -ac 1 -ar 16000 -y output.wav
    cmd = [
        _ffmpeg_bin(), "-y",
        "-i", src_path,
        "-ac", "1",
        "-ar", "16000",
        dst_path,
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return dst_path
    except subprocess.CalledProcessError as e:
        try:
            os.remove(dst_path)
        except Exception:
            pass
        raise RuntimeError("ffmpeg conversion failed") from e

def _transcribe_wav(path: str, lang: str) -> str:
    # Prefer OpenAI Whisper if key and client available
    api_key = os.environ.get("OPENAI_API_KEY")
    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key)
            with open(path, "rb") as f:
                tr = client.audio.transcriptions.create(model="whisper-1", file=f)
            if hasattr(tr, "text") and tr.text:
                return tr.text
        except Exception:
            pass
    # Fallback to SpeechRecognition offline API (uses Google Web Speech - internet required)
    if sr is None:
        return ""
    try:
        r = sr.Recognizer()
        with sr.AudioFile(path) as source:
            audio = r.record(source)
        try:
            return r.recognize_google(audio, language=lang)
        except Exception:
            return ""
    except Exception:
        return ""

def _lang_code_of(s: str) -> str:
    try:
        base = (s or "").split("-", 1)[0].lower()
        return base if base else "en"
    except Exception:
        return "en"

def _ensure_lang(text: str, desired_lang: str) -> str:
    try:
        dl = (desired_lang or "en").lower()
        if not text:
            return text
        res_lang = jai_detect_language(text)
        if res_lang == dl:
            return text
        if WebTranslator is not None:
            try:
                return WebTranslator(source='auto', target=dl).translate(text)
            except Exception:
                return text
        return text
    except Exception:
        return text

def _image_to_data_url(mime: str, data: bytes) -> str:
    try:
        b64 = base64.b64encode(data).decode('ascii')
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""

def _analyze_image_bytes(data: bytes, mime: str, prompt: str) -> str:
    try:
        data_url = _image_to_data_url(mime, data)
        if not data_url:
            return "Could not read image data."
        api_key = os.environ.get("OPENAI_API_KEY")
        if OpenAI and api_key:
            try:
                client = OpenAI(api_key=api_key)
                user_prompt = (prompt or "").strip()
                if not user_prompt:
                    user_prompt = "Describe this image in detail and answer any implicit questions. Respond only in English."
                else:
                    user_prompt = user_prompt + "\n\nIMPORTANT: Respond only in English."
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ]
                resp = client.chat.completions.create(
                    model=os.environ.get("JAI_VISION_MODEL", "gpt-4o-mini"),
                    messages=messages,
                    max_tokens=800,
                    temperature=0.2,
                )
                text = resp.choices[0].message.content
                return (text or "").strip() or "No description generated."
            except Exception:
                pass
        return "Image analysis is not available on this server. Set OPENAI_API_KEY to enable vision analysis."
    except Exception:
        return "Image analysis failed."

def _handle_special_qa(user_text: str) -> Optional[str]:
    try:
        low = (user_text or "").strip().lower()
        if re.search(r"\bwho\s+(?:created|made|built)\s+(?:you|aj|jai)\b", low):
            return "I was created by Abdul Rehman as a personal AI project, developed without prior professional experience."
        return None
    except Exception:
        return None

@app.post("/api/image")
async def api_image(request: Request, file: UploadFile = File(...), prompt: str = Form("")):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    token = request_id_ctx_var.set(rid)
    try:
        web_id = request.cookies.get("jai_web_id") or "anon"
        username = f"web:{web_id}"
        if username not in ja_sessions:
            ja_sessions[username] = JAUserSession(username)
        session = ja_sessions[username]
        # Force JAI WEBSITE to English-only responses
        try:
            session.language_mode = "fixed"
            session.preferred_lang = "en"
            session.detected_lang = "en"
        except Exception:
            pass

        data = await file.read()
        mime = (getattr(file, "content_type", None) or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream")
        if not isinstance(mime, str):
            mime = "application/octet-stream"
        if not mime.startswith("image/"):
            return JSONResponse({"error": "Unsupported file type. Please upload an image."}, status_code=400)

        analysis = _analyze_image_bytes(data, mime, prompt)
        analysis = _ensure_lang(analysis, "en")
        return {"response": analysis, "requestId": rid}
    finally:
        try:
            request_id_ctx_var.reset(token)
        except Exception:
            pass

@app.post("/api/voice")
async def api_voice(request: Request, file: UploadFile = File(...), lang: str = Form("en-US")):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    token = request_id_ctx_var.set(rid)
    try:
        # Save uploaded audio (accept webm/ogg/wav/flac/etc.)
        up_ext = pathlib.Path(file.filename or "").suffix.lower() or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=up_ext) as tmp:
            data = await file.read()
            tmp.write(data)
            src_path = tmp.name

        # Ensure we have ffmpeg for webm/ogg -> wav conversion
        if not _ffmpeg_exists():
            # If file is already wav/flac we can try SpeechRecognition directly; else error
            if up_ext not in {".wav", ".flac"}:
                return JSONResponse({"error": "ffmpeg not installed. Install ffmpeg to process web audio."}, status_code=400)
            wav_path = src_path
        else:
            wav_path = _convert_to_wav16k_mono(src_path)

        # Transcribe
        text = _transcribe_wav(wav_path, lang)
        web_id = request.cookies.get("jai_web_id") or "anon"
        username = f"web:{web_id}"
        if username not in ja_sessions:
            ja_sessions[username] = JAUserSession(username)
        session = ja_sessions[username]
        if not text:
            return {"transcript": "", "response": "Could not transcribe."}
        # Force JAI WEBSITE to English-only responses
        try:
            session.language_mode = "fixed"
            session.preferred_lang = "en"
            session.detected_lang = "en"
        except Exception:
            pass
        desired_lang = "en"
        special = _handle_special_qa(text)
        if special is not None:
            result = special
        else:
            result = execute_command(text, session, suppress_tts=True)
        result = _ensure_lang(result, desired_lang)
        return {"transcript": text, "response": result, "requestId": rid}
    finally:
        try:
            request_id_ctx_var.reset(token)
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)