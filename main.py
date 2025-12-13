from fastapi import FastAPI, HTTPException, Header, Request, Response, UploadFile, File, Form
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

load_dotenv()
try:
    load_dotenv('.env.local', override=True)
except Exception:
    pass
app = FastAPI(title="JAI Mobile API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
JAI_MOBILE_TOKEN = os.environ.get("JAI_MOBILE_TOKEN", "my-super-secret-token-123")
if JAI_MOBILE_TOKEN == "my-super-secret-token-123":
    print("[WARN] Using default JAI_MOBILE_TOKEN; set env JAI_MOBILE_TOKEN for production")

# Store device states (in-memory for simplicity)
device_states = {}

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

class HeartbeatRequest(BaseModel):
    deviceId: str
    status: str  # idle|busy|error
    battery: int
    appVersion: str
    timestamp: str

class HeartbeatResponse(BaseModel):
    intervalMs: int
    action: str  # none|sync|speak
    message: Optional[str] = None

class EventRequest(BaseModel):
    type: str  # error|info
    message: str
    data: dict = {}

class MobileCommandRequest(BaseModel):
    deviceId: str
    text: str
    suppressTTS: Optional[bool] = True

class WebTextRequest(BaseModel):
    text: str

# Middleware to validate auth token and request-id
@app.middleware("http")
async def validate_auth(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/mobile/"):
        auth = request.headers.get("authorization")
        request_id = request.headers.get("x-request-id")
        if not auth or auth != f"Bearer {JAI_MOBILE_TOKEN}":
            raise HTTPException(status_code=401, detail="Invalid token")
        if not request_id:
            raise HTTPException(status_code=400, detail="Missing X-Request-Id")
    response = await call_next(request)
    return response

@app.get("/api/health")
async def health_check():
    return {
        "ok": True,
        "time": datetime.utcnow().isoformat() + "Z"
    }

@app.post("/api/mobile/heartbeat", response_model=HeartbeatResponse)
async def heartbeat(request: HeartbeatRequest):
    # Store device state
    device_states[request.deviceId] = {
        "status": request.status,
        "battery": request.battery,
        "last_seen": request.timestamp
    }
    
    # Simple logic: if battery < 20%, ask to sync
    action = "none"
    message = None
    if request.battery < 20:
        action = "sync"
        message = "Low battery - please sync data"
    elif request.status == "idle":
        action = "speak"
        message = "Hello! Ready for next task?"
    
    return HeartbeatResponse(
        intervalMs=60000,  # Poll every 60 seconds
        action=action,
        message=message
    )

@app.post("/api/mobile/event")
async def event(request: EventRequest):
    print(f"[{request.type}] {request.message} - Data: {request.data}")
    return Response(status_code=204)

@app.post("/api/mobile/command")
async def mobile_command(req: MobileCommandRequest, authorization: Optional[str] = Header(None), x_request_id: Optional[str] = Header(None)):
    if not authorization or authorization != f"Bearer {JAI_MOBILE_TOKEN}":
        raise HTTPException(status_code=401, detail="Invalid token")
    rid = x_request_id or str(uuid.uuid4())
    token = request_id_ctx_var.set(rid)
    try:
        username = f"mobile:{req.deviceId}"
        if username not in ja_sessions:
            ja_sessions[username] = JAUserSession(username)
        session = ja_sessions[username]
        desired_lang = jai_detect_language(req.text)
        special = _handle_special_qa(req.text)
        if special is not None:
            result = special
        else:
            result = execute_command(req.text, session, suppress_tts=bool(req.suppressTTS))
        result = _ensure_lang(result, desired_lang)
        return {"response": result, "requestId": rid}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Command execution failed")
    finally:
        try:
            request_id_ctx_var.reset(token)
        except Exception:
            pass

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
        desired_lang = jai_detect_language(req.text)
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

def _handle_special_qa(user_text: str) -> Optional[str]:
    try:
        low = (user_text or "").strip().lower()
        if re.search(r"\bwho\s+(?:created|made|built)\s+(?:you|aj|jai)\b", low):
            return "I was created by Abdul Rehman as a personal AI project, developed without prior professional experience."
        return None
    except Exception:
        return None

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
        desired_lang = jai_detect_language(text) if text else _lang_code_of(lang)
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