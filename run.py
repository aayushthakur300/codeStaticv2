# 4th version
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

from dotenv import load_dotenv
import google.generativeai as genai

# FastAPI & Core Utilities
from fastapi import FastAPI, Request, HTTPException, Depends, Form, BackgroundTasks, status
from fastapi.responses import JSONResponse, Response, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from fpdf import FPDF, XPos, YPos

# Security & Auth Libraries
from fastapi_sso.sso.google import GoogleSSO
from fastapi_sso.sso.microsoft import MicrosoftSSO
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

#latest added
def send_otp_email(email: str, otp: str):
    print(f"📧 SENDING OTP TO: {email}")
    
    sender_email = os.getenv("MAIL_USERNAME", "codestatic.ai@gmail.com")
    sender_password = os.getenv("MAIL_PASSWORD")
    
    # 1. Setup Message with UTF-8 support
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = "Your Verification Code"
    
    body = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>🔐 Login Verification</h2>
        <p>Your OTP code is:</p>
        <h1 style="color: #4CAF50; letter-spacing: 5px;">{otp}</h1>
        <p>This code expires in 10 minutes.</p>
    </div>
    """
    
    # ✅ FIX: Explicitly set utf-8 encoding to prevent crashes with symbols
    message.attach(MIMEText(body, "html", "utf-8"))
    
    try:
        # 2. Connect via SSL (Port 465)
        # timeout=30 prevents it from hanging forever
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)
        
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        print("✅ EMAIL SENT SUCCESSFULLY")
        return True
        
    except Exception as e:
        print(f"❌ EMAIL FAILED: {e}")
        # We re-raise the error so the route knows it failed
        raise e

# --- 💀 SILENT KILLER DETECTION: GLOBAL CRASH HANDLER ---
def crash_handler(exctype, value, tb):
    print("\n\n" + "="*60)
    print("💀 FATAL ERROR: SYSTEM CRASHED!")
    print("="*60)
    traceback.print_exception(exctype, value, tb)
    print("="*60)
    input("Press ENTER to exit...")

sys.excepthook = crash_handler
print("🚀 [SYSTEM] Initializing CodeStatic AI SaaS Backend...")
# ----------------------------------

# 1. LOAD ENVIRONMENT VARIABLES
load_dotenv()
print("✅ [CHECKPOINT] Environment Variables Loaded")

# 2. SETUP FASTAPI APP
app = FastAPI(title="CodeStatic AI (Enterprise SaaS)")

# --- PASTE THIS INTO RUN.PY (REPLACING THE OLD STARTUP FUNCTION) ---


# --- REPLACE YOUR STARTUP EVENT IN RUN.PY ---

@app.on_event("startup")
def fix_all_database_tables():
    print("🔨 [MAINTENANCE] SYNCHRONIZING DATABASE TO SESSION...")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. USERS TABLE (Standard)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255),
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255),
            otp_code VARCHAR(10),
            otp_expiry DATETIME,
            provider VARCHAR(50) DEFAULT 'email',
            google_id VARCHAR(255),
            profile_pic VARCHAR(500),
            is_verified BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. PROJECTS TABLE (Switching user_id -> user_email)
        print("🔧 Re-building 'projects' table...")
        cursor.execute("DROP TABLE IF EXISTS projects")
        cursor.execute("""
        CREATE TABLE projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255),  -- ✅ MATCHES SESSION
            name VARCHAR(255),
            description TEXT,
            code TEXT,
            language VARCHAR(50) DEFAULT 'python',
            is_favorite BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 3. FEEDBACKS TABLE
        print("🔧 Re-building 'feedbacks' table...")
        cursor.execute("DROP TABLE IF EXISTS feedbacks")
        cursor.execute("""
        CREATE TABLE feedbacks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255),  -- ✅ MATCHES SESSION
            name VARCHAR(255),
            message TEXT,
            rating INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 4. CHATS TABLE (Switching user_id -> user_email)
        print("🔧 Re-building 'chats' table...")
        cursor.execute("DROP TABLE IF EXISTS chats")
        cursor.execute("""
        CREATE TABLE chats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_email VARCHAR(255),  -- ✅ MATCHES SESSION
            user_message TEXT,
            ai_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()
        conn.close()
        print("✅ SUCCESS: Database is now 100% synced with Session data.")
        
    except Exception as e:
        print(f"❌ DATABASE INIT ERROR: {e}")
# -------------------------------------------------------------------

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

# SECURITY: Session Middleware (Crucial for Login)
# In production, SESSION_SECRET should be a complex random string in .env
# UPDATE IN RUN.PY
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware, 
    secret_key=os.getenv("SESSION_SECRET", "dev-secret-key-change-me-in-prod"),
    https_only=True,       # Keep False for Localhost, change to True for Render
    max_age=30*24*60*60,    # 30 Days (in seconds) -> "Remember Me"
    same_site="lax"         # Helps cookies stick better on localhost
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "templates")), name="static")

