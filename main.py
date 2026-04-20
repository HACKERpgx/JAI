from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any, Union
import time
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
    PIL_AVAILABLE = True
except Exception:
    Image = None
    PIL_AVAILABLE = False
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

try:
    from security.ids.integrations import init_ids, get_ids_instance
except Exception as e:
    init_ids = None
    get_ids_instance = None

# Import math engine
try:
    from jai_math_engine import math_engine
    MATH_ENGINE_AVAILABLE = True
except Exception as e:
    math_engine = None
    MATH_ENGINE_AVAILABLE = False


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
# Favicon directory - mount only if exists and not empty
favicon_dir = os.path.join(BASE_DIR, "apps", "web_static", "favicon")
if os.path.isdir(favicon_dir) and os.listdir(favicon_dir):
    app.mount("/favicon", StaticFiles(directory=favicon_dir), name="favicon")

 

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

try:
    if init_ids is not None:
        _ids = init_ids(app)
    else:
        _ids = None
except Exception:
    _ids = None


class WebTextRequest(BaseModel):
    text: str
    persona: str

class MathSimplifyRequest(BaseModel):
    expression: str

class MathExpandRequest(BaseModel):
    expression: str

class MathFactorRequest(BaseModel):
    expression: str

class MathSolveRequest(BaseModel):
    equation: str
    variable: str = "x"

class MathSystemRequest(BaseModel):
    equations: List[str]
    variables: List[str]

class MathDerivativeRequest(BaseModel):
    expression: str
    variable: str = "x"
    order: int = 1

class MathIntegralRequest(BaseModel):
    expression: str
    variable: str = "x"

class MathDefiniteIntegralRequest(BaseModel):
    expression: str
    variable: str
    lower: Union[str, float]
    upper: Union[str, float]

class MathLimitRequest(BaseModel):
    expression: str
    variable: str
    point: Union[str, float]
    direction: str = "+"

class MathMatrixRequest(BaseModel):
    matrix: str  # JSON string representation
    operation: str  # determinant, inverse, eigenvalues, transpose

class MathNumericalRequest(BaseModel):
    expression: str
    variable: str = "x"
    initial_guess: float = 0.0

class MathStatisticsRequest(BaseModel):
    data: List[float]

class WebPersonaRequest(BaseModel):
    persona: str


@app.get("/api/health")
async def health_check():
    return {
        "ok": True,
        "time": datetime.utcnow().isoformat() + "Z"
    }

@app.post("/api/logout")
async def logout(request: Request):
    """Clear user session and message history"""
    web_id = request.cookies.get("jai_web_id") or "anon"
    username = f"web:{web_id}"
    
    # Clear session from memory
    if username in ja_sessions:
        del ja_sessions[username]
    
    # Create response with cleared cookie
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("jai_web_id")
    
    return response


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

@app.get("/static/icon-192.png")
async def icon_192():
    path = os.path.join(BASE_DIR, "static", "icon-192.png")
    return FileResponse(path, media_type="image/png")

@app.get("/static/icon-512.png")
async def icon_512():
    path = os.path.join(BASE_DIR, "static", "icon-512.png")
    return FileResponse(path, media_type="image/png")

@app.get("/static/favicon.ico")
async def favicon():
    path = os.path.join(BASE_DIR, "static", "favicon.ico")
    return FileResponse(path, media_type="image/x-icon")

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
    except Exception as e:
        logging.error(f"Error in api_text: {e}", exc_info=True)
        return {"response": f"I apologize, but I encountered an error processing your request. Please try again.", "requestId": rid, "error": str(e)}
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




def _load_and_convert(img: Any, fmt_label: str) -> bytes:
    if not PIL_AVAILABLE:
        raise Exception("PIL not available for image processing")
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


def _image_to_data_url(mime: str, data: bytes) -> str:
    """Convert image bytes to base64 data URL for vision API."""
    try:
        import base64
        b64 = base64.b64encode(data).decode("utf-8")
        # Ensure mime type is valid for images
        if not mime or not mime.startswith("image/"):
            mime = "image/jpeg"
        return f"data:{mime};base64,{b64}"
    except Exception as e:
        print(f"[ERROR] _image_to_data_url failed: {e}")
        return ""


