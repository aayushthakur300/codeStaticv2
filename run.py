import sys
import traceback
import os
import json
import time
import io
import random
import string
import datetime
import pymysql
import pymysql.cursors
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Optional, Any

# Third-party imports
from dotenv import load_dotenv
import google.generativeai as genai
from fpdf import FPDF, XPos, YPos

# FastAPI & Core Utilities
from fastapi import FastAPI, Request, HTTPException, Depends, Form, BackgroundTasks, status
from fastapi.responses import JSONResponse, Response, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

# Security & Auth Libraries
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.microsoft import MicrosoftSSO
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

# --- 💀 GLOBAL CRASH HANDLER (RENDER SAFE) ---
def crash_handler(exctype, value, tb):
    print("\n\n" + "="*60)
    print("💀 FATAL ERROR: SYSTEM CRASHED!")
    print("="*60)
    traceback.print_exception(exctype, value, tb)
    print("="*60)
    # NOTE: input() is removed because it freezes Cloud Servers

sys.excepthook = crash_handler
print("🚀 [SYSTEM] Initializing CodeStatic AI SaaS Backend...")

# ----------------------------------
# 1. LOAD CONFIGURATION
# ----------------------------------
load_dotenv()
print("✅ [CHECKPOINT] Environment Variables Loaded")

# --- DATABASE CONFIG (AIVEN / CLOUD READY) ---
# Ensure these match your Render Environment Variables exactly
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DB", "defaultdb")
DB_PORT = int(os.getenv("DB_PORT", 3306)) # Aiven usually uses a different port like 12345

# --- EMAIL CONFIG (SSL MODE FOR RENDER) ---
# CRITICAL: We use Port 465 (SSL) instead of 587 (TLS) to avoid timeouts on Render
mail_conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"), # MUST be a Google App Password
    MAIL_FROM=os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME")),
    MAIL_PORT=465,        # SSL Port
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=False,  # Turn OFF TLS for Port 465
    MAIL_SSL_TLS=True,    # Turn ON SSL for Port 465
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# --- AI CONFIG ---
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

MODEL_ROSTER = [
     # --- TIER 1: HIGH SPEED & STABLE FLASH ---
    'models/gemini-2.0-flash',
    'models/gemini-2.0-flash-001',
    'models/gemini-flash-latest',
    'models/gemini-flash-lite-latest',
    'models/gemini-2.5-flash',
    'models/gemini-2.5-flash-lite',
    'models/gemini-robotics-er-1.5-preview',

    # --- TIER 2: 1.5 FLASH SERIES ---
    'models/gemini-1.5-flash',
    'models/gemini-1.5-flash-latest',
    'models/gemini-1.5-flash-001',
    'models/gemini-1.5-flash-002',
    'models/gemini-1.5-flash-8b',
    'models/gemini-1.5-flash-8b-latest',
    'models/gemini-1.5-flash-8b-001',
    
    # --- TIER 3: 1.5 PRO SERIES ---
    'models/gemini-1.5-pro',
    'models/gemini-1.5-pro-latest',
    'models/gemini-1.5-pro-001',
    'models/gemini-1.5-pro-002',
    
    # --- TIER 5: LEGACY 1.0 PRO SERIES ---
    'models/gemini-1.0-pro',
    'models/gemini-1.0-pro-latest',
    'models/gemini-1.0-pro-001',
    'models/gemini-pro',
    'models/gemini-pro-vision', # Text compatible
    
    # --- TIER 2: NEXT GEN (2.5) ---
    'models/gemini-2.5-flash-preview-09-2025',
    'models/gemini-2.5-flash-lite-preview-09-2025',
    'models/gemini-2.5-flash-tts',

    # --- TIER 3: HIGH INTELLIGENCE PRO MODELS ---
    'models/gemini-2.5-pro',
    'models/gemini-pro-latest',
    'models/gemini-3-pro-preview',
    'models/deep-research-pro-preview-12-2025',

    # --- TIER 4: LIGHTWEIGHT / PREVIEW ---
    'models/gemini-2.0-flash-lite',
    'models/gemini-2.0-flash-lite-001',
    'models/gemini-2.0-flash-lite-preview',
    'models/gemini-2.0-flash-lite-preview-02-05',

    # --- TIER 5: EXPERIMENTAL ---
    'models/gemini-2.0-flash-exp',
    'models/gemini-exp-1206',

    # --- TIER 6: GEMMA (OPEN MODELS FALLBACK) ---
    'models/gemma-3-27b-it',
    'models/gemma-3-12b-it',
    'models/gemma-3-4b-it',
    'models/gemma-3-1b-it',
    'models/gemma-3n-e4b-it',
    'models/gemma-3n-e2b-it',

    # --- TIER 6: GEMMA & OPEN MODELS ---
    'models/gemma-2-27b-it',
    'models/gemma-2-9b-it',
    'models/gemma-2-2b-it',
    
    # --- TIER 7: OBSCURE PREVIEWS (LAST RESORT) ---
    'models/gemini-2.5-flash-native-audio-dialog',
    'models/nano-banana-pro-preview'
     
    # --- TIER 7: OBSCURE / LAST RESORT ---
    'models/aqa'
]

