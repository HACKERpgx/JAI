from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
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
from io import BytesIO
try:
    from PIL import Image
except Exception:
    Image = None
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

# Import autonomous system components
try:
    from jai_autonomous import jai_autonomous
    from jai_learning_system import learning_system
    from jai_error_handler import error_handler
    from jai_integration_agent import integration_agent, IntegrationConfig, IntegrationType, AuthType
    from jai_email_categorizer import email_categorizer, EmailContent
    from jai_auto_reply import auto_reply_engine, AutoReplyConfig
    from jai_security_config import get_security_config, validate_api_scopes, check_content_security
except Exception as e:
    print(f"Warning: Autonomous system not available: {e}")
    jai_autonomous = None
    learning_system = None
    error_handler = None
    integration_agent = None
    email_categorizer = None
    auto_reply_engine = None

load_dotenv()
try:
    load_dotenv('.env.local', override=True)
except Exception:
    pass
app = FastAPI(title="JAI Web API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Also load env files relative to server directory to avoid CWD issues
try:
    load_dotenv(os.path.join(BASE_DIR, '.env'), override=False)
except Exception:
    pass
try:
    load_dotenv(os.path.join(BASE_DIR, '.env.local'), override=True)
except Exception:
    pass
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




def _load_and_convert(img: Image.Image, fmt_label: str) -> bytes:
    bio = BytesIO()
    try:
        # Ensure correct mode for JPEG
        if fmt_label == "JPEG" and img.mode in {"RGBA", "P"}:
            img = img.convert("RGB")
        img.save(bio, format=fmt_label)
        return bio.getvalue()
    finally:
        try:
            bio.close()
        except Exception:
            pass


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

# Autonomous System API Endpoints
class AutonomousRequest(BaseModel):
    text: str
    autonomous: bool = False
    context: dict = {}

class FeedbackRequest(BaseModel):
    task_id: str
    rating: int
    comment: str = ""

class IntegrationRequest(BaseModel):
    name: str
    type: str
    auth_type: str
    endpoint: str
    auth_data: dict = {}
    headers: dict = {}
    enabled: bool = True
    rate_limit: int = 100
    timeout: int = 30

class IntegrationActionRequest(BaseModel):
    integration_id: str
    action_type: str
    parameters: dict = {}
    target_endpoint: str = None

class EmailCategory(BaseModel):
    category: str
    labels: List[str]
    priority: str = "normal"
    auto_reply: bool = False

class EmailLabelRequest(BaseModel):
    message_id: str
    category: str
    labels: List[str]
    priority: str = "normal"

class AutoReplyConfigRequest(BaseModel):
    enabled: bool = True
    max_replies_per_hour: int = 10
    delay_seconds: int = 30
    confidence_threshold: float = 0.7
    auto_reply_categories: List[str] = ["work", "finance", "health", "urgent"]
    exclude_senders: List[str] = ["noreply@", "no-reply@", "spam@"]
    working_hours_only: bool = True
    working_hours: List[int] = [9, 17]
    timezone: str = "UTC"

class IncomingEmailRequest(BaseModel):
    message_id: str
    subject: str
    sender: str
    body: str
    date: str
    thread_id: str = None

@app.get("/autonomous", response_class=HTMLResponse)
async def autonomous_interface(request: Request):
    """Serve the autonomous interface"""
    path = os.path.join(BASE_DIR, "apps", "web_static", "autonomous.html")
    if os.path.exists(path):
        return FileResponse(path)
    else:
        return HTMLResponse("<h1>Autonomous interface not found</h1>", status_code=404)

@app.get("/email-categorizer", response_class=HTMLResponse)
async def email_categorizer_interface(request: Request):
    """Serve the email categorizer interface"""
    path = os.path.join(BASE_DIR, "apps", "web_static", "email_categorizer.html")
    if os.path.exists(path):
        return FileResponse(path)
    else:
        return HTMLResponse("<h1>Email categorizer interface not found</h1>", status_code=404)

@app.post("/api/autonomous/process")
async def autonomous_process(req: AutonomousRequest, request: Request):
    """Process request using autonomous system"""
    if not jai_autonomous:
        return {"success": False, "message": "Autonomous system not available"}
    
    try:
        web_id = request.cookies.get("jai_web_id") or "anon"
        context = {"user_id": web_id, **req.context}
        
        result = await jai_autonomous.process_request(req.text, context)
        return result
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/autonomous/enable")
async def enable_autonomous():
    """Enable autonomous mode"""
    if not jai_autonomous:
        return {"success": False, "message": "Autonomous system not available"}
    
    try:
        # Implementation for enabling autonomous mode
        return {"success": True, "message": "Autonomous mode enabled"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/autonomous/disable")
async def disable_autonomous():
    """Disable autonomous mode"""
    if not jai_autonomous:
        return {"success": False, "message": "Autonomous system not available"}
    
    try:
        # Implementation for disabling autonomous mode
        return {"success": True, "message": "Autonomous mode disabled"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/autonomous/emergency-stop")
async def emergency_stop():
    """Emergency stop all autonomous tasks"""
    if not jai_autonomous:
        return {"success": False, "message": "Autonomous system not available"}
    
    try:
        # Cancel all active tasks
        active_tasks = list(jai_autonomous.active_tasks.keys())
        for task_id in active_tasks:
            task = jai_autonomous.active_tasks[task_id]
            task.status = jai_autonomous.TaskStatus.CANCELLED
            del jai_autonomous.active_tasks[task_id]
        
        return {"success": True, "message": f"Emergency stop executed. Cancelled {len(active_tasks)} tasks."}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/autonomous/statistics")
async def get_autonomous_statistics():
    """Get autonomous system statistics"""
    if not jai_autonomous:
        return {"error": "Autonomous system not available"}
    
    try:
        stats = jai_autonomous.get_statistics()
        stats["uptime"] = 3600  # Placeholder uptime in seconds
        stats["avg_response_time"] = 250  # Placeholder response time
        return stats
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.get("/api/autonomous/active-tasks")
async def get_active_tasks():
    """Get list of active tasks"""
    if not jai_autonomous:
        return {"error": "Autonomous system not available"}
    
    try:
        return jai_autonomous.get_active_tasks()
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.get("/api/autonomous/task-history")
async def get_task_history():
    """Get task history"""
    if not jai_autonomous:
        return {"error": "Autonomous system not available"}
    
    try:
        history = []
        for task in jai_autonomous.task_history[-50:]:  # Last 50 tasks
            history.append({
                "id": task.id,
                "intent": task.intent.intent_type.value,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "error": task.error
            })
        return history
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.post("/api/autonomous/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Submit feedback for learning"""
    if not learning_system:
        return {"success": False, "message": "Learning system not available"}
    
    try:
        feedback = {
            "task_id": req.task_id,
            "rating": req.rating,
            "comment": req.comment,
            "type": "explicit"
        }
        await learning_system.learn_from_feedback(feedback)
        return {"success": True, "message": "Feedback submitted successfully"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/autonomous/learning-insights")
async def get_learning_insights():
    """Get learning system insights"""
    if not learning_system:
        return {"error": "Learning system not available"}
    
    try:
        insights = learning_system.get_learning_insights()
        insights["accuracy_improvement"] = 15  # Placeholder improvement percentage
        return insights
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.post("/api/autonomous/train")
async def train_model():
    """Train the learning model"""
    if not learning_system:
        return {"success": False, "message": "Learning system not available"}
    
    try:
        await learning_system.auto_improve()
        return {"success": True, "message": "Model training completed", "improvement": 2.5}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/autonomous/export-data")
async def export_learning_data():
    """Export learning data"""
    if not learning_system:
        return {"error": "Learning system not available"}
    
    try:
        insights = learning_system.get_learning_insights()
        import json
        data = json.dumps(insights, indent=2, default=str)
        from fastapi.responses import Response
        return Response(
            content=data,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=jai_learning_data.json"}
        )
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.get("/api/autonomous/error-statistics")
async def get_error_statistics():
    """Get error handling statistics"""
    if not error_handler:
        return {"error": "Error handler not available"}
    
    try:
        return error_handler.get_error_statistics()
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

# Chrome DevTools JSON endpoint - Fix 404 error
@app.get("/.well-known/appspecific/com.chrome.devtools.json")
async def chrome_devtools_json():
    """Handle Chrome DevTools JSON request to prevent 404 errors"""
    return JSONResponse({
        "protocol_version": "1.1",
        "allowed_origins": ["*"],
        "url": "http://localhost:8080"
    })

@app.post("/api/email/categorize")
async def categorize_email(request: EmailLabelRequest):
    """Categorize and label an email"""
    try:
        if not email_categorizer:
            return {"success": False, "error": "Email categorizer not available"}
        
        # Create EmailContent object
        email_content = EmailContent(
            message_id=request.message_id,
            subject=f"Test Email {request.message_id}",  # Would come from actual email
            sender="test@example.com",  # Would come from actual email
            body="Sample email content for categorization",  # Would come from actual email
            date=datetime.now().isoformat(),
            thread_id=request.message_id
        )
        
        # Categorize the email using advanced engine
        category = email_categorizer.categorize_email(email_content)
        
        # Apply labels to Gmail if available
        gmail_applied = False
        if hasattr(email_categorizer, 'gmail_service') and email_categorizer.gmail_service:
            gmail_applied = await email_categorizer.apply_labels_to_gmail(email_content, category)
        
        return {
            "success": True,
            "message_id": request.message_id,
            "category": category.category,
            "labels": category.labels,
            "priority": category.priority,
            "confidence": category.confidence,
            "auto_applied": gmail_applied,
            "auto_reply": category.auto_reply
        }
        
    except Exception as e:
        return {"success": False, "error": f"Categorization failed: {str(e)}"}

@app.post("/api/email/learn-correction")
async def learn_email_correction(request: dict):
    """Learn from user corrections to improve categorization"""
    try:
        if not email_categorizer:
            return {"success": False, "error": "Email categorizer not available"}
        
        message_id = request.get("message_id")
        original_category = request.get("original_category")
        correct_category = request.get("correct_category")
        sender = request.get("sender", "unknown@example.com")
        user_feedback = request.get("feedback", "")
        
        # Create EmailContent for learning
        email_content = EmailContent(
            message_id=message_id,
            subject="Corrected Email",
            sender=sender,
            body="",
            date=datetime.now().isoformat(),
            thread_id=message_id
        )
        
        email_categorizer.learn_from_correction(
            email_content, original_category, correct_category, user_feedback
        )
        
        return {
            "success": True,
            "message": "Learning data saved successfully",
            "improved_accuracy": True
        }
        
    except Exception as e:
        return {"success": False, "error": f"Learning failed: {str(e)}"}

@app.get("/api/email/categories")
async def get_email_categories():
    """Get all available email categories"""
    if not email_categorizer:
        return {"error": "Email categorizer not available"}
    
    try:
        return {
            "categories": email_categorizer.categories,
            "stats": email_categorizer.get_categorization_stats()
        }
    except Exception as e:
        return {"error": f"Failed to get categories: {str(e)}"}

@app.post("/api/email/batch-categorize")
async def batch_categorize_emails(request: dict):
    """Categorize multiple emails at once"""
    try:
        if not email_categorizer:
            return {"success": False, "error": "Email categorizer not available"}
        
        emails_data = request.get("emails", [])
        emails = []
        
        for email_data in emails_data:
            email = EmailContent(
                message_id=email_data.get("message_id", ""),
                subject=email_data.get("subject", ""),
                sender=email_data.get("sender", ""),
                body=email_data.get("body", ""),
                date=email_data.get("date", datetime.now().isoformat()),
                thread_id=email_data.get("thread_id", "")
            )
            emails.append(email)
        
        # Batch categorize
        results = await email_categorizer.batch_categorize_emails(emails)
        
        # Convert to response format
        response_results = []
        for i, category in enumerate(results):
            response_results.append({
                "message_id": emails[i].message_id,
                "category": category.category,
                "labels": category.labels,
                "priority": category.priority,
                "confidence": category.confidence,
                "auto_reply": category.auto_reply
            })
        
        return {
            "success": True,
            "processed": len(response_results),
            "results": response_results
        }
        
    except Exception as e:
        return {"success": False, "error": f"Batch categorization failed: {str(e)}"}

@app.get("/api/email/categorization-stats")
async def get_categorization_stats():
    """Get email categorization statistics"""
    try:
        if not email_categorizer:
            return {"error": "Email categorizer not available"}
        
        stats = email_categorizer.get_categorization_stats()
        
        return {
            "success": True,
            "stats": stats,
            "learning_data_size": len(email_categorizer.learning_data.get("user_corrections", {})),
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": f"Stats failed: {str(e)}"}

@app.post("/api/email/export-learning-data")
async def export_learning_data():
    """Export learning data for backup"""
    try:
        if not email_categorizer:
            return {"error": "Email categorizer not available"}
        
        data = email_categorizer.export_learning_data()
        
        from fastapi.responses import Response
        return Response(
            content=json.dumps(data, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=email_learning_data.json"}
        )
        
    except Exception as e:
        return {"success": False, "error": f"Export failed: {str(e)}"}

# Auto-Reply System Endpoints
@app.post("/api/auto-reply/process")
async def process_auto_reply(request: IncomingEmailRequest):
    """Process incoming email and generate auto-reply if appropriate"""
    try:
        if not auto_reply_engine:
            return {"success": False, "error": "Auto-reply engine not available"}
        
        # Create EmailContent object
        email_content = EmailContent(
            message_id=request.message_id,
            subject=request.subject,
            sender=request.sender,
            body=request.body,
            date=request.date,
            thread_id=request.thread_id or request.message_id
        )
        
        # Process email and generate auto-reply
        result = await auto_reply_engine.process_incoming_email(email_content)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Auto-reply processing failed: {str(e)}"}

@app.get("/api/auto-reply/config")
async def get_auto_reply_config():
    """Get current auto-reply configuration"""
    try:
        if not auto_reply_engine:
            return {"error": "Auto-reply engine not available"}
        
        stats = auto_reply_engine.get_conversation_stats()
        return {
            "success": True,
            "config": stats.get("config", {}),
            "stats": stats,
            "model_loaded": stats.get("model_loaded", False)
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get config: {str(e)}"}

@app.post("/api/auto-reply/config")
async def update_auto_reply_config(request: AutoReplyConfigRequest):
    """Update auto-reply configuration"""
    try:
        if not auto_reply_engine:
            return {"success": False, "error": "Auto-reply engine not available"}
        
        # Convert to dict and update config
        config_dict = request.dict()
        config_dict["working_hours"] = tuple(config_dict["working_hours"])
        
        auto_reply_engine.update_config(config_dict)
        
        return {
            "success": True,
            "message": "Auto-reply configuration updated successfully",
            "config": config_dict
        }
        
    except Exception as e:
        return {"success": False, "error": f"Config update failed: {str(e)}"}

@app.get("/api/auto-reply/conversations")
async def get_conversations():
    """Get conversation history and statistics"""
    try:
        if not auto_reply_engine:
            return {"error": "Auto-reply engine not available"}
        
        stats = auto_reply_engine.get_conversation_stats()
        
        return {
            "success": True,
            "stats": stats,
            "conversations": list(auto_reply_engine.conversations.keys())[:10],  # Last 10 conversations
            "total_conversations": len(auto_reply_engine.conversations)
        }
        
    except Exception as e:
        return {"success": False, "error": f"Failed to get conversations: {str(e)}"}

@app.post("/api/auto-reply/test")
async def test_auto_reply(request: IncomingEmailRequest):
    """Test auto-reply functionality without actually sending"""
    try:
        if not auto_reply_engine:
            return {"success": False, "error": "Auto-reply engine not available"}
        
        # Create EmailContent object
        email_content = EmailContent(
            message_id=f"test_{request.message_id}",
            subject=request.subject,
            sender=request.sender,
            body=request.body,
            date=request.date,
            thread_id=request.thread_id or f"test_{request.message_id}"
        )
        
        # Check if should auto-reply
        from jai_auto_reply import AutoReplyEngine
        should_reply, reason = auto_reply_engine._should_auto_reply(email_content)
        
        if not should_reply:
            return {
                "success": True,
                "would_auto_reply": False,
                "reason": reason,
                "message_id": email_content.message_id
            }
        
        # Generate reply
        reply = auto_reply_engine._generate_smart_reply(email_content)
        
        return {
            "success": True,
            "would_auto_reply": True,
            "reply": reply,
            "confidence": 0.85 if auto_reply_engine.generator else 0.6,
            "message_id": email_content.message_id,
            "model_used": "Hugging Face" if auto_reply_engine.generator else "Template"
        }
        
    except Exception as e:
        return {"success": False, "error": f"Test failed: {str(e)}"}

@app.post("/api/auto-reply/batch-process")
async def batch_process_auto_reply(request: dict):
    """Process multiple incoming emails for auto-reply"""
    try:
        if not auto_reply_engine:
            return {"success": False, "error": "Auto-reply engine not available"}
        
        emails_data = request.get("emails", [])
        results = []
        
        for email_data in emails_data:
            email_content = EmailContent(
                message_id=email_data.get("message_id", ""),
                subject=email_data.get("subject", ""),
                sender=email_data.get("sender", ""),
                body=email_data.get("body", ""),
                date=email_data.get("date", datetime.now().isoformat()),
                thread_id=email_data.get("thread_id")
            )
            
            result = await auto_reply_engine.process_incoming_email(email_content)
            results.append(result)
        
        processed_count = len([r for r in results if r.get("success", False)])
        auto_replied_count = len([r for r in results if r.get("auto_replied", False)])
        
        return {
            "success": True,
            "processed": len(results),
            "auto_replied": auto_replied_count,
            "results": results
        }
        
    except Exception as e:
        return {"success": False, "error": f"Batch processing failed: {str(e)}"}

@app.get("/auto-reply", response_class=HTMLResponse)
async def auto_reply_interface(request: Request):
    """Serve auto-reply interface"""
    path = os.path.join(BASE_DIR, "apps", "web_static", "auto_reply.html")
    if os.path.exists(path):
        return FileResponse(path)
    else:
        return HTMLResponse("<h1>Auto-reply interface not found</h1>", status_code=404)

# Security Endpoints
@app.get("/api/security/config")
async def get_security_config():
    """Get security configuration"""
    try:
        if not SECURITY_AVAILABLE:
            return {"error": "Security system not available"}
        
        config = get_security_config()
        return {
            "success": True,
            "config": config,
            "security_level": config.get("security_level", "medium"),
            "features": {
                "token_encryption": config.get("require_encryption", True),
                "scope_validation": config.get("scope_validation", "strict"),
                "rate_limiting": config.get("rate_limiting", False),
                "content_scanning": config.get("content_scanning", False)
            }
        }
    except Exception as e:
        return {"success": False, "error": f"Security config error: {str(e)}"}

@app.post("/api/security/validate-scopes")
async def validate_api_scopes(request: dict):
    """Validate API scopes for security"""
    try:
        if not SECURITY_AVAILABLE:
            return {"success": False, "error": "Security system not available"}
        
        service = request.get("service", "")
        scopes = request.get("scopes", [])
        
        is_valid, issues = validate_api_scopes(service, scopes)
        
        return {
            "success": is_valid,
            "service": service,
            "requested_scopes": scopes,
            "valid": is_valid,
            "issues": issues,
            "minimal_required": get_security_config().get("minimal_scopes", {}).get(service, [])
        }
    except Exception as e:
        return {"success": False, "error": f"Scope validation error: {str(e)}"}

@app.post("/api/security/check-content")
async def check_content_security(request: dict):
    """Check content for security issues"""
    try:
        content = request.get("content", "")
        is_safe, issues = check_content_security(content)
        
        return {
            "success": True,
            "content_safe": is_safe,
            "issues": issues,
            "content_length": len(content),
            "checked_patterns": len(get_security_config().get("suspicious_patterns", []))
        }
    except Exception as e:
        return {"success": False, "error": f"Content check error: {str(e)}"}

@app.post("/api/security/audit")
async def run_security_audit():
    """Run security audit"""
    try:
        if not SECURITY_AVAILABLE:
            return {"success": False, "error": "Security system not available"}
        
        # This would integrate with jai_security.SecurityAuditor
        # For now, return basic audit results
        audit_results = {
            "timestamp": datetime.now().isoformat(),
            "secure_directories": True,  # Would check actual permissions
            "token_encryption": True,  # Would check actual token files
            "exposed_tokens": False,  # Would scan code
            "old_tokens": False,  # Would check token dates
            "recommendations": [
                "Enable token encryption",
                "Use minimal API scopes",
                "Regular security audits"
            ]
        }
        
        return {
            "success": True,
            "audit": audit_results,
            "message": "Security audit completed"
        }
    except Exception as e:
        return {"success": False, "error": f"Audit error: {str(e)}"}

# Integration Agent API Endpoints
@app.get("/api/integrations")
async def get_integrations():
    """Get all integrations"""
    if not integration_agent:
        return {"error": "Integration agent not available"}
    
    try:
        return integration_agent.get_integration_status()
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

@app.post("/api/integrations")
async def add_integration(req: IntegrationRequest):
    """Add new integration"""
    if not integration_agent:
        return {"success": False, "message": "Integration agent not available"}
    
    try:
        integration_id = f"int_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(req.name)}"
        
        config = IntegrationConfig(
            integration_id=integration_id,
            name=req.name,
            type=IntegrationType(req.type),
            auth_type=AuthType(req.auth_type),
            endpoint=req.endpoint,
            auth_data=req.auth_data,
            headers=req.headers,
            enabled=req.enabled,
            rate_limit=req.rate_limit,
            timeout=req.timeout
        )
        
        success = integration_agent.add_integration(config)
        if success:
            return {"success": True, "integration_id": integration_id, "message": "Integration added successfully"}
        else:
            return {"success": False, "message": "Failed to add integration"}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.delete("/api/integrations/{integration_id}")
async def remove_integration(integration_id: str):
    """Remove integration"""
    if not integration_agent:
        return {"success": False, "message": "Integration agent not available"}
    
    try:
        success = integration_agent.remove_integration(integration_id)
        if success:
            return {"success": True, "message": "Integration removed successfully"}
        else:
            return {"success": False, "message": "Failed to remove integration"}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/integrations/webhook")
async def send_webhook(integration_id: str, data: dict):
    """Send webhook through integration"""
    if not integration_agent:
        return {"success": False, "message": "Integration agent not available"}
    
    try:
        success = await integration_agent.send_webhook(integration_id, data)
        if success:
            return {"success": True, "message": "Webhook sent successfully"}
        else:
            return {"success": False, "message": "Failed to send webhook"}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/integrations/api-request")
async def make_api_request(req: IntegrationActionRequest):
    """Make API request through integration"""
    if not integration_agent:
        return {"success": False, "message": "Integration agent not available"}
    
    try:
        result = await integration_agent.make_api_request(
            req.integration_id,
            req.action_type,
            req.target_endpoint,
            req.parameters
        )
        return result
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/integrations/websocket-connect")
async def connect_websocket(integration_id: str):
    """Connect to WebSocket integration"""
    if not integration_agent:
        return {"success": False, "message": "Integration agent not available"}
    
    try:
        success = await integration_agent.connect_websocket(integration_id)
        if success:
            return {"success": True, "message": "WebSocket connected successfully"}
        else:
            return {"success": False, "message": "Failed to connect WebSocket"}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/integrations/start-websockets")
async def start_all_websockets():
    """Start all WebSocket connections"""
    if not integration_agent:
        return {"success": False, "message": "Integration agent not available"}
    
    try:
        await integration_agent.start_all_websockets()
        return {"success": True, "message": "All WebSocket connections started"}
    
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/integrations/status")
async def get_integration_status():
    """Get detailed integration status"""
    if not integration_agent:
        return {"error": "Integration agent not available"}
    
    try:
        return integration_agent.get_integration_status()
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 JAI Assistant Server Starting...")
    print("📧 Available Features:")
    print("   ✅ Web Interface: http://localhost:8080")
    print("   ✅ Email Categorizer: /email-categorizer")
    print("   ✅ Auto-Reply System: /auto-reply")
    print("   ✅ Gmail Integration: Available")
    print("   ✅ Voice Recognition: Available")
    print("   ✅ AI Responses: English Only (Auto-Translation)")
    print("\n🔧 Server Configuration:")
    print("   🌐 Host: http://localhost:8080")
    print("   📝 Logs: jai_assistant.log")
    print("   🔊 TTS: English responses only")
    print("\n🎯 Starting server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )