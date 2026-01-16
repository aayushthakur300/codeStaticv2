import os
import json
import time
import sys
import io
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any

from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse, Response, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fpdf import FPDF, XPos, YPos

# 1. LOAD ENVIRONMENT VARIABLES
load_dotenv()

# 2. SETUP FASTAPI APP
app = FastAPI(title="CodeStatic API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Template Configuration
# Assumes 'templates' folder exists in the same directory
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Mount templates as static to serve CSS/JS if they are mixed in the folder
# (Matching Flask's static_folder='templates' behavior)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "templates")), name="static")


# --------------------------------------------------------------------
# 🔹 DATABASE SETUP (SQLITE)
# --------------------------------------------------------------------
DB_PATH = BASE_DIR / "app.db"

def init_db():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS ai_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            ai_response TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS code_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            language TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            code TEXT,
            language TEXT,
            is_favorite INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        conn.close()
        print(f"✅ Database connected and initialized at: {DB_PATH}")
    except Exception as e:
        print(f"❌ Database Initialization Failed: {e}")

# Run init immediately
init_db()

# Dependency to get DB connection per request (Thread Safe)
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# --------------------------------------------------------------------
# 🔹 PYDANTIC MODELS (Input Validation)
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

class ProcessCodeData(BaseModel):
    code: str
    target_lang: str

# For PDF generation, the input is a complex dict (the report)
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
    # Allow extra fields without validation error
    class Config:
        extra = "allow"

# --------------------------------------------------------------------
# 🔹 GEMINI CONFIGURATION
# --------------------------------------------------------------------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ WARNING: API Key not found! Check your .env file.")

if api_key:
    genai.configure(api_key=api_key)

# MASSIVE ROUND ROBIN MODEL ROSTER
MODEL_ROSTER = [
    # --- TIER 1: HIGH SPEED & STABLE FLASH ---
    'models/gemini-2.0-flash',
    'models/gemini-2.0-flash-001',
    'models/gemini-flash-latest',
    'models/gemini-flash-lite-latest',
    'models/gemini-2.5-flash',
    'models/gemini-2.5-flash-lite',
    'models/gemini-robotics-er-1.5-preview',

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

    # --- TIER 7: OBSCURE PREVIEWS (LAST RESORT) ---
    'models/gemini-2.5-flash-native-audio-dialog',
    'models/nano-banana-pro-preview' 
]

# --------------------------------------------------------------------
# 🔹 PDF CLASS
# --------------------------------------------------------------------
class CodeReportPDF(FPDF):
    def header(self):
        # Professional Header
        self.set_font('Helvetica', 'B', 16)
        self.set_text_color(255, 255, 255)
        self.set_fill_color(220, 53, 69) # Professional Red (matching UI)
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
        self.set_fill_color(240, 240, 240) # Light Gray for Section Headers
        self.cell(0, 8, f"  {title}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L', fill=True)
        self.ln(4)

    def status_field(self, label, value):
        # Label
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(50, 50, 50)
        self.cell(45, 6, label, 0, new_x=XPos.RIGHT, new_y=YPos.TOP)
        
        # Value (Wrapped)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(0, 0, 0)
        # Handle non-string values
        val_str = str(value) if value is not None else ""
        self.multi_cell(0, 6, val_str, 0, align='L')
        self.ln(2)

    def code_block(self, code_text):
        self.set_font('Courier', '', 9)
        self.set_fill_color(250, 250, 250) # Very light gray for code background
        self.set_draw_color(200, 200, 200) # Subtle border
        
        # Convert to string just in case
        text = str(code_text)
        
        # Calculate height required
        self.multi_cell(0, 5, text, border=0, align='L', fill=False, dry_run=True)
        # Using effective_page_width for width calculation in FPDF2
        width = self.epw 
        
        # We print the cell with border and fill
        self.multi_cell(width, 5, text, border=1, align='L', fill=True)
        self.ln(5)

# --------------------------------------------------------------------
# 🔹 HTML ROUTES
# --------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    # Renders the NEW Landing Page (CodeStatic Home)
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logicprobe", response_class=HTMLResponse)
async def logic_probe(request: Request):
    # Renders the Assessment Tool
    return templates.TemplateResponse("tool.html", {"request": request})

# --------------------------------------------------------------------
# 🔹 PROJECT & DATABASE API ENDPOINTS
# --------------------------------------------------------------------

@app.post("/save-code")
def save_code(data: CodeData, db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute("INSERT INTO code_history (code, language) VALUES (?, ?)", (data.code, data.language))
        db.commit()
        return {"status": "success", "id": cur.lastrowid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/load-last-code")
def load_last_code(db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute("SELECT * FROM code_history ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            return {"status": "success", "data": None}
        return {"status": "success", "data": dict(row)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/load-chat")
def load_chat(db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute("SELECT * FROM ai_chat ORDER BY id ASC")
        rows = cur.fetchall()
        return {"status": "success", "chat": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-project")
def save_project(data: ProjectData, db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute("INSERT INTO projects (project_name, code, language) VALUES (?, ?, ?)",
                        (data.projectName, data.code, data.language))
        db.commit()
        return {"status": "success", "id": cur.lastrowid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects")
def get_projects(db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute("SELECT * FROM projects ORDER BY created_at DESC")
        rows = cur.fetchall()
        return {"status": "success", "projects": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/favorite-project")
def favorite_project(data: FavoriteData, db: sqlite3.Connection = Depends(get_db)):
    try:
        val = 1 if data.fav else 0
        cur = db.cursor()
        cur.execute("UPDATE projects SET is_favorite = ? WHERE id = ?", (val, data.id))
        db.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delete-project")
def delete_project(data: DeleteData, db: sqlite3.Connection = Depends(get_db)):
    try:
        cur = db.cursor()
        cur.execute("DELETE FROM projects WHERE id = ?", (data.id,))
        db.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------------------------------------------------
# 🔹 CORE FUNCTIONALITY (PDF & AI)
# --------------------------------------------------------------------

@app.post("/generate_pdf")
def generate_pdf(data: ReportData):
    try:
        if not data.final_code:
            raise HTTPException(status_code=400, detail="Missing required report data (run assessment first).")
        
        pdf = CodeReportPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        # 1. METADATA SECTION
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f"Target Language: {data.target_lang}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 6, f"Date: {time.strftime('%Y-%m-%d')}", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        # 2. STATUS SUMMARY
        pdf.chapter_title("2. Compliance & Integrity Status")
        # --- QUALITY SCORE SUPPORT ---
        pdf.status_field("Quality Score:", str(data.quality_score) + " / 100")
        pdf.status_field("Compliance Status:", str(data.compliance_status))
        pdf.status_field("Integrity Check:", str(data.integrity_check))
        pdf.status_field("Plagiarism Check:", str(data.plagiarism_check))
        pdf.ln(5)

        # 3. ORIGINAL CODE
        pdf.chapter_title("3. Candidate Submission (Original Code)")
        pdf.code_block(data.original_code if data.original_code else 'No code provided.')

        # 4. FIXED CODE
        pdf.chapter_title("4. Standardized & Fixed Code")
        pdf.code_block(data.final_code if data.final_code else 'Analysis failed.')

        # 5. CRITICAL ERROR LOG
        pdf.chapter_title("5. Critical Error Log")
        pdf.code_block(data.error_log_text if data.error_log_text else 'No critical errors found.')
        
        # 6. COMPLEXITY
        pdf.chapter_title("6. Complexity Analysis")
        pdf.code_block(data.time_analysis if data.time_analysis else 'N/A')
        pdf.code_block(data.space_analysis if data.space_analysis else 'N/A')

        # 7. EXPLANATION
        pdf.chapter_title("7. Line-by-Line Explanation")
        pdf.code_block(data.explanation_text if data.explanation_text else 'No detailed explanation provided.')
        
        # Output PDF to a buffer
        pdf_bytes = pdf.output()
        pdf_buffer = io.BytesIO(pdf_bytes)
        
        # Send the PDF as a file download
        download_filename = f"CodeStatic_Report_{time.strftime('%Y%m%d%H%M%S')}.pdf"
        
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={download_filename}"}
        )

    except Exception as e:
        print(f"PDF Generation Error (Fpdf2): {e}")
        raise HTTPException(status_code=500, detail=f"PDF Generation Failed: {str(e)}")

@app.post("/ai_chat")
def ai_chat(data: ChatData, db: sqlite3.Connection = Depends(get_db)):
    try:
        user_message = data.message
        current_code = data.code_context
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No message provided")

        # Chat Prompt - Helpful Assistant
        prompt = f"""
        ACT AS: An Expert AI Coding Assistant for the CodeStatic platform.
        YOUR GOAL: Help the user understand logic, syntax, or concepts. Be concise, friendly, and accurate. Use **only** standard Markdown (like bold, italics, code blocks, or lists) for formatting. DO NOT use special Unicode symbols, emojis, or custom stylistic characters.
        
        USER'S CURRENT CODE CONTEXT (For reference only):
        ```{current_code}```
        
        USER QUESTION: "{user_message}"
        
        RESPONSE: Provide a direct, helpful answer.
        """
        
        # Simple Round Robin for Chat
        for model_name in MODEL_ROSTER:
            try:
                current_model = genai.GenerativeModel(model_name)
                response = current_model.generate_content(prompt)
                ai_reply = response.text

                # --- SAVE TO DB ---
                try:
                    cur = db.cursor()
                    cur.execute("INSERT INTO ai_chat (user_message, ai_response) VALUES (?, ?)", (user_message, ai_reply))
                    db.commit()
                except Exception as db_err:
                    print(f"⚠️ Failed to save chat to DB: {db_err}")

                return {"status": "success", "reply": ai_reply}
            except:
                continue 
        
        return JSONResponse(status_code=429, content={"status": "error", "message": "AI services busy."})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process_code")
def process_code(data: ProcessCodeData):
    try:
        source_code = data.code
        target_lang = data.target_lang
        
        if not source_code or not target_lang:
            raise HTTPException(status_code=400, detail="Missing code or target language")

        lines = source_code.split('\n')
        numbered_code = "\n".join([f"{i+1} | {line}" for i, line in enumerate(lines)])

        # --------------------------------------------------------------------------------
        #  SUPREME CODE ARCHITECT & ADVANCED PLAGIARISM FORENSICS MODULE
        # --------------------------------------------------------------------------------
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
        
        # --- ROUND ROBIN GENERATION STRATEGY ---
        last_error = None
        
        for model_name in MODEL_ROSTER:
            try:
                current_model = genai.GenerativeModel(model_name)
                response = current_model.generate_content(prompt)
                
                clean_text = response.text.replace('```json', '').replace('```', '').strip()
                json_response = json.loads(clean_text)
                
                # Manually inject dummy metrics to prevent JS crash
                json_response["maintainability_index"] = json_response.get("maintainability_index", 50)
                json_response["readability_score"] = json_response.get("readability_score", 75)
                json_response["target_complexity"] = json_response.get("target_complexity", "O(N log N)")
                
                # Default Fallback for Quality Score
                json_response["quality_score"] = json_response.get("quality_score", 0)

                print(f"✅ Success using: {model_name}") 
                return json_response

            except exceptions.ResourceExhausted:
                print(f"⚠️ Quota exceeded for {model_name}. Switching to next...")
                last_error = "Daily Quota Exceeded on all models."
                continue 
            
            except Exception as e:
                last_error = str(e)
                continue 

        return JSONResponse(
            status_code=429,
            content={
                "status": "error", 
                "message": f"All available models are busy or out of quota. Last error: {last_error}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- TERMINAL STARTUP INSTRUCTION ---
if __name__ == "__main__":
    import uvicorn
    # Use 'main:app' if the file is named main.py, otherwise change 'main' to filename
    uvicorn.run(app, host="0.0.0.0", port=10000)