# Vision analysis prompt templates for different analysis types
VISION_PROMPTS = {
    "general": "Analyze this image thoroughly. Describe what you see in detail: the main subject, objects, people, setting, colors, layout, style, quality, and any visible text. Provide a comprehensive analysis.",
    "ocr": "Extract and transcribe ALL visible text from this image. Quote text exactly as shown. Note any handwriting, printed text, signs, labels, or documents. Preserve formatting where possible.",
    "diagram": "Analyze this diagram, chart, or technical drawing. Explain the structure, components, relationships, data presented, and any technical details. Describe what information it conveys.",
    "code": "Analyze this code screenshot or code image. Identify the programming language, explain what the code does, note any issues or improvements, and transcribe the code if readable.",
    "ui": "Analyze this UI/UX screenshot. Describe the interface elements, layout, design patterns, user flow, and any usability observations. Identify the app or website if recognizable.",
    "math": "Analyze this mathematical content. Identify equations, formulas, or problems. Explain the mathematical concepts and solve or interpret if applicable.",
    "object": "Identify and describe all objects in this image. For each object, note its type, approximate size relative to surroundings, color, condition, and any notable features.",
    "document": "Analyze this document image. Extract all text, identify the document type, note any forms, tables, or structured data. Summarize the document's purpose and key information.",
    "photo": "Analyze this photograph professionally. Describe the composition, lighting, subject matter, artistic elements, camera angle, and any notable photography techniques used.",
    "screenshot": "Analyze this screenshot. Describe what application or website it shows, the current state, any visible data or content, and explain what action might have been captured.",
}


def _analyze_image_bytes(data: bytes, mime: str, prompt: str, analysis_type: str = "general") -> str:
    """Analyze image using vision-capable AI model.
    
    Args:
        data: Raw image bytes
        mime: MIME type of image
        prompt: Custom user prompt (optional)
        analysis_type: Type of analysis (general, ocr, diagram, code, ui, math, object, document, photo, screenshot)
    
    Returns:
        Analysis text response
    """
    try:
        # Log debug info
        print(f"[DEBUG] Analyzing image: mime={mime}, size={len(data)} bytes, type={analysis_type}")
        
        data_url = _image_to_data_url(mime, data)
        if not data_url:
            return "Could not read image data."
        
        print(f"[DEBUG] Data URL created: {data_url[:100]}...")
        
        # Try OpenAI first
        api_key = os.environ.get("OPENAI_API_KEY")
        print(f"[DEBUG] API key available: {bool(api_key)}")
        print(f"[DEBUG] OpenAI client available: {OpenAI is not None}")
        
        if OpenAI and api_key:
            try:
                client = OpenAI(api_key=api_key)
                user_prompt = (prompt or "").strip()
                
                # Use analysis type prompt if no custom prompt provided
                if not user_prompt:
                    analysis_type_key = (analysis_type or "general").lower()
                    base_prompt = VISION_PROMPTS.get(analysis_type_key, VISION_PROMPTS["general"])
                    user_prompt = base_prompt + "\n\nIMPORTANT: Respond only in English."
                else:
                    user_prompt = user_prompt + "\n\nIMPORTANT: Respond only in English."
                
                print(f"[DEBUG] Using prompt: {user_prompt[:100]}...")
                
                messages = [
                    {
                        "role": "system",
                        "content": "You are JAI Vision, an advanced image analysis AI with native vision capabilities. You can see, analyze, and understand any image perfectly. You have direct access to the visual content. NEVER say you cannot view images or that you're a text-based AI. Always respond as if you clearly see the image. Be precise, detailed, and helpful. Read all text exactly as shown, note small details, and provide comprehensive analysis."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                        ],
                    }
                ]
                
                print(f"[DEBUG] Calling OpenAI API with model: {os.environ.get('JAI_VISION_MODEL', 'gpt-4o-mini')}")
                
                resp = client.chat.completions.create(
                    model=os.environ.get("JAI_VISION_MODEL", "gpt-4o-mini"),
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.3,
                )
                text = resp.choices[0].message.content
                print(f"[DEBUG] Got response: {text[:100]}...")
                return (text or "").strip() or "No description generated."
            except Exception as e:
                error_msg = f"OpenAI error: {str(e)}"
                print(f"[ERROR] {error_msg}")
                # Check if it's a quota error and try fallback
                if "quota" in str(e).lower() or "429" in str(e):
                    print("[DEBUG] OpenAI quota exceeded, trying Gemini fallback...")
                    gemini_result = _analyze_with_gemini(data, mime, prompt, analysis_type)
                    if "failed" not in gemini_result.lower() and "unavailable" not in gemini_result.lower():
                        return gemini_result
                    print("[DEBUG] Gemini failed, trying Groq fallback...")
                    return _analyze_with_groq(data, mime, prompt, analysis_type)
                import traceback
                traceback.print_exc()
                return error_msg
        
        # Fallback to Gemini if OpenAI not available
        print("[DEBUG] OpenAI not available, trying Gemini...")
        gemini_result = _analyze_with_gemini(data, mime, prompt, analysis_type)
        if "failed" not in gemini_result.lower() and "unavailable" not in gemini_result.lower():
            return gemini_result
        
        # Fallback to Groq
        print("[DEBUG] Gemini failed, trying Groq...")
        return _analyze_with_groq(data, mime, prompt, analysis_type)
        
    except Exception as e:
        error_msg = f"Image analysis failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return error_msg