# --- OAUTH CONFIG ---
# Ensure "Authorized redirect URIs" in Google Console matches your Render URL
# e.g., https://your-app-name.onrender.com/auth/google/callback
google_sso = GoogleSSO(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
    allow_insecure_http=True 
)

microsoft_sso = MicrosoftSSO(
    client_id=os.getenv("MS_CLIENT_ID"),
    client_secret=os.getenv("MS_CLIENT_SECRET"),
    redirect_uri=os.getenv("MS_REDIRECT_URI"),
    allow_insecure_http=True
)

# ----------------------------------
# 2. SETUP FASTAPI APP
# ----------------------------------
app = FastAPI(title="CodeStatic AI (Enterprise SaaS)")

# Middleware
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET", "super-secret-key-change-me"),
    https_only=False, # Render handles SSL termination
    max_age=30*24*60*60,
    same_site="lax"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "templates")), name="static")

# Mock Analysis Engine if missing
try:
    from analysis_engine import analyzer
    print("✅ [CHECKPOINT] Analysis Engine Loaded Successfully")
except ImportError:
    print("⚠️ [WARNING] analysis_engine.py not found! Using Mock Fallback.")
    class MockAnalyzer:
        def analyze(self, c, l): return {"quality_score": 0, "error_table": [], "complexity": {}}
    analyzer = MockAnalyzer()

# ----------------------------------
# 3. DATABASE HELPERS (AIVEN SSL FIX)
# ----------------------------------
def get_connection():
    """Creates a fresh connection to MySQL with SSL for Aiven Support"""
    try:
        # Create a permissive SSL context 
        # (Required for Cloud DBs to accept the connection)
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        return pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=20,    # Increased timeout for cloud latency
            ssl=ssl_ctx            # Inject SSL Context
        )
    except Exception as e:
        print(f"\n💀 [FATAL] Database Connection Failed!")
        print(f"   Error: {e}")
        print(f"   Target: {DB_HOST}:{DB_PORT}")
        raise e

def init_db():
    print("⏳ [INIT] Verifying Database Connection...")
    try:
        conn = get_connection()
        conn.close()
        print("✅ [INIT] Database Connected Successfully.")
    except Exception as e:
        print(f"❌ [INIT] Database Error: {e}")

init_db()

def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

# ----------------------------------
# 4. PYDANTIC MODELS
# ----------------------------------
class CodeData(BaseModel):
    code: str
    language: str

class ProjectData(BaseModel):
    projectName: str
    code: str
    language: str

class FavoriteData(BaseModel):
    id: int
    fav: bool | int

class DeleteData(BaseModel):
    id: int

class ChatData(BaseModel):
    message: str
    code_context: Optional[str] = ""

class FeedbackData(BaseModel):
    message: str
    rating: int
    name: Optional[str] = "Anonymous"

class ProcessCodeData(BaseModel):
    code: str
    target_lang: str
    candidate_id: Optional[str] = "N/A"
    is_ci_build: Optional[bool] = False 

class ReportData(BaseModel):
    target_lang: Optional[str] = "N/A"
    quality_score: Optional[Any] = 0
    compliance_status: Optional[str] = "N/A"
    integrity_check: Optional[str] = "N/A"
    plagiarism_check: Optional[str] = "N/A"
    original_code: Optional[str] = ""
    final_code: Optional[str] = ""
    error_log_text: Optional[str] = ""
    time_analysis: Optional[str] = ""
    space_analysis: Optional[str] = ""
    explanation_text: Optional[str] = ""
    class Config:
        extra = "allow"

