🚀 **CodeStatic — Enterprise Forensic Workspace**

Production-grade AI system for static code analysis, forensic auditing, and automated security compliance.

CodeStatic is a secure, full-stack forensic platform designed to mirror real-world enterprise security workflows. It performs deep static analysis, enforces Sentinel CI/CD quality gates, identifies algorithmic complexity (Big-O), and auto-remediates vulnerabilities using deterministic AI models.

The system is built on a FastAPI backend with a custom "Dangerous" themed frontend, utilizing secure OAuth protocols (Google & Microsoft), passwordless OTP authentication, and containerized deployment standards.

---

## 🧠 Why This Project Stands Out (Recruiter View)

✔ **Solves Real Engineering Problems** — Implements forensic auditing and complexity analysis, not just basic CRUD operations.
✔ **Enterprise Security Architecture** — OAuth2 (Google/Microsoft Entra ID) with HTTP-only persistent sessions instead of weak JWT-only auth.
✔ **DevOps & Containerization** — Fully Dockerized using multi-stage builds for cloud-agnostic deployment (Render / AWS).
✔ **CI/CD Simulation** — Includes a Sentinel gate that blocks builds below quality thresholds, simulating Jenkins / GitHub Actions.
✔ **High-Performance Async Backend** — Built with FastAPI + BackgroundTasks for non-blocking execution.

---