# --- IMPORT: DETERMINISTIC ENGINE ---
try:
    from analysis_engine import analyzer
    print("✅ [CHECKPOINT] Analysis Engine Loaded Successfully")
except ImportError:
    print("❌ [CRITICAL] analysis_engine.py not found! AI Fallback only.")
    # Fallback to prevent crash if engine is missing
    class MockAnalyzer:
        def analyze(self, c, l): return {"quality_score": 0, "error_table": [], "complexity": {}}
    analyzer = MockAnalyzer()

# --------------------------------------------------------------------
# 🔹 CONFIGURATION (DB, EMAIL, AI)
# --------------------------------------------------------------------

# Database Config
# DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_HOST = os.getenv("DB_HOST", "DB_HOST")
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DB", "codestatic_db")
DB_PORT = int(os.getenv("DB_PORT", 25214)) # It will read 25390 from Render

#------------------------------------------------------------------------------------
# # Email Config (SMTP)
# mail_conf = ConnectionConfig(
#     MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your-email@gmail.com"),
#     MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
#     # MAIL_FROM=os.getenv("MAIL_USERNAME", "admin@localhost"),
#     # Change "admin@localhost" to something with a domain
#     MAIL_FROM=os.getenv("MAIL_FROM", "admin@codestatic.ai"),
#     MAIL_PORT=587,
#     MAIL_SERVER="smtp.gmail.com",
#     MAIL_STARTTLS=True,
#     MAIL_SSL_TLS=False,
#     USE_CREDENTIALS=True,
#     VALIDATE_CERTS=True
# )
# ✅ CORRECT CONFIGURATION (Matches your working Test Script)
mail_conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME","codestatic.ai@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD",""),
    
    # ⚠️ CRITICAL: Gmail blocks emails if "From" doesn't match "Username"
    # We force it to match your login email to prevent "Silent Death"
    MAIL_FROM=os.getenv("MAIL_USERNAME","codestatic.ai@gmail.com"), 
    
    # ✅ USE PORT 465 (SSL) - This is what worked in your test
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    
    # ✅ SSL SETTINGS (Must match Port 465)
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False
)
#-------------------------------------------------------------------------------
# AI Config
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

# OAuth Config (Optional)
google_sso = GoogleSSO(
    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    # redirect_uri="http://localhost:10000/auth/google/callback"
    redirect_uri= "https://codestaticv2.onrender.com/auth/google/callback"
)

microsoft_sso = MicrosoftSSO(
    client_id=os.getenv("MS_CLIENT_ID", ""),
    client_secret=os.getenv("MS_CLIENT_SECRET", ""),
    #redirect_uri="http://localhost:10000/auth/microsoft/callback"
    redirect_uri= "https://codestaticv2.onrender.com/auth/microsoft/callback"
)
# --------------------------------------------------------------------
# 🔹 DATABASE HELPERS
# --------------------------------------------------------------------
def get_connection():
    # Define the path where Render mounts the Secret File
    ca_path = "/etc/secrets/ca.pem"

    # Check if the file actually exists (Safety Check)
    ssl_config = None
    if os.path.exists(ca_path):
        print(f"🔒 SSL: Found CA Certificate at {ca_path}")
        ssl_config = {'ca': ca_path}
    else:
        print("⚠️ SSL: CA Certificate NOT found! Connection might fail.")
    print("--------------------------------------------------")
    print(f"🔍 DEBUG DATABASE: Trying to connect to host: '{DB_HOST}'")
    print("--------------------------------------------------")
    """Creates a fresh connection to MySQL"""
    try:
        return pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "defaultdb"),
            charset='utf8mb4',
            port=int(os.getenv("DB_PORT", 25214)),
            ssl=ssl_config,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"💀 [FATAL] Database Connection Failed: {e}")
        raise e

def init_db():
    print("⏳ [INIT] Verifying Database Connection...")
    try:
        conn = get_connection()
        conn.close()
        print("✅ [INIT] Database Connected Successfully.")
    except Exception as e:
        print(f"❌ [INIT] Database Error: {e}")
        # We don't exit here to allow debugging, but routes will fail

init_db()

def get_db():
    """Dependency for routes"""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

# --------------------------------------------------------------------
# 🔹 AUTHENTICATION UTILITIES (The Guard)
# --------------------------------------------------------------------

def get_current_user(request: Request):
    """
    SECURITY GATE: Ensures only logged-in users can access specific routes.
    """
    user = request.session.get("user")
    if not user:
        print(f"⛔ [AUTH BLOCK] Access denied to {request.url.path}")
        raise HTTPException(status_code=401, detail="Not Authenticated. Please Login.")
    return user

async def send_otp_email(email: str, otp: str):
    """Sends the magic code via real SMTP"""
    print(f"📧 [EMAIL] Preparing to send OTP to {email}...")
    try:
        message = MessageSchema(
            subject="LogicProbe Verification Code",
            recipients=[email],
            body=f"""
            Your Secure Login Code is: {otp}
            
            This code expires in 10 minutes.
            If you did not request this, please ignore this email.
            """,
            subtype=MessageType.plain
        )
        fm = FastMail(mail_conf)
        await fm.send_message(message)
        print(f"✅ [EMAIL] OTP sent successfully to {email}")
    except Exception as e:
        print("=====================================================")
        print("💀 EMAIL FATAL ERROR DETAILS:")
        print(traceback.format_exc())  # <--- THIS IS THE MAGIC LINE
        print("=====================================================")
    # Keep your existing return statement if you have one
# --------------------------------------------------------------------
# 🔹 PYDANTIC MODELS
# --------------------------------------------------------------------
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

# --------------------------------------------------------------------
# 🔹 PDF GENERATOR CLASS
# --------------------------------------------------------------------
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

# --------------------------------------------------------------------
# 🔹 PUBLIC ROUTES (Landing & Auth)
# --------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/logicprobe", response_class=HTMLResponse)
async def logic_probe(request: Request):
    # SECURE: Require Session
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("tool.html", {"request": request, "user": user})

# --------------------------------------------------------------------
# 🔹 AUTHENTICATION ENDPOINTS (OTP & OAUTH)
# --------------------------------------------------------------------

async def send_feedback_notification(user_email: str, rating: int, feedback_msg: str):
    """
    Sends an email to the Admin (You) when a user submits feedback.
    """
    admin_email = os.getenv("MAIL_USERNAME") # You receive the email
    
    print(f"📧 [EMAIL] Forwarding user feedback to Admin ({admin_email})...")
    
    html_body = f"""
    <h3>🚀 New Feedback Received</h3>
    <p><strong>User:</strong> {user_email}</p>
    <p><strong>Rating:</strong> {rating} / 5 Stars</p>
    <hr>
    <p><strong>Message:</strong></p>
    <blockquote style="background: #f9f9f9; padding: 10px; border-left: 5px solid #ef4444;">
        {feedback_msg}
    </blockquote>
    """
    
    try:
        message = MessageSchema(
            subject=f"📢 New Feedback from {user_email}",
            recipients=[admin_email],  # Sending to YOU
            body=html_body,
            subtype=MessageType.html
        )
        fm = FastMail(mail_conf)
        await fm.send_message(message)
        print("✅ [EMAIL] Feedback notification sent to Admin.")
    except Exception as e:
        print(f"💀 [EMAIL ERROR] Failed to notify admin: {e}")
        
@app.post("/auth/send-otp")
# async def send_otp(background_tasks: BackgroundTasks, email: str = Form(...)):
#     # 1. Generate Logic
#     otp = ''.join(random.choices(string.digits, k=6))
#     expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
    
#     conn = get_connection()
#     try:
#         with conn.cursor() as cur:
#             # 2. Save to DB (Upsert)
#             cur.execute("""
#                 INSERT INTO users (email, provider, otp_code, otp_expiry) 
#                 VALUES (%s, 'email', %s, %s)
#                 ON DUPLICATE KEY UPDATE otp_code=%s, otp_expiry=%s
#             """, (email, otp, expiry, otp, expiry))
#         conn.commit()
#     except Exception as e:
#         print(f"💀 [DB ERROR] OTP Write Failed: {e}")
#         raise HTTPException(status_code=500, detail="Database Error")
#     finally:
#         conn.close()

#     # 3. Send Email (Background)
#     background_tasks.add_task(send_otp_email, email, otp)
    
#     return {"status": "success", "message": "OTP Sent"}
@app.post("/auth/send-otp")
async def send_otp(email: str = Form(...)):  # Removed BackgroundTasks
    # 1. Generate Logic
    otp = ''.join(random.choices(string.digits, k=6))
    expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 2. Save to DB (Upsert)
            cur.execute("""
                INSERT INTO users (email, provider, otp_code, otp_expiry) 
                VALUES (%s, 'email', %s, %s)
                ON DUPLICATE KEY UPDATE otp_code=%s, otp_expiry=%s
            """, (email, otp, expiry, otp, expiry))
        conn.commit()
    except Exception as e:
        print(f"💀 [DB ERROR] OTP Write Failed: {e}")
        raise HTTPException(status_code=500, detail="Database Error")
    finally:
        conn.close()

    # 3. Send Email (DIRECTLY - No Background Task)
    # This calls the new sync function we just wrote using smtplib
    try:
        send_otp_email(email, otp)
    except Exception as e:
        print(f"💀 [EMAIL ERROR] Failed to notify user: {e}")
        # We return success to the UI so the user isn't confused, 
        # but check your logs if it fails.
        return {"status": "error", "message": "Email failed to send"}
    
    return {"status": "success", "message": "OTP Sent"}

@app.post("/auth/verify-otp")
async def verify_otp(request: Request, email: str = Form(...), otp: str = Form(...)):
    conn = get_connection()
    user_valid = False
    try:
        with conn.cursor() as cur:
            # 1. Check DB
            cur.execute("SELECT * FROM users WHERE email=%s AND otp_code=%s", (email, otp))
            user = cur.fetchone()
            
            if user:
                # 2. Check Expiry
                if user['otp_expiry'] and user['otp_expiry'] > datetime.datetime.now():
                    user_valid = True
                    # 3. Cleanup
                    cur.execute("UPDATE users SET otp_code=NULL, is_verified=1 WHERE email=%s", (email,))
                    conn.commit()
    finally:
        conn.close()

    if user_valid:
        # 4. Create Session
        request.session["user"] = {"email": email, "provider": "email"}
        print(f"✅ [AUTH] User {email} logged in successfully.")
        return RedirectResponse(url="/logicprobe", status_code=303)
    else:
        print(f"⛔ [AUTH] Invalid Login Attempt for {email}")
        return RedirectResponse(url="/login?error=Invalid+or+Expired+OTP", status_code=303)

# --- SOCIAL OAUTH (FIXED: CONTEXT MANAGER) ---

@app.get("/auth/google/login")
async def google_login():
    """Redirect to Google Login Page"""
    with google_sso:  # SECURITY FIX: Use Context Manager
        return await google_sso.get_login_redirect()

@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """Process Google Login Response"""
    try:
        with google_sso:  # SECURITY FIX: Use Context Manager
            user = await google_sso.verify_and_process(request)
        
        # Save User to DB
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

        # Set Session
        request.session["user"] = {
            "email": user.email, 
            "provider": "google", 
            "name": user.display_name
        }
        return RedirectResponse(url="/logicprobe")
    
    except Exception as e:
        print(f"💀 Google Auth Error: {e}")
        return RedirectResponse(url="/login?error=Google+Auth+Failed")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

# --------------------------------------------------------------------
# 🔹 USER DATA API (ISOLATED PER USER)
# --------------------------------------------------------------------

# @app.post("/submit-feedback")
# async def submit_feedback(
#     data: FeedbackData, 
#     background_tasks: BackgroundTasks,  # <--- INJECTED HERE
#     user=Depends(get_current_user), 
#     db=Depends(get_db)
# ):
#     try:
#         # 1. Save to Database (Existing Logic)
#         cur = db.cursor()
#         cur.execute("INSERT INTO feedbacks (user_email, message, rating) VALUES (%s, %s, %s)", 
#                    (user['email'], data.message, data.rating))
#         db.commit()
        
#         # 2. Trigger Email to Admin (New Logic)
#         # We use background_tasks so the user interface doesn't freeze while sending email.
#         background_tasks.add_task(
#             send_feedback_notification, 
#             user['email'], 
#             data.rating, 
#             data.message
#         )

#         return {"status": "success"}
#     except Exception as e:
#         print(f"Feedback Error: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/save-code")
# def save_code(data: CodeData, user=Depends(get_current_user), db=Depends(get_db)):
#     try:
#         cur = db.cursor()
#         # SECURE: Save with user_email
#         cur.execute("INSERT INTO code_history (code, language, user_email) VALUES (%s, %s, %s)", 
#                    (data.code, data.language, user['email']))
#         db.commit()
#         return {"status": "success", "id": cur.lastrowid}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/load-last-code")
# def load_last_code(user=Depends(get_current_user), db=Depends(get_db)):
#     try:
#         cur = db.cursor()
#         # SECURE: Filter by user_email
#         cur.execute("SELECT * FROM code_history WHERE user_email = %s ORDER BY id DESC LIMIT 1", (user['email'],))
#         row = cur.fetchone()
#         if not row: return {"status": "success", "data": None}
#         if 'created_at' in row: row['created_at'] = str(row['created_at'])
#         return {"status": "success", "data": row}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/save-project")
# def save_project(data: ProjectData, user=Depends(get_current_user), db=Depends(get_db)):
#     try:
#         cur = db.cursor()
#         cur.execute("INSERT INTO projects (project_name, code, language, user_email) VALUES (%s, %s, %s, %s)",
#                     (data.projectName, data.code, data.language, user['email']))
#         db.commit()
#         return {"status": "success"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/projects")
# def get_projects(user=Depends(get_current_user), db=Depends(get_db)):
#     try:
#         cur = db.cursor()
#         # SECURE: Filter by user_email
#         cur.execute("SELECT * FROM projects WHERE user_email = %s ORDER BY created_at DESC", (user['email'],))
#         rows = cur.fetchall()
#         for r in rows: 
#             if 'created_at' in r: r['created_at'] = str(r['created_at'])
#         return {"status": "success", "projects": rows}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/favorite-project")
# def favorite_project(data: FavoriteData, user=Depends(get_current_user), db=Depends(get_db)):
#     try:
#         val = 1 if data.fav else 0
#         cur = db.cursor()
#         cur.execute("UPDATE projects SET is_favorite = %s WHERE id = %s AND user_email = %s", 
#                    (val, data.id, user['email']))
#         db.commit()
#         return {"status": "success"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/delete-project")
# def delete_project(data: DeleteData, user=Depends(get_current_user), db=Depends(get_db)):
#     try:
#         cur = db.cursor()
#         cur.execute("DELETE FROM projects WHERE id = %s AND user_email = %s", (data.id, user['email']))
#         db.commit()
#         return {"status": "success"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/load-chat")
# def load_chat(user=Depends(get_current_user), db=Depends(get_db)):
#     try:
#         cur = db.cursor()
#         # Filter by User
#         cur.execute("SELECT * FROM ai_chat WHERE user_email = %s ORDER BY id ASC", (user['email'],))
#         rows = cur.fetchall()
#         for r in rows:
#             if 'created_at' in r: r['created_at'] = str(r['created_at'])
#         return {"status": "success", "chat": rows}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
@app.post("/submit-feedback")
async def submit_feedback(request: Request):
    # 1. Get User Session
    user = request.session.get("user")
    
    # 2. Parse Data
    data = await request.json()
    email = user["email"] if user else "Anonymous"
    name = data.get("name", "Guest")
    message = data.get("message")
    rating = data.get("rating")
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 3. Save to Database
            cur.execute("""
                INSERT INTO feedbacks (user_email, name, message, rating) 
                VALUES (%s, %s, %s, %s)
            """, (email, name, message, rating))
        conn.commit()
        
        # 4. (Optional) Send Email to Admin directly
        # If you have an admin email function, call it here:
        # send_admin_notification(email, message, rating)
        
        return {"status": "success", "message": "Feedback Received"}
        
    except Exception as e:
        print(f"❌ FEEDBACK ERROR: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

# ------------------------------------------------------------------
# 2. CODE HISTORY (Save & Load Last Code)
# ------------------------------------------------------------------
@app.post("/save-code")
async def save_code(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in"}, status_code=401)

    data = await request.json()
    code = data.get("code")
    language = data.get("language")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Ensure table exists on the fly (Safety check)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS code_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_email VARCHAR(255),
                    code TEXT,
                    language VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Save
            cur.execute("""
                INSERT INTO code_history (code, language, user_email) 
                VALUES (%s, %s, %s)
            """, (code, language, user["email"]))
        conn.commit()
        return {"status": "success", "message": "Code Saved"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

@app.get("/load-last-code")
async def load_last_code(request: Request):
    user = request.session.get("user")
    if not user:
        return {"status": "success", "data": None} # Return empty for guests

    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT * FROM code_history 
                WHERE user_email = %s 
                ORDER BY id DESC LIMIT 1
            """, (user["email"],))
            row = cur.fetchone()
            
            # Convert datetime to string for JSON serialization
            if row and 'created_at' in row:
                row['created_at'] = str(row['created_at'])
                
            return {"status": "success", "data": row}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

# ------------------------------------------------------------------
# 3. PROJECTS (Save, Load, Delete, Favorite)
# ------------------------------------------------------------------
@app.post("/save-project")
async def save_project(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in"}, status_code=401)
    
    data = await request.json()
    # Support both 'projectName' (frontend) and 'name'
    name = data.get("projectName") or data.get("name")
    code = data.get("code")
    language = data.get("language", "python")
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO projects (user_email, name, code, language) 
                VALUES (%s, %s, %s, %s)
            """, (user["email"], name, code, language))
        conn.commit()
        return {"status": "success", "message": "Project Saved"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

@app.get("/projects")
async def get_projects(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in"}, status_code=401)

    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("""
                SELECT * FROM projects 
                WHERE user_email = %s 
                ORDER BY created_at DESC
            """, (user["email"],))
            projects = cur.fetchall()
            
            # Convert datetimes
            for p in projects:
                if 'created_at' in p: p['created_at'] = str(p['created_at'])
                
            return {"status": "success", "projects": projects}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

@app.post("/favorite-project")
async def favorite_project(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in"}, status_code=401)

    data = await request.json()
    project_id = data.get("id")
    # Support both 'fav' and 'is_favorite' keys
    is_fav = data.get("fav") if "fav" in data else data.get("is_favorite")
    
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            val = 1 if is_fav else 0
            cur.execute("""
                UPDATE projects SET is_favorite = %s 
                WHERE id = %s AND user_email = %s
            """, (val, project_id, user["email"]))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

@app.post("/delete-project")
async def delete_project(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse({"status": "error", "message": "Not logged in"}, status_code=401)

    data = await request.json()
    project_id = data.get("id")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM projects 
                WHERE id = %s AND user_email = %s
            """, (project_id, user["email"]))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        conn.close()

# ------------------------------------------------------------------
# 4. CHAT HISTORY
# ------------------------------------------------------------------
@app.get("/load-chat")
async def load_chat(request: Request):
    user = request.session.get("user")
    if not user:
        return {"status": "success", "chat": []}

    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # We check both 'chats' and 'ai_chat' tables to be safe
            # Use the one defined in your startup script (likely 'chats')
            cur.execute("""
                SELECT * FROM chats 
                WHERE user_email = %s 
                ORDER BY id ASC
            """, (user["email"],))
            rows = cur.fetchall()
            
            for r in rows:
                if 'timestamp' in r: r['timestamp'] = str(r['timestamp'])
                if 'created_at' in r: r['created_at'] = str(r['created_at'])
                
            return {"status": "success", "chat": rows}
    except Exception as e:
        print(f"Chat Load Error: {e}")
        return {"status": "success", "chat": []} # Return empty if error
    finally:
        conn.close()
# --------------------------------------------------------------------
# 🔹 CORE ANALYSIS LOGIC (AI, Chat, Reports)
# --------------------------------------------------------------------

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
        
        pdf.chapter_title("2. Compliance & Integrity Status")
        pdf.status_field("Quality Score:", str(data.quality_score) + " / 100")
        pdf.status_field("Compliance Status:", str(data.compliance_status))
        pdf.status_field("Integrity Check:", str(data.integrity_check))
        pdf.status_field("Plagiarism Check:", str(data.plagiarism_check))
        pdf.ln(5)

        pdf.chapter_title("3. Candidate Submission")
        pdf.code_block(data.original_code if data.original_code else 'No code provided.')

        pdf.chapter_title("4. Standardized & Fixed Code")
        pdf.code_block(data.final_code if data.final_code else 'Analysis failed.')

        pdf.chapter_title("5. Critical Error Log")
        pdf.code_block(data.error_log_text if data.error_log_text else 'No critical errors found.')
        
        pdf.chapter_title("6. Complexity Analysis")
        pdf.code_block(data.time_analysis if data.time_analysis else 'N/A')
        pdf.code_block(data.space_analysis if data.space_analysis else 'N/A')

        pdf.chapter_title("7. Line-by-Line Explanation")
        pdf.code_block(data.explanation_text if data.explanation_text else 'No explanation.')
        
        pdf_bytes = pdf.output()
        pdf_buffer = io.BytesIO(pdf_bytes)
        download_filename = f"CodeStatic_Report_{time.strftime('%Y%m%d%H%M%S')}.pdf"
        
        return Response(content=pdf_buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={download_filename}"})

    except Exception as e:
        print(f"PDF Error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF Generation Failed: {str(e)}")

@app.post("/ai_chat")
def ai_chat(data: ChatData, request: Request, db=Depends(get_db)):
    # Optional Auth for Chat (or link to session if exists)
    user_email = "anonymous"
    user = request.session.get("user")
    if user: user_email = user['email']

    try:
        user_message = data.message
        current_code = data.code_context
        
        if not user_message: raise HTTPException(status_code=400, detail="No message provided")

        prompt = f"""
        ACT AS: An Expert AI Coding Assistant.
        CONTEXT CODE: ```{current_code}```
        QUESTION: "{user_message}"
        RESPONSE: Provide a direct, helpful Markdown answer.
        """
        
        ai_reply = "AI Services Busy."
        success = False
        
        for model_name in MODEL_ROSTER:
            try:
                current_model = genai.GenerativeModel(model_name)
                response = current_model.generate_content(prompt)
                ai_reply = response.text
                success = True
                break
            except Exception as e:
                print(f"⚠️ Model {model_name} failed: {e}")
                continue
        
        if success:
            try:
                cur = db.cursor()
                cur.execute("INSERT INTO ai_chat (user_message, ai_response, user_email) VALUES (%s, %s, %s)", 
                           (user_message, ai_reply, user_email))
                db.commit()
            except Exception as e:
                print(f"Chat DB Error: {e}")

        return {"status": "success", "reply": ai_reply}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_code")
def process_code(data: ProcessCodeData, request: Request):
    # This endpoint is PUBLIC to allow CLI tools to work without complex session cookies
    # However, if called from the Browser, we try to link it to the User for logs.
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

        print("🔍 Running Deterministic Rules Engine...")
        static_result = analyzer.analyze(source_code, target_lang)
        
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
                response = current_model.generate_content(prompt)
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                json_response = json.loads(clean_text)
                
                # MERGE LOGIC
                ai_errors = json_response.get("error_table", [])
                deterministic_errors = static_result.get("error_table", [])
                json_response["error_table"] = deterministic_errors + ai_errors
                
                if len(deterministic_errors) > 0 and json_response.get("quality_score", 100) > 50:
                    json_response["quality_score"] -= (len(deterministic_errors) * 10)
                
                json_response["quality_score"] = max(0, json_response.get("quality_score", 0))
                final_response = json_response
                ai_success = True
                
                # --- AUTO-SAVE TO MYSQL (With User Email if available) ---
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO analysis_reports 
                        (language, quality_score, critical_errors_count, original_code, fixed_code, full_json_report, user_email)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        target_lang,
                        final_response["quality_score"],
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
                # --------------------------
                
                break

            except Exception as e:
                print(f"⚠️ Model {model_name} failed: {e}")
                continue 

        # 3. FALLBACK ENGINE
        if not ai_success:
            print("❌ AI FAILED. ENGAGING FALLBACK.")
            return {
                "status": "success",
                "quality_score": static_result["quality_score"],
                "integrity_check": "⚠️ AI OFFLINE - RUNNING DETERMINISTIC",
                "plagiarism_check": "Unavailable",
                "error_table": static_result["error_table"],
                "final_code": source_code,
                "code_explanation": [{"line": 0, "code": "SYS", "explanation": "AI Unavailable."}],
                "complexity": static_result["complexity"],
                "target_lang": target_lang
            }

        # 4. CI/CD LOGGING (Sentinel)
        if data.is_ci_build:
            status_val = "PASS" if final_response["quality_score"] >= 70 else "BLOCK"
            issues = f"{len(final_response.get('error_table', []))} Errors"
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO ci_logs (project_name, status, score, detected_issues, user_email)
                    VALUES (%s, %s, %s, %s, %s)
                """, ("CI_Job", status_val, final_response["quality_score"], issues, user_email))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"⚠️ CI Log Failed: {e}")

        return final_response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("✅ CHECKPOINT 4: Reached Main Block")
    print("⚡ CHECKPOINT 5: Starting Uvicorn Server on Port 10000...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=10000)
    except Exception as e:
        print(f"💀 SERVER CRASHED: {e}")
