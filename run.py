import sys
import traceback
import os
import json
import time
import io
import random
import string
import datetime
import ssl
import smtplib
import re
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

# 🛡️ SECURITY INJECTIONS: Added Field and field_validator for input capping and XSS prevention
from pydantic import BaseModel, ConfigDict, Field, field_validator
from fpdf import FPDF, XPos, YPos

# MongoDB Integration
import pymongo
from bson.objectid import ObjectId
from bson.errors import InvalidId # 🛡️ SECURITY: Prevents DB crashes on fake IDs

# Email Libraries
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

# 🛡️ SECURITY INJECTIONS: Bleach for sanitizing HTML/JS payloads
import bleach

# --- 💀 SILENT KILLER DETECTION: GLOBAL CRASH HANDLER ---
def crash_handler(exctype, value, tb):
    print("\n\n" + "="*60)
    print("💀 FATAL ERROR: SYSTEM CRASHED!")
    print("="*60)
    traceback.print_exception(exctype, value, tb)
    print("="*60)
    input("Press ENTER to exit...")

sys.excepthook = crash_handler
print("🚀 [SYSTEM] Initializing CodeStatic AI SaaS Backend (MongoDB Edition)...")
# ----------------------------------

# 1. LOAD ENVIRONMENT VARIABLES
load_dotenv()
print("✅ [CHECKPOINT] Environment Variables Loaded")

# 2. SETUP FASTAPI APP
app = FastAPI(title="CodeStatic AI (Enterprise SaaS)")

@app.get("/healthz")
def health_check():
    return {"status": "ok"}

# 🛡️ SECURITY UPGRADE: CORS Lockdown. No more "*" wildcard.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://codestatic2-0.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"], 
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

# MongoDB Config
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB", "codestatic_db")

#------------------------------------------------------------------------------------
# Email Config (SMTP)
mail_conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your-email@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", "admin@codestatic.ai"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

#-------------------------------------------------------------------------------
# AI Config
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

MODEL_ROSTER = [
     # --- TIER 1: HIGH SPEED & STABLE FLASH ---
    'models/gemini-3-flash-lite-preview',
        'models/gemini-3.1-pro-preview',
        'models/gemini-3.1-pro-preview-customtools',
        'models/gemini-2.5-pro',
        'models/gemini-2.5-flash',
        'models/gemini-2.5-flash-lite',
        'models/gemini-3-flash-preview',
        'models/gemini-2.0-flash',
        'models/gemini-flash-latest',
        'models/gemini-flash-lite-latest',
        'models/gemini-robotics-er-1.5-preview',
        'models/gemini-3.1-flash-preview',
        'models/gemini-3.1-flash-lite-preview',
        'models/gemini-2.0-flash-001',
        'models/gemini-2.0-flash-lite',
        'models/gemini-2.0-flash-lite-001',
        'models/gemini-2.0-flash-exp',
        'models/gemini-exp-1206',
        'models/gemini-2.0-flash-lite-preview',
        'models/gemini-2.0-flash-lite-preview-02-05',
        'models/gemini-2.5-flash-preview-09-2025',
        'models/gemini-2.5-flash-lite-preview-09-2025',
        'models/gemma-3-27b-it',
        'models/gemma-3-12b-it',
        'models/gemma-3-4b-it',
        'models/gemma-3-1b-it',
        'models/gemma-3n-e4b-it',
        'models/gemma-3n-e2b-it',
        'models/gemma-2-27b-it',
        'models/gemma-2-9b-it',
        'models/gemma-2-2b-it',
        'models/gemini-3-pro-preview',
        'models/deep-research-pro-preview-12-2025',
        'models/gemini-1.5-pro',
        'models/gemini-1.5-pro-latest',
        'models/gemini-1.5-pro-001',
        'models/gemini-1.5-pro-002',
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-latest',
        'models/gemini-1.5-flash-001',
        'models/gemini-1.5-flash-002',
        'models/gemini-1.5-flash-8b',
        'models/gemini-1.5-flash-8b-latest',
        'models/gemini-1.5-flash-8b-001',
        'models/gemini-pro-latest',
        'models/gemini-pro-latest',
        'models/gemini-1.0-pro-001',
        'models/gemini-pro',
        'models/gemini-pro-vision',
        'models/gemini-2.5-flash-native-audio-dialog',
        'models/gemini-2.5-flash-tts',
        'models/nano-banana-pro-preview',
        'models/aqa',
]

# --------------------------------------------------------------------
# 🔹 DATABASE HELPERS (MongoDB)
# --------------------------------------------------------------------
try:
    mongo_client = pymongo.MongoClient(MONGO_URI)
    db = mongo_client[MONGO_DB_NAME]
    mongo_client.server_info() # Validate connection
    print("✅ [INIT] MongoDB Connected Successfully.")
except Exception as e:
    print(f"\n💀 [FATAL] MongoDB Connection Failed!")
    print(f"   Error: {e}")
    print(f"   Check: Is MongoDB running? Is the URI correct?")

def get_db():
    """Dependency for routes"""
    return db

def format_mongo_doc(doc):
    """Formats MongoDB _id object to string for JSON serialization"""
    if doc and "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc

# --------------------------------------------------------------------
# 🔹 AUTHENTICATION UTILITIES
# --------------------------------------------------------------------

def get_current_user():
    """
    Returns a unified anonymous user model since OAuth & Sessions 
    have been stripped from the architecture.
    """
    return {"email": "anonymous@codestatic.ai", "provider": "guest"}

# --------------------------------------------------------------------
# 🔹 PYDANTIC MODELS (🛡️ SECURITY UPGRADED)
# --------------------------------------------------------------------
class CodeData(BaseModel):
    # 🛡️ CAP MEMORY EXPLOITS: Limit code submission sizes to 50k chars
    code: str = Field(..., max_length=50000)
    language: str = Field(..., max_length=50)

class ProjectData(BaseModel):
    projectName: str = Field(..., max_length=150)
    code: str = Field(..., max_length=50000)
    language: str = Field(..., max_length=50)
    report_data: Optional[dict] = None  # <-- Added this field

    # 🛡️ XSS SHIELD: Sanitize the project name before it hits DB
    @field_validator('projectName')
    @classmethod
    def sanitize_name(cls, value: str) -> str:
        return bleach.clean(value)

class FavoriteData(BaseModel):
    id: str
    fav: bool | int

class DeleteData(BaseModel):
    id: str

class ChatData(BaseModel):
    message: str = Field(..., max_length=3000)
    code_context: Optional[str] = Field(default="", max_length=50000)

    # 🛡️ XSS SHIELD: Sanitize the AI chat message input
    @field_validator('message')
    @classmethod
    def sanitize_chat(cls, value: str) -> str:
        return bleach.clean(value)

class FeedbackData(BaseModel):
    message: str = Field(..., max_length=2000)
    rating: int

    # 🛡️ XSS SHIELD: Sanitize the user feedback
    @field_validator('message')
    @classmethod
    def sanitize_msg(cls, value: str) -> str:
        return bleach.clean(value)

class ProcessCodeData(BaseModel):
    code: str = Field(..., max_length=50000)
    target_lang: str = Field(..., max_length=50)
    candidate_id: Optional[str] = "N/A"
    is_ci_build: Optional[bool] = False 

class ReportData(BaseModel):
    model_config = ConfigDict(extra="allow") # <-- This replaces "class Config:"
    
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
    user = get_current_user()
    return templates.TemplateResponse("tool.html", {"request": request, "user": user})

# --------------------------------------------------------------------
# 🔹 UTILITY ENDPOINTS
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

# --------------------------------------------------------------------
# 🔹 USER DATA API (ISOLATED PER USER)
# --------------------------------------------------------------------

@app.post("/submit-feedback")
async def submit_feedback(
    data: FeedbackData, 
    background_tasks: BackgroundTasks,  # <--- INJECTED HERE
    user=Depends(get_current_user), 
    db=Depends(get_db)
):
    try:
        # 1. Save to MongoDB
        db.feedbacks.insert_one({
            "user_email": user['email'],
            "message": data.message,
            "rating": data.rating,
            "created_at": datetime.datetime.now()
        })
        
        # 2. Trigger Email to Admin 
        background_tasks.add_task(
            send_feedback_notification, 
            user['email'], 
            data.rating, 
            data.message
        )

        return {"status": "success"}
    except Exception as e:
        # 🛡️ SECURITY: Mask Internal DB Errors from Hackers
        print(f"CRITICAL ERROR in /submit-feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/save-code")
def save_code(data: CodeData, user=Depends(get_current_user), db=Depends(get_db)):
    try:
        result = db.code_history.insert_one({
            "code": data.code,
            "language": data.language,
            "user_email": user['email'],
            "created_at": datetime.datetime.now()
        })
        return {"status": "success", "id": str(result.inserted_id)}
    except Exception as e:
        print(f"CRITICAL ERROR in /save-code: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.get("/load-last-code")
def load_last_code(user=Depends(get_current_user), db=Depends(get_db)):
    try:
        row = db.code_history.find_one(
            {"user_email": user['email']}, 
            sort=[("_id", pymongo.DESCENDING)]
        )
        if not row: return {"status": "success", "data": None}
        
        row = format_mongo_doc(row)
        if 'created_at' in row: row['created_at'] = str(row['created_at'])
        return {"status": "success", "data": row}
    except Exception as e:
        print(f"CRITICAL ERROR in /load-last-code: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/save-project")
def save_project(data: ProjectData, user=Depends(get_current_user), db=Depends(get_db)):
    try:
        result = db.projects.insert_one({
            "project_name": data.projectName,
            "code": data.code,
            "language": data.language,
            "report_data": data.report_data,  # <-- Saving the snapshot to MongoDB
            "user_email": user['email'],
            "is_favorite": 0,
            "created_at": datetime.datetime.now()
        })
        return {"status": "success", "id": str(result.inserted_id)}
    except Exception as e:
        print(f"CRITICAL ERROR in /save-project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")
    
@app.get("/projects")
def get_projects(user=Depends(get_current_user), db=Depends(get_db)):
    try:
        rows = list(db.projects.find({"user_email": user['email']}).sort("_id", pymongo.DESCENDING))
        for r in rows: 
            r = format_mongo_doc(r)
            if 'created_at' in r: r['created_at'] = str(r['created_at'])
        return {"status": "success", "projects": rows}
    except Exception as e:
        print(f"CRITICAL ERROR in /projects: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/favorite-project")
def favorite_project(data: FavoriteData, user=Depends(get_current_user), db=Depends(get_db)):
    try:
        # 🛡️ SECURITY: Prevent DB crash on fake ObjectId injections
        if not ObjectId.is_valid(data.id):
            raise HTTPException(status_code=400, detail="Invalid Project ID format.")

        val = 1 if data.fav else 0
        db.projects.update_one(
            {"_id": ObjectId(data.id), "user_email": user['email']},
            {"$set": {"is_favorite": val}}
        )
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR in /favorite-project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/delete-project")
def delete_project(data: DeleteData, user=Depends(get_current_user), db=Depends(get_db)):
    try:
        # 🛡️ SECURITY: Prevent DB crash on fake ObjectId injections
        if not ObjectId.is_valid(data.id):
            raise HTTPException(status_code=400, detail="Invalid Project ID format.")

        db.projects.delete_one({"_id": ObjectId(data.id), "user_email": user['email']})
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR in /delete-project: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.get("/load-chat")
def load_chat(user=Depends(get_current_user), db=Depends(get_db)):
    try:
        rows = list(db.ai_chat.find({"user_email": user['email']}).sort("_id", pymongo.ASCENDING))
        for r in rows:
            r = format_mongo_doc(r)
            if 'created_at' in r: r['created_at'] = str(r['created_at'])
        return {"status": "success", "chat": rows}
    except Exception as e:
        print(f"CRITICAL ERROR in /load-chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

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
        print(f"CRITICAL ERROR in /generate_pdf: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/ai_chat")
def ai_chat(data: ChatData, request: Request, db=Depends(get_db)):
    user_email = "anonymous@codestatic.ai"
    user = get_current_user()
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
                print(f"⚠️ Chat Model {model_name} failed: {e}")
                continue
        
        if success:
            try:
                db.ai_chat.insert_one({
                    "user_message": user_message,
                    "ai_response": ai_reply,
                    "user_email": user_email,
                    "created_at": datetime.datetime.now()
                })
            except Exception as e:
                print(f"Chat DB Error: {e}")

        return {"status": "success", "reply": ai_reply}

    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR in /ai_chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

@app.post("/process_code")
def process_code(data: ProcessCodeData, request: Request):
    user_email = "cli-bot@codestatic.ai"
    user = get_current_user()
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

        # --------------------------------------------------------------------
        # STAGE 1: NATIVE JSON GENERATION LOOP
        # --------------------------------------------------------------------
        for model_name in MODEL_ROSTER:
            try:
                print(f"🤖 [STAGE 1: NATIVE JSON] Attempting: {model_name}")
                current_model = genai.GenerativeModel(model_name)
                response = current_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
                )
                
                json_response = json.loads(response.text)
                
                # MERGE LOGIC
                ai_errors = json_response.get("error_table", [])
                deterministic_errors = static_result.get("error_table", [])
                json_response["error_table"] = deterministic_errors + ai_errors
                
                if len(deterministic_errors) > 0 and json_response.get("quality_score", 100) > 50:
                    json_response["quality_score"] -= (len(deterministic_errors) * 10)
                
                json_response["quality_score"] = max(0, json_response.get("quality_score", 0))
                final_response = json_response
                ai_success = True
                
                try:
                    db.analysis_reports.insert_one({
                        "language": target_lang,
                        "quality_score": final_response["quality_score"],
                        "critical_errors_count": len(final_response["error_table"]),
                        "original_code": source_code,
                        "fixed_code": final_response.get("final_code", ""),
                        "full_json_report": json.dumps(final_response),
                        "user_email": user_email,
                        "created_at": datetime.datetime.now()
                    })
                except Exception as db_err:
                    print(f"⚠️ DB Save Failed: {db_err}")
                
                break
            except Exception as e:
                print(f"⚠️ Stage 1 Model {model_name} failed: {e}")
                continue 

        # --------------------------------------------------------------------
        # STAGE 2: FALLBACK REGEX & STRING STRIPPING LOOP
        # --------------------------------------------------------------------
        if not ai_success:
            print("⚠️ STAGE 1 NATIVE JSON FAILED. ENGAGING STAGE 2: REGEX STRIPPING...")
            for model_name in MODEL_ROSTER:
                try:
                    print(f"🤖 [STAGE 2: REGEX] Attempting: {model_name}")
                    current_model = genai.GenerativeModel(model_name)
                    response = current_model.generate_content(prompt)
                    
                    clean_text = response.text
                    json_match = re.search(r'```json\n(.*?)\n```', clean_text, re.DOTALL)
                    
                    if json_match:
                        clean_text = json_match.group(1)
                    else:
                        clean_text = clean_text.replace('```json', '').replace('```', '').strip()
                        
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
                    
                    try:
                        db.analysis_reports.insert_one({
                            "language": target_lang,
                            "quality_score": final_response["quality_score"],
                            "critical_errors_count": len(final_response["error_table"]),
                            "original_code": source_code,
                            "fixed_code": final_response.get("final_code", ""),
                            "full_json_report": json.dumps(final_response),
                            "user_email": user_email,
                            "created_at": datetime.datetime.now()
                        })
                    except Exception as db_err:
                        print(f"⚠️ DB Save Failed: {db_err}")
                        
                    break
                except Exception as e:
                    print(f"⚠️ Stage 2 Model {model_name} failed: {e}")
                    continue

        # 3. FALLBACK ENGINE (If both stages fail)
        if not ai_success:
            print("❌ AI ENTIRELY FAILED. ENGAGING DETERMINISTIC FALLBACK.")
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
                db.ci_logs.insert_one({
                    "project_name": "CI_Job",
                    "status": status_val,
                    "score": final_response["quality_score"],
                    "detected_issues": issues,
                    "user_email": user_email,
                    "created_at": datetime.datetime.now()
                })
            except Exception as e:
                print(f"⚠️ CI Log Failed: {e}")

        return final_response

    except HTTPException:
        raise
    except Exception as e:
        print(f"CRITICAL ERROR in /process_code: {e}")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")

if __name__ == "__main__":
    import uvicorn
    print("✅ CHECKPOINT 4: Reached Main Block")
    print("⚡ CHECKPOINT 5: Starting Uvicorn Server on Port 10000...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=10000)
    except Exception as e:
        print(f"💀 SERVER CRASHED: {e}")