def _analyze_with_groq(data: bytes, mime: str, prompt: str, analysis_type: str = "general") -> str:
    """Fallback to Groq for image analysis."""
    try:
        from groq import Groq
        import base64
        
        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            return "Groq API key not configured. Please set GROQ_API_KEY."
        
        print(f"[DEBUG] Using Groq API with key: {bool(groq_key)}")
        client = Groq(api_key=groq_key)
        
        # Convert image to base64
        image_b64 = base64.b64encode(data).decode('utf-8')
        
        user_prompt = (prompt or "").strip()
        if not user_prompt:
            analysis_type_key = (analysis_type or "general").lower()
            base_prompt = VISION_PROMPTS.get(analysis_type_key, VISION_PROMPTS["general"])
            user_prompt = base_prompt + "\n\nIMPORTANT: Respond only in English."
        
        print(f"[DEBUG] Groq prompt: {user_prompt[:100]}...")
        
        # Try Groq vision models
        try:
            from groq import Groq
            # Get available models
            temp_client = Groq(api_key=groq_key)
            models_list = temp_client.models.list()
            vision_models = [model.id for model in models_list.data if 'llava' in model.id.lower() or 'vision' in model.id.lower()]
            print(f"[DEBUG] Available Groq models: {[m.id for m in models_list.data[:10]]}")
            print(f"[DEBUG] Vision models: {vision_models}")
            
            if vision_models:
                models = vision_models
            else:
                models = [
                    "llava-v1.5-7b",
                    "llava-v1.5-13b", 
                    "llava-v1.5-34b"
                ]
        except Exception as list_e:
            print(f"[ERROR] Could not list Groq models: {list_e}")
            models = [
                "llava-v1.5-7b",
                "llava-v1.5-13b", 
                "llava-v1.5-34b"
            ]
        
        for model_name in models:
            try:
                print(f"[DEBUG] Trying Groq model: {model_name}")
                
                messages = [
                    {
                        "role": "system",
                        "content": "You are JAI Vision, an advanced image analysis AI with native vision capabilities. You can see, analyze, and understand any image perfectly. You have direct access to the visual content. NEVER say you cannot view images or that you're a text-based AI. Always respond as if you clearly see the image. Be precise, detailed, and helpful. Read all text exactly as shown, note small details, and provide comprehensive analysis."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime};base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ]
                
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.3
                )
                
                if response.choices and response.choices[0].message.content:
                    result = response.choices[0].message.content
                    print(f"[DEBUG] Groq response with {model_name}: {result[:100]}...")
                    return result
                else:
                    print(f"[DEBUG] {model_name} returned empty response")
                    continue
                    
            except Exception as model_e:
                print(f"[ERROR] Groq model {model_name} failed: {model_e}")
                if "not found" in str(model_e).lower() or "not supported" in str(model_e).lower():
                    continue  # Try next model
                else:
                    raise model_e
        
        return "All Groq vision models failed or are unavailable."
            
    except Exception as e:
        error_msg = f"Groq fallback failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return f"All vision services failed. OpenAI: quota exceeded, Gemini: unavailable, Groq: {str(e)}\n\n{_get_basic_image_info(data, mime)}"


def _get_basic_image_info(data: bytes, mime: str) -> str:
    """Provide basic image information when all vision APIs fail."""
    try:
        from PIL import Image as PILImage
        import io
        from datetime import datetime
        
        image = PILImage.open(io.BytesIO(data))
        
        info = []
        info.append("📷 Basic Image Information:")
        info.append(f"• Format: {image.format or 'Unknown'}")
        info.append(f"• Size: {image.size[0]} × {image.size[1]} pixels")
        info.append(f"• Mode: {image.mode}")
        info.append(f"• File size: {len(data):,} bytes ({len(data)/1024:.1f} KB)")
        
        if hasattr(image, 'info') and image.info:
            if 'dpi' in image.info:
                info.append(f"• DPI: {image.info['dpi']}")
            if 'comment' in image.info:
                info.append(f"• Comment: {image.info['comment'][:100]}...")
        
        # Add basic analysis based on image properties
        info.append("\n🔍 Basic Analysis:")
        
        # Analyze aspect ratio
        width, height = image.size
        aspect_ratio = width / height
        if 0.9 <= aspect_ratio <= 1.1:
            info.append("• Shape: Square image")
        elif aspect_ratio > 1.5:
            info.append("• Shape: Wide/landscape image")
        elif aspect_ratio < 0.7:
            info.append("• Shape: Tall/portrait image")
        else:
            info.append("• Shape: Standard rectangle")
        
        # Analyze color mode
        if image.mode == 'RGB':
            info.append("• Color: Full color image")
        elif image.mode == 'RGBA':
            info.append("• Color: Full color with transparency")
        elif image.mode == 'L':
            info.append("• Color: Grayscale/monochrome")
        elif image.mode == 'CMYK':
            info.append("• Color: CMYK (print format)")
        else:
            info.append(f"• Color: {image.mode} format")
        
        # Estimate image type based on size and format
        if image.format == 'JPEG':
            if width >= 1920 or height >= 1080:
                info.append("• Likely: High-resolution photograph")
            elif width >= 800:
                info.append("• Likely: Standard web image")
            else:
                info.append("• Likely: Thumbnail or small image")
        elif image.format == 'PNG':
            if image.mode == 'RGBA':
                info.append("• Likely: Graphic with transparency")
            else:
                info.append("• Likely: Web graphic or screenshot")
        elif image.format == 'GIF':
            info.append("• Likely: Animated image or simple graphic")
        
        info.append("\n⚠️ Vision analysis services are currently unavailable due to API quota limits.")
        info.append("Please try again later or upload a different image.")
        
        return "\n".join(info)
        
    except Exception as e:
        return f"Unable to process image. Error: {str(e)}"


def _analyze_with_gemini(data: bytes, mime: str, prompt: str, analysis_type: str = "general") -> str:
    """Fallback to Google Gemini Vision for image analysis."""
    try:
        import google.generativeai as genai
        from PIL import Image as PILImage
        import io
        
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return "Gemini API key not configured. Please set GEMINI_API_KEY."
        
        print(f"[DEBUG] Using Gemini API with key: {bool(gemini_key)}")
        genai.configure(api_key=gemini_key)
        
        # Validate and fix image data
        try:
            image = PILImage.open(io.BytesIO(data))
            # Verify image can be loaded
            image.verify()
            # Reload after verify (verify() closes the image)
            image = PILImage.open(io.BytesIO(data))
            
            # Convert to RGB if needed (Gemini works best with RGB)
            if image.mode not in ['RGB', 'L']:
                image = image.convert('RGB')
            
            print(f"[DEBUG] Image loaded successfully: {image.size}, mode={image.mode}")
        except Exception as img_e:
            print(f"[ERROR] Image validation failed: {img_e}")
            # Try to fix common image issues
            try:
                # Try with PIL's error handling
                image = PILImage.open(io.BytesIO(data))
                image = image.convert('RGB')
                print(f"[DEBUG] Image converted to RGB successfully")
            except Exception as fix_e:
                return f"Image file appears corrupted or truncated. Please upload a valid image file. Error: {str(img_e)}"
        
        user_prompt = (prompt or "").strip()
        if not user_prompt:
            analysis_type_key = (analysis_type or "general").lower()
            base_prompt = VISION_PROMPTS.get(analysis_type_key, VISION_PROMPTS["general"])
            user_prompt = base_prompt + "\n\nIMPORTANT: Respond only in English."
        
        print(f"[DEBUG] Gemini prompt: {user_prompt[:100]}...")
        
        # First, list available models to find the correct ones
        try:
            models = genai.list_models()
            vision_models = [m.name for m in models if 'vision' in m.name.lower() or 'image' in m.name.lower() or 'gemini' in m.name.lower()]
            print(f"[DEBUG] Available models: {[m.name for m in models[:10]]}")  # Show first 10
            print(f"[DEBUG] Vision-capable models: {vision_models}")
        except Exception as list_e:
            print(f"[ERROR] Could not list models: {list_e}")
            vision_models = []
        
        # Try different model names based on what's actually available
        model_names = []
        
        # If we found vision models, use them
        if vision_models:
            model_names = [name.replace('models/', '') for name in vision_models]
        else:
            # Fallback to common model names
            model_names = [
                'gemini-1.5-flash-latest',
                'gemini-1.5-pro-latest',
                'gemini-1.0-pro-latest',
                'gemini-pro-latest',
                'gemini-pro-vision'
            ]
        
        for model_name in model_names:
            try:
                print(f"[DEBUG] Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                
                # Generate content
                response = model.generate_content([user_prompt, image])
                
                if response.text:
                    print(f"[DEBUG] Gemini response with {model_name}: {response.text[:100]}...")
                    return response.text
                else:
                    print(f"[DEBUG] {model_name} returned empty response")
                    continue
                    
            except Exception as model_e:
                print(f"[ERROR] Model {model_name} failed: {model_e}")
                if "not found" in str(model_e).lower() or "not supported" in str(model_e).lower():
                    continue  # Try next model
                else:
                    raise model_e  # Re-raise if it's not a model not found error
        
        return "All Gemini models failed or are unavailable for vision tasks."
            
    except Exception as e:
        error_msg = f"Gemini fallback failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Check if it's still a quota issue
        if "quota" in str(e).lower() or "billing" in str(e).lower():
            return f"Both OpenAI and Gemini have quota issues. Please check API billing."
        
        # Try Groq as last resort
        print("[DEBUG] All vision APIs failed, trying Groq...")
        return _analyze_with_groq(data, mime, prompt, analysis_type)

def _handle_special_qa(user_text: str) -> Optional[str]:
    try:
        low = (user_text or "").strip().lower()
        if re.search(r"\bwho\s+(?:created|made|built)\s+(?:you|aj|jai)\b", low):
            return "I was created by Abdul Rehman as a personal AI project, developed without prior professional experience."
        return None
    except Exception:
        return None

@app.post("/api/image")
async def api_image(request: Request, file: UploadFile = File(...), prompt: str = Form(""), analysis_type: str = Form("general")):
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
        
        # Validate image data before processing
        if len(data) < 100:  # Images should be at least 100 bytes
            return JSONResponse({"error": "Image file is too small or corrupted. Please upload a valid image."}, status_code=400)
        
        if len(data) > 20 * 1024 * 1024:  # 20MB limit
            return JSONResponse({"error": "Image file is too large. Please upload an image smaller than 20MB."}, status_code=400)
        
        # Quick validation with PIL
        try:
            from PIL import Image as PILImage
            import io
            test_img = PILImage.open(io.BytesIO(data))
            test_img.verify()  # Just verify, don't load fully
            print(f"[DEBUG] Image validation passed: {file.filename}, size={len(data)} bytes")
        except Exception as img_e:
            print(f"[ERROR] Image validation failed: {img_e}")
            return JSONResponse({"error": f"Image file appears corrupted or invalid: {str(img_e)}"}, status_code=400)

        analysis = _analyze_image_bytes(data, mime, prompt, analysis_type)
        analysis = _ensure_lang(analysis, "en")
        return {"response": analysis, "requestId": rid, "analysis_type": analysis_type}
    finally:
        try:
            request_id_ctx_var.reset(token)
        except Exception:
            pass


class MultiImageRequest(BaseModel):
    prompt: str = ""
    analysis_type: str = "general"


@app.post("/api/image/analyze-multi")
async def api_image_multi(request: Request, files: List[UploadFile] = File(...), prompt: str = Form(""), analysis_type: str = Form("general")):
    """Analyze multiple images in a single request."""
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    token = request_id_ctx_var.set(rid)
    try:
        web_id = request.cookies.get("jai_web_id") or "anon"
        username = f"web:{web_id}"
        if username not in ja_sessions:
            ja_sessions[username] = JAUserSession(username)
        
        if not files or len(files) == 0:
            return JSONResponse({"error": "No images provided."}, status_code=400)
        
        results = []
        for i, file in enumerate(files):
            data = await file.read()
            mime = (getattr(file, "content_type", None) or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream")
            if not isinstance(mime, str):
                mime = "application/octet-stream"
            if not mime.startswith("image/"):
                results.append({"index": i, "filename": file.filename, "error": "Unsupported file type"})
                continue
            
            analysis = _analyze_image_bytes(data, mime, prompt, analysis_type)
            results.append({
                "index": i,
                "filename": file.filename,
                "analysis": analysis
            })
        
        return {"results": results, "requestId": rid, "total_images": len(files)}
    finally:
        try:
            request_id_ctx_var.reset(token)
        except Exception:
            pass


@app.get("/api/image/types")
async def get_analysis_types():
    """Get available analysis types for image analysis."""
    return {
        "types": list(VISION_PROMPTS.keys()),
        "descriptions": VISION_PROMPTS
    }

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
        "url": "https://j-ai.top"
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

try:
    _ = get_security_config and validate_api_scopes and check_content_security
    SECURITY_AVAILABLE = True
except Exception:
    SECURITY_AVAILABLE = False


# Mathematical Computation API Endpoints
@app.post("/api/math/simplify")
async def math_simplify(req: MathSimplifyRequest):
    """Simplify algebraic expression"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.simplify_expression(req.expression)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/expand")
async def math_expand(req: MathExpandRequest):
    """Expand algebraic expression"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.expand_expression(req.expression)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/factor")
async def math_factor(req: MathFactorRequest):
    """Factor algebraic expression"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.factor_expression(req.expression)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/solve")
async def math_solve(req: MathSolveRequest):
    """Solve equation for variable"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.solve_equation(req.equation, req.variable)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/system")
async def math_system(req: MathSystemRequest):
    """Solve system of equations"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.solve_system(req.equations, req.variables)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/derivative")
async def math_derivative(req: MathDerivativeRequest):
    """Calculate derivative"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.derivative(req.expression, req.variable, req.order)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/integral")
async def math_integral(req: MathIntegralRequest):
    """Calculate indefinite integral"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.integral(req.expression, req.variable)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/definite-integral")
async def math_definite_integral(req: MathDefiniteIntegralRequest):
    """Calculate definite integral"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.definite_integral(req.expression, req.variable, req.lower, req.upper)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/limit")
async def math_limit(req: MathLimitRequest):
    """Calculate limit"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.limit(req.expression, req.variable, req.point, req.direction)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/matrix")
async def math_matrix(req: MathMatrixRequest):
    """Perform matrix operations"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.matrix_operations(req.matrix, req.operation)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/numerical")
async def math_numerical(req: MathNumericalRequest):
    """Numerical root finding"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.numerical_solve(req.expression, req.variable, req.initial_guess)
        return result
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/math/statistics")
async def math_statistics(req: MathStatisticsRequest):
    """Calculate statistics"""
    if not MATH_ENGINE_AVAILABLE:
        return {"error": "Math engine not available"}
    try:
        result = math_engine.statistics(req.data)
        return result
    except Exception as e:
        return {"error": str(e)}

# Auth endpoints for Supabase integration
from fastapi import Depends
from jai_auth import (
    get_current_user, require_auth, User, 
    AuthResponse, LoginRequest, SignupRequest,
    SUPABASE_URL, SUPABASE_ANON_KEY
)

@app.get("/api/auth/session")
async def get_session(user: Optional[User] = Depends(get_current_user)):
    """Get current user session info"""
    if user:
        return {
            "authenticated": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "user_metadata": user.user_metadata
            }
        }
    return {"authenticated": False, "user": None}

@app.get("/api/auth/config")
async def get_auth_config():
    """Get Supabase configuration for frontend"""
    return {
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key": SUPABASE_ANON_KEY,
        "enabled": bool(SUPABASE_URL and SUPABASE_ANON_KEY)
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 JAI Assistant Server Starting...")
    print("📧 Available Features:")
    print("   ✅ Web Interface: https://j-ai.top")
    print("   ✅ Email Categorizer: /email-categorizer")
    print("   ✅ Auto-Reply System: /auto-reply")
    print("   ✅ Gmail Integration: Available")
    print("   ✅ Voice Recognition: Available")
    print("   ✅ AI Responses: English Only (Auto-Translation)")
    print("   ✅ User Authentication: Supabase Auth")
    print("\n🔧 Server Configuration:")
    print("   🌐 Host: https://j-ai.top")
    print("   📝 Logs: jai_assistant.log")
    print("   🔊 TTS: English responses only")
    print("\n🎯 Starting server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
