from fastapi import FastAPI, HTTPException, Header, Request, Response, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid
import os
from jai_assistant import execute_command, sessions as ja_sessions, UserSession as JAUserSession, request_id_ctx_var
import tempfile
import pathlib
try:
    import speech_recognition as sr
except Exception:
    sr = None

app = FastAPI(title="JAI Mobile API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
JAI_MOBILE_TOKEN = os.environ.get("JAI_MOBILE_TOKEN", "my-super-secret-token-123")
if JAI_MOBILE_TOKEN == "my-super-secret-token-123":
    print("[WARN] Using default JAI_MOBILE_TOKEN; set env JAI_MOBILE_TOKEN for production")

# Store device states (in-memory for simplicity)
device_states = {}

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
        result = execute_command(req.text, session, suppress_tts=bool(req.suppressTTS))
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
        result = execute_command(req.text, session, suppress_tts=True)
        return {"response": result, "requestId": rid}
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
        if sr is None:
            return JSONResponse({"error": "SpeechRecognition not available"}, status_code=400)
        suffix = pathlib.Path(file.filename or "").suffix.lower()
        if suffix not in {".wav", ".flac"}:
            return JSONResponse({"error": "Unsupported audio format. Please upload WAV or FLAC."}, status_code=400)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            data = await file.read()
            tmp.write(data)
            tmp_path = tmp.name
        r = sr.Recognizer()
        try:
            with sr.AudioFile(tmp_path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio, language=lang)
        except Exception:
            text = ""
        web_id = request.cookies.get("jai_web_id") or "anon"
        username = f"web:{web_id}"
        if username not in ja_sessions:
            ja_sessions[username] = JAUserSession(username)
        session = ja_sessions[username]
        if not text:
            return {"transcript": "", "response": "Could not transcribe."}
        result = execute_command(text, session, suppress_tts=True)
        return {"transcript": text, "response": result, "requestId": rid}
    finally:
        try:
            request_id_ctx_var.reset(token)
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)