# ----------------------------------
# 5. PDF GENERATOR
# ----------------------------------
class CodeReportPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(220, 53, 69)
        self.cell(0, 15, 'CodeStatic Evaluation Report', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C', fill=True)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} | Generated by CodeStatic AI', 0, new_x=XPos.RIGHT, new_y=YPos.TOP, align='C')

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(0, 0, 0)
        self.set_fill_color(240, 240, 240)
        title = self.sanitize_text(title) 
        self.cell(0, 8, f"  {title}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L', fill=True)
        self.ln(4)

    def status_field(self, label, value):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(50, 50, 50)
        self.cell(45, 6, label, 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        val_str = self.sanitize_text(str(value) if value is not None else "")
        self.multi_cell(0, 6, val_str, 0, align='L')
        self.ln(2)

    def code_block(self, code_text):
        self.set_font('Courier', '', 9)
        self.set_fill_color(250, 250, 250)
        self.set_draw_color(200, 200, 200)
        text = self.sanitize_text(str(code_text))
        self.multi_cell(0, 5, text, border=1, align='L', fill=True)
        self.ln(5)

    def sanitize_text(self, text):
        return text.encode('latin-1', 'replace').decode('latin-1')

# ----------------------------------
# 6. AUTH & EMAIL LOGIC (CRITICAL FIXES)
# ----------------------------------

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not Authenticated")
    return user

async def send_otp_email(email: str, otp: str):
    """Sends OTP using SSL (Port 465)"""
    print(f"📧 [EMAIL] Sending OTP to {email}...")
    try:
        message = MessageSchema(
            subject="CodeStatic Verification Code",
            recipients=[email],
            body=f"""
            Your Login Code is: {otp}
            
            This code expires in 10 minutes.
            """,
            subtype=MessageType.plain
        )
        fm = FastMail(mail_conf)
        await fm.send_message(message)
        print(f"✅ [EMAIL] OTP sent to {email}")
    except Exception as e:
        print(f"💀 [EMAIL ERROR]: {e}")
        # Traceback helps debug connection issues
        traceback.print_exc()

async def send_admin_feedback(user_email: str, rating: int, feedback_msg: str):
    """Sends Feedback to Admin (YOU)"""
    admin_email = os.getenv("MAIL_USERNAME") 
    print(f"📧 [EMAIL] Sending Feedback to Admin ({admin_email})...")
    
    html_body = f"""
    <h3>🚀 New User Feedback</h3>
    <p><strong>User:</strong> {user_email}</p>
    <p><strong>Rating:</strong> {rating} / 5</p>
    <hr>
    <p><strong>Message:</strong></p>
    <blockquote>{feedback_msg}</blockquote>
    """
    
    try:
        message = MessageSchema(
            subject=f"📢 Feedback from {user_email}",
            recipients=[admin_email],
            body=html_body,
            subtype=MessageType.html
        )
        fm = FastMail(mail_conf)
        await fm.send_message(message)
        print("✅ [EMAIL] Admin notified of feedback.")
    except Exception as e:
        print(f"💀 [EMAIL ERROR]: {e}")

# ----------------------------------
# 7. ROUTES
# ----------------------------------

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/logicprobe", response_class=HTMLResponse)
async def logic_probe(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("tool.html", {"request": request, "user": user})

# --- AUTH ROUTES ---

@app.post("/auth/send-otp")
async def send_otp(background_tasks: BackgroundTasks, email: str = Form(...)):
    otp = ''.join(random.choices(string.digits, k=6))
    expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (email, provider, otp_code, otp_expiry) 
                VALUES (%s, 'email', %s, %s)
                ON DUPLICATE KEY UPDATE otp_code=%s, otp_expiry=%s
            """, (email, otp, expiry, otp, expiry))
        conn.commit()
    except Exception as e:
        print(f"💀 [DB ERROR] OTP Write Failed: {e}")
        # We don't crash here, so we can try to send email anyway or return error
        return JSONResponse({"status": "error", "message": "Database Error"}, status_code=500)
    finally:
        conn.close()

    # Trigger Email in Background
    background_tasks.add_task(send_otp_email, email, otp)
    
    return {"status": "success", "message": "OTP Sent"}

@app.post("/auth/verify-otp")
async def verify_otp(request: Request, email: str = Form(...), otp: str = Form(...)):
    conn = get_connection()
    user_valid = False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email=%s AND otp_code=%s", (email, otp))
            user = cur.fetchone()
            
            if user:
                # Basic expiry check
                if user['otp_expiry'] and user['otp_expiry'] > datetime.datetime.now():
                    user_valid = True
                    cur.execute("UPDATE users SET otp_code=NULL, is_verified=1 WHERE email=%s", (email,))
                    conn.commit()
    finally:
        conn.close()

    if user_valid:
        request.session["user"] = {"email": email, "provider": "email"}
        return RedirectResponse(url="/logicprobe", status_code=303)
    else:
        return RedirectResponse(url="/login?error=Invalid+OTP", status_code=303)

# --- SOCIAL AUTH ---

@app.get("/auth/google/login")
async def google_login():
    with google_sso:
        return await google_sso.get_login_redirect()

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    try:
        with google_sso:
            user = await google_sso.verify_and_process(request)
        
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT IGNORE INTO users (email, provider, full_name, is_verified) 
                    VALUES (%s, 'google', %s, 1)
                """, (user.email, user.display_name))
            conn.commit()
        finally:
            conn.close()

        request.session["user"] = {
            "email": user.email, 
            "provider": "google", 
            "name": user.display_name
        }
        return RedirectResponse(url="/logicprobe")
    except Exception as e:
        print(f"💀 Google Auth Error: {e}")
        return RedirectResponse(url="/login?error=Google+Auth+Failed")

@app.get("/auth/microsoft/login")
async def microsoft_login():
    with microsoft_sso:
        return await microsoft_sso.get_login_redirect()

@app.get("/auth/microsoft/callback")
async def microsoft_callback(request: Request):
    try:
        with microsoft_sso:
            user = await microsoft_sso.verify_and_process(request)
        
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT IGNORE INTO users (email, provider, full_name, is_verified) 
                    VALUES (%s, 'microsoft', %s, 1)
                """, (user.email, user.display_name))
            conn.commit()
        finally:
            conn.close()

        request.session["user"] = {
            "email": user.email, 
            "provider": "microsoft", 
            "name": user.display_name
        }
        return RedirectResponse(url="/logicprobe")
    except Exception as e:
        return RedirectResponse(url="/login?error=MS+Auth+Failed")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

# --- FEATURES ---

@app.post("/submit-feedback")
async def submit_feedback(
    request: Request,
    background_tasks: BackgroundTasks
):
    user = request.session.get("user")
    data = await request.json()
    email = user["email"] if user else "Anonymous"
    message = data.get("message")
    rating = data.get("rating")
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO feedbacks (user_email, name, message, rating) 
                VALUES (%s, 'Anonymous', %s, %s)
            """, (email, message, rating))
        conn.commit()
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

    # TRIGGER EMAIL TO ADMIN
    background_tasks.add_task(send_admin_feedback, email, rating, message)

    return {"status": "success"}

@app.post("/save-code")
def save_code(data: CodeData, user=Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS code_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_email VARCHAR(255),
                    code TEXT,
                    language VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("INSERT INTO code_history (code, language, user_email) VALUES (%s, %s, %s)", 
                        (data.code, data.language, user['email']))
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()

@app.get("/load-last-code")
def load_last_code(user=Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM code_history WHERE user_email = %s ORDER BY id DESC LIMIT 1", (user['email'],))
            row = cur.fetchone()
            if row and 'created_at' in row: row['created_at'] = str(row['created_at'])
            return {"status": "success", "data": row}
    finally:
        conn.close()

@app.post("/save-project")
def save_project(data: ProjectData, user=Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO projects (user_email, name, code, language) VALUES (%s, %s, %s, %s)",
                        (user['email'], data.projectName, data.code, data.language))
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()

@app.get("/projects")
def get_projects(user=Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM projects WHERE user_email = %s ORDER BY created_at DESC", (user['email'],))
            rows = cur.fetchall()
            for r in rows: 
                if 'created_at' in r: r['created_at'] = str(r['created_at'])
            return {"status": "success", "projects": rows}
    finally:
        conn.close()

@app.post("/favorite-project")
def favorite_project(data: FavoriteData, user=Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE projects SET is_favorite = %s WHERE id = %s AND user_email = %s", 
                        (1 if data.fav else 0, data.id, user['email']))
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()

@app.post("/delete-project")
def delete_project(data: DeleteData, user=Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM projects WHERE id = %s AND user_email = %s", (data.id, user['email']))
        conn.commit()
        return {"status": "success"}
    finally:
        conn.close()

@app.get("/load-chat")
def load_chat(user=Depends(get_current_user)):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM ai_chat WHERE user_email = %s ORDER BY id ASC", (user['email'],))
            rows = cur.fetchall()
            for r in rows:
                if 'created_at' in r: r['created_at'] = str(r['created_at'])
            return {"status": "success", "chat": rows}
    except:
        return {"status": "success", "chat": []}
    finally:
        conn.close()

@app.post("/generate_pdf")
def generate_pdf(data: ReportData):
    try:
        pdf = CodeReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f"Target Language: {data.target_lang}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 6, f"Date: {time.strftime('%Y-%m-%d')}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        pdf.chapter_title("1. Compliance & Integrity Status")
        pdf.status_field("Quality Score:", str(data.quality_score) + " / 100")
        pdf.status_field("Compliance Status:", str(data.compliance_status))
        pdf.status_field("Plagiarism Check:", str(data.plagiarism_check))
        pdf.ln(5)

        pdf.chapter_title("2. Fixed Code")
        pdf.code_block(data.final_code if data.final_code else 'Analysis failed.')

        pdf.chapter_title("3. Explanation")
        pdf.code_block(data.explanation_text if data.explanation_text else 'No explanation.')
        
        pdf_bytes = pdf.output()
        pdf_buffer = io.BytesIO(pdf_bytes)
        filename = f"CodeStatic_Report_{time.strftime('%Y%m%d')}.pdf"
        
        return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})

    except Exception as e:
        print(f"PDF Error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF Generation Failed: {str(e)}")

@app.post("/ai_chat")
def ai_chat(data: ChatData, request: Request):
    user_email = "anonymous"
    user = request.session.get("user")
    if user: user_email = user['email']

    try:
        prompt = f"""
        ACT AS: An Expert AI Coding Assistant.
        CONTEXT CODE: ```{data.code_context}```
        QUESTION: "{data.message}"
        RESPONSE: Provide a direct, helpful Markdown answer.
        """
        
        ai_reply = "AI Services Busy."
        
        for model_name in MODEL_ROSTER:
            try:
                current_model = genai.GenerativeModel(model_name)
                response = current_model.generate_content(prompt)
                ai_reply = response.text
                break
            except:
                continue
        
        # Save to DB
        if user_email != "anonymous":
            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS ai_chat (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            user_email VARCHAR(255),
                            user_message TEXT,
                            ai_response TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cur.execute("INSERT INTO ai_chat (user_message, ai_response, user_email) VALUES (%s, %s, %s)", 
                                (data.message, ai_reply, user_email))
                conn.commit()
            finally:
                conn.close()

        return {"status": "success", "reply": ai_reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_code")
def process_code(data: ProcessCodeData, request: Request):
    user_email = "cli-bot"
    user = request.session.get("user")
    if user: user_email = user['email']

    try:
        source_code = data.code
        target_lang = data.target_lang
        
        if not source_code or not target_lang:
            raise HTTPException(status_code=400, detail="Missing code or target language")

        lines = source_code.split('\n')
        numbered_code = "\n".join([f"{i+1} | {line}" for i, line in enumerate(lines)])

        # Static Analysis (Mock or Real)
        static_result = analyzer.analyze(source_code, target_lang)
        
        # --- THE FULL PROMPT (PRESERVED) ---
        prompt = f"""
        ACT AS: The "Supreme Code Architect" and Forensic Debugger.
        TASK: Perform a deep-scan code audit, ruthlessly identify ALL errors, and generate a 100% CORRECT, COMPILABLE solution in {target_lang}.
        
        *** CRITICAL INSTRUCTION ON LINE NUMBERS ***
        The "CANDIDATE INPUT CODE" provided below is PRE-NUMBERED (Format: "LineNumber | Code").
        Use the EXPLICIT line number printed at the start of the line for the error table.
        
        CANDIDATE INPUT CODE:
        ```{numbered_code}```
        
        TARGET LANGUAGE: {target_lang}
        
        ------------------------------------------------------------------------
        MODULE 1: FORENSIC PLAGIARISM & AI DETECTION (ADVANCED SUPERVISED CHECK)
        ------------------------------------------------------------------------
        You are a highly supervised detection engine. Analyze the code for:
        
        1. **AI FINGERPRINT ANALYSIS:**
           - **ChatGPT Style:** Look for "Here is the code", generic variable names (foo, bar, example), or overly verbose comment structures typical of GPT-3.5/4.
           - **Gemini Style:** Look for Google-specific coding patterns, concise "solution-first" structures, or markers typical of PaLM/Gemini training data.
           - **Perplexity/Search AI:** Look for synthesized code that combines multiple distinct styles abruptly (indicating search aggregation).
           
        2. **TOP PROGRAMMING PLATFORM MATCHING:**
           - **LeetCode / HackerRank / GFG / Stack Overflow / Codeforces / CodeChef:** Check logic against the "Canonical Solutions" for known algorithms.
           - **StackOverflow:** Check for "Copy-Paste" patterns (e.g., keeping specific, irrelevant comments or variable names from popular threads).
           
        **PLAGIARISM OUTPUT INSTRUCTION:**
        In the JSON output `plagiarism_check` field, you MUST return a structured detailed string.
        - IF AI GENERATED: "High Match (AI Detected: [Model Name] Pattern)"
        - IF LEETCODE/GFG: "High Match (90%+ Similarity to [Site Name] Standard Solution)"
        - IF ORIGINAL: "Low Match (Original Logic / Custom Implementation)"

        ------------------------------------------------------------------------
        MODULE 2: 23-POINT VALIDATION PROTOCOL
        ------------------------------------------------------------------------
        1. **SYNTAX & COMPILATION (CRITICAL)**
           - Semicolons, Brackets, Typos.
        2. **LOGIC & SEMANTIC ERRORS**
           - Infinite Loops, Unreachable Code, Bad Assignments.
        3. **TYPE & CASTING ERRORS**
        4. **RUNTIME & EXCEPTION PREDICTION**
           - Null Pointer, Division by Zero.
        5. **LINKER & API ERRORS**
           - Missing Imports, Wrong Signatures.
        6. **MEMORY & RESOURCE MANAGEMENT**
           - Leaks, Unclosed Files.
        7. **OOP INTEGRITY**
           - Encapsulation, Inheritance, Class Structure.
        8. **DSA INTEGRITY (Data Structures)**
           - Linked Lists, Arrays (Bounds), Stacks.
        9. **SECURITY RISKS**
           - Buffer Overflow, Injection, Secrets.
        10. **CONCURRENCY (Thread Safety)**
        11. **I/O & FILE HANDLING**
        12. **CONFIGURATION & ENVIRONMENT**
            - Global Namespace Pollution.
        13. **MATH & ALGORITHMIC ACCURACY**
        14. **INTENT vs IMPLEMENTATION**
        15. **MANDATORY INDENTATION (Python Only)**
        16. **Database Errors**
        17. **Exception Handling (Empty catch)**
        18. **Hardware/Driver Issues**
        19. **Network Socket Failures**
        20. **Deprecated API Usage**
        21. **Race Conditions**
        22. **Floating Point Precision**
        23. **Misleading Comments**
        
        INSTRUCTIONS:
        1. **DETECT**: Identify source language.

        2. **ASSESS (Forensic Scan)**: 
           - **MENTAL COMPILATION**: Mentally compile the code. 
           - **ERROR MAPPING**: Populate the `error_table` with EVERY SINGLE issue found.
           - **Score**: Assign a strict quality score to the *INPUT* code (likely low) from 0 to 100.
           - **Plagiarism**: SIMULATE a check against known online solutions. Set `plagiarism_check` to: "High Match (e.g., LeetCode/GFG solution)" if the code is structured like a direct copy, or "Low Match (Original Logic)" otherwise.
        
        3. **MANDATORY PRE-FLIGHT CHECK (Internal)**:
           - "Does this code solve all 23 checklist items?"
           - "Is the fixed code translated correctly to {target_lang}?"
           - "Is the score of my fixed code 95/100 or higher?"
           -  If NO, refine it immediately until it is perfect.
        
        4. **FIX (Supreme Correction & TRANSLATION - Target 100/100)**: 
           - **MANDATORY TRANSLATION**: The `final_code` MUST be written in **{target_lang}**.
           - Rewrite the code to be **100% ERROR-FREE**.
           - The fixed code MUST address EVERY item in the checklist above.
           - **Guarantee**: The result must compile and run immediately without modification.
           - Add ALL missing imports/headers.
           - Fix ALL logic.
        
        5. **EXPLAIN (STRICT FILTERING)**: 
           - Provide a line-by-line explanation of the **FIXED FINAL CODE**.
           - **STRICT EXCLUSION RULE**: Do NOT generate an explanation object for:
             a. Lines that are empty or whitespace only.
             b. Lines that contain ONLY comments (starting with //, #, /*).
             c. Lines that contain ONLY closing braces '}}' or keywords like 'end' (unless critical logic).
           - **CRITICAL**: The 'code' field MUST contain the ACTUAL CODE SNIPPET from the 'final_code'.
           - Explain *what* the code does and *why* specific fixes were made.
        
        6. **COMPLEXITY**: 
           - Analyze Best, Average, and Worst Case Time Complexity.
           - Analyze Best, Average, and Worst Case Space Complexity.
           - Accuracy Check: Ensure the complexity analysis accurately reflects the efficiency of the provided solution and accounts for any recursive stacks or auxiliary structures.     
        
        OUTPUT FORMAT (Strict JSON):
        {{
            "detected_language": "String",
            "quality_score": Integer,
            "integrity_check": "String (Summary of critical failures found in original code)",
            "plagiarism_check": "String (DETAILED finding from Module 1)", 
            "maintainability_index": Integer,
            "readability_score": Integer,
            "target_complexity": "String (e.g., O(N log N))",
            "error_table": [ {{ "line": 5, "error": "Detailed error description" }} ],
            "final_code": "String (The 100% CORRECTED, COMPLETE, and COMPILABLE code in {target_lang})",
            "code_explanation": [ 
                {{ "line": 1, "code": "import os", "explanation": "Imports standard library..." }}
            ],
            "complexity": {{
                "time": {{ "best": "O(1)", "average": "O(n)", "worst": "O(n)", "desc": "Explanation..." }},
                "space": {{ "best": "O(1)", "average": "O(1)", "worst": "O(n)", "desc": "Explanation..." }}
            }},
            "status": "success",
            "target_lang": "{target_lang}" 
        }}
        """
        
        ai_success = False
        final_response = {}

        for model_name in MODEL_ROSTER:
            try:
                print(f"🤖 Attempting: {model_name}")
                current_model = genai.GenerativeModel(model_name)
                # FORCE JSON
                response = current_model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                final_response = json.loads(response.text)
                
                # MERGE STATIC ERRORS
                ai_errors = final_response.get("error_table", [])
                deterministic_errors = static_result.get("error_table", [])
                final_response["error_table"] = deterministic_errors + ai_errors
                
                ai_success = True
                
                # AUTO-SAVE REPORT TO DB
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS analysis_reports (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            user_email VARCHAR(255),
                            language VARCHAR(50),
                            quality_score INT,
                            critical_errors_count INT,
                            original_code TEXT,
                            fixed_code TEXT,
                            full_json_report JSON,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    cur.execute("""
                        INSERT INTO analysis_reports 
                        (language, quality_score, critical_errors_count, original_code, fixed_code, full_json_report, user_email)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        target_lang,
                        final_response.get("quality_score", 0),
                        len(final_response["error_table"]),
                        source_code,
                        final_response.get("final_code", ""),
                        json.dumps(final_response),
                        user_email
                    ))
                    conn.commit()
                    conn.close()
                except Exception as db_err:
                    print(f"⚠️ DB Save Failed: {db_err}")
                
                break

            except Exception as e:
                print(f"⚠️ Model {model_name} failed: {e}")
                continue 

        # FALLBACK
        if not ai_success:
            print("❌ AI FAILED. ENGAGING FALLBACK.")
            return {
                "status": "success",
                "quality_score": static_result.get("quality_score", 0),
                "integrity_check": "AI Unavailable",
                "plagiarism_check": "Unavailable",
                "error_table": static_result.get("error_table", []),
                "final_code": source_code,
                "explanation_text": "AI Services offline.",
                "target_lang": target_lang
            }

        return final_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("✅ CHECKPOINT 4: Reached Main Block")
    print("⚡ CHECKPOINT 5: Starting Uvicorn Server on Port 10000...")
    uvicorn.run(app, host="0.0.0.0", port=10000)