## 🏗️ System Architecture
![pic](https://github.com/user-attachments/assets/b59396cc-9c83-4250-ba45-1386b2fba73c)


CodeStatic operates on a high-throughput, distributed micro-architecture designed for security and speed.

### Edge / Client Tier (Vanilla JS + CSS)

Captures raw code input, utilizes debounced auto-saving to prevent DDoS, and enforces strict DOM sanitization (textContent) to neutralize DOM-based XSS attacks before they render.

### API Gateway (FastAPI)

Handles incoming REST payloads, validates payload sizes using Pydantic limits (Buffer Overflow protection), and strips malicious HTML/JS via the bleach library (Stored XSS protection).

### Deterministic Engine (Stage 1 Analysis)

A lightning-fast, pre-compiled Regex engine containing 500+ forensic signatures. It scans for hardcoded secrets, dangerous evaluations, and weak cryptography without relying on AI latency.

### Generative AI Microservice (Stage 2 Analysis)

Invokes the Google Gemini API to contextually understand the code, fix complex logical errors, compute Space/Time complexity (Big-O), and format the remediation output into a strict, parseable JSON schema.

### Persistence Layer (MongoDB Atlas)

ACID-compliant document storage ensuring referential integrity of User Profiles, Audit Logs, and Code Snapshots.

### Reporting Engine

Asynchronously formats successful scans into downloadable forensic PDF artifacts via fpdf2.

---

## ✨ Core Capabilities

### 🛡️ 1. Advanced Authentication & Security

* Multi-Provider OAuth SSO: Google Workspace & Microsoft Outlook / Entra ID integration via fastapi-sso
* Magic Link / OTP Login: Secure, passwordless email authentication via SMTP
* Persistent Sessions: HTTP-only cookies with 30-day persistence (max_age=2592000) and SameSite=Lax
* Role-Based Access Control: Middleware blocks forensic tools unless a valid session exists

---

### 🔍 2. Static Analysis & Sentinel Gate

* Algorithmic Complexity Analysis: Automatic Big-O estimation for Time (Best / Average / Worst) and Space complexity
* Security & Integrity Scanning: Detects OWASP-style vulnerabilities, plagiarism patterns (SourceSense Monitor), and code integrity violations
* Sentinel CI/CD Gate: Blocks builds if Quality Score < 70, emitting real CI-style logs: EXIT CODE 1 (Build Aborted)

---

### 🛠️ 3. AI Remediation & Forensic Reporting

* Deterministic AI Fixes: Generates compilable, safe remediation for detected bugs and vulnerabilities
* Automated PDF Reports: Forensic reports generated using fpdf2 (modern Unicode support)
* Downloadable Artifacts: One-click export bundle containing:

  * Original source code
  * Error & vulnerability logs
  * Remediation steps
  * Complexity metrics

---

### ⚡ 4. Asynchronous Feedback Loop

* Background Tasks: Heavy email operations are offloaded using FastAPI BackgroundTasks
* Admin Notifications: HTML-formatted alert emails sent instantly without blocking user requests

---

## ⚙️ Backend Architecture

### 🧩 Tech Stack

* Runtime: Python 3.13 / 3.10 (compatible)
* Framework: FastAPI (async/await architecture)
* Containerization: Docker (multi-stage builds)
* Authentication: OAuth2 (Google & Microsoft Entra ID) + OTP
* Database: MongoDB Atlas (Cloud NoSQL) / SQLite / MySQL
* PDF Engine: fpdf2
* Template Engine: Jinja2 (server-side rendering)

---

## 📂 Key Files

* run.py → Complete backend: API routing, AI pipelines, DB persistence, PDF generation, and security middleware
* analysis_engine.py → 500+ signature deterministic static analyzer
* templates/login.html → Secure "Dangerous" themed login (SSO + OTP)
* templates/tool.html → Main forensic workspace dashboard
* Dockerfile → Production-grade container definition

---

## 🔧 Configuration (.env)

The application requires a `.env` file in the project root.

⚠️ **Do NOT commit this file to version control.**

```env
# --- Core Security ---
SESSION_SECRET=your_long_random_string_here

# --- Database ---
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
MONGO_DB=codestatic_db
DATABASE_URL=sqlite:///./codestatic.db

# --- AI Integration ---
GEMINI_API_KEY=your_google_gemini_api_key
GOOGLE_API_KEY=your_google_gemini_api_key

# --- OAuth ---
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
MS_CLIENT_ID=your_azure_client_id
MS_CLIENT_SECRET=your_azure_client_secret

# --- Email / SMTP (OTP & Feedback) ---
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=your_email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
```

---

## 📦 Installation & Deployment

### Option A: Docker (Production — Recommended)

CodeStatic is fully containerized for seamless cloud deployment.

#### 1. Build the Image

```bash
# Uses Python 3.13-slim base image
docker build -t codestatic-app .
```

#### 2. Run the Container

```bash
# Runs on port 10000, injecting environment variables
docker run -p 10000:10000 --env-file .env codestatic-app
```

---

### Option B: Local Development

#### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

⚠️ Ensure `fpdf2` is installed (not deprecated `fpdf`).

#### 2. Run the Server

```bash
python run.py
```

Access the application at:
[http://localhost:10000](http://localhost:10000)

---

## 🔌 API Documentation

Once running, interactive Swagger docs are automatically generated and available at:
[http://localhost:10000/docs](http://localhost:10000/docs)

### Key Endpoints

| Method | Endpoint              | Description                                      |
| ------ | --------------------- | ------------------------------------------------ |
| GET    | /auth/google/login    | Google OAuth flow                                |
| GET    | /auth/microsoft/login | Microsoft OAuth (prompt: select_account)         |
| POST   | /process_code         | Core static analysis and AI remediation endpoint |
| POST   | /generate_pdf         | Generate forensic PDF artifact                   |
| POST   | /submit-feedback      | Async feedback submission to Admin               |
| POST   | /ai_chat              | Context-aware generative AI assistant            |

---

## 🏁 Final Note

CodeStatic is not a tutorial project. It is a portfolio-grade engineering system aligned with real enterprise hiring standards.

It demonstrates expertise in:

* Cloud Security (OAuth2, secure sessions, XSS/Injection mitigation)
* DevOps (Docker, CI/CD Sentinel simulation)
* Advanced Backend Engineering (FastAPI, async systems, regex compilation)

---

**Author:** Aayush Thakur
**Role:** Full-Stack Engineer | AI-Focused Systems

⭐ If this repository impressed you or added value, consider starring it.
