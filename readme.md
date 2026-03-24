🚀 **CodeStatic — Enterprise Forensic Workspace**

 AI system for static code analysis, forensic auditing, and automated security compliance.

CodeStatic is a full-stack forensic platform designed to mirror real-world enterprise code-quality workflows. It performs deep static analysis, enforces Sentinel CI/CD quality gates, identifies algorithmic complexity (Big-O), and auto-remediates vulnerabilities using deterministic AI models.

The system is built on a high-performance FastAPI backend with a custom "Dangerous" themed frontend.

---
### 🌐 Live Link
# ⏳ Service Initialization Instructions (Render Cold Start)
# Due to cold start behavior on hosted backend services:
# 1️⃣ Open the backend services first:
# Link: https://codestatic-2-0.onrender.com

## 🧠 Why This Project Stands Out (Recruiter View)

✔ **Solves Real Engineering Problems** — Implements forensic auditing and complexity analysis, not just basic CRUD operations.
✔ **DevOps & Containerization** — Fully Dockerized using multi-stage builds for cloud-agnostic deployment (Render / AWS).
✔ **CI/CD Simulation** — Includes a Sentinel gate that blocks builds below quality thresholds, simulating Jenkins / GitHub Actions.
✔ **High-Performance Async Backend** — Built with FastAPI + BackgroundTasks for non-blocking execution.

---

## 🏗️ System Architecture
![Image 2026-03-20 at 9 27 22 PM](https://github.com/user-attachments/assets/b31f9d36-5637-4e4c-a2b5-fbe616f0f946)

CodeStatic operates on a high-throughput, distributed micro-architecture designed for speed and reliability.

### Edge / Client Tier (Vanilla JS + CSS)

Captures raw code input, utilizes debounced auto-saving to prevent server overload, and enforces strict DOM sanitization (textContent) to neutralize DOM-based XSS attacks before they render.

### API Gateway (FastAPI)

Handles incoming REST payloads, validates payload sizes using Pydantic limits (Buffer Overflow protection), and strips malicious HTML/JS via the bleach library (Stored XSS protection).

### Deterministic Engine (Stage 1 Analysis)

A lightning-fast, pre-compiled Regex engine containing 500+ forensic signatures. It scans for hardcoded secrets, dangerous evaluations, and weak cryptography without relying on AI latency.

### Generative AI Microservice (Stage 2 Analysis)

Invokes the Google Gemini API to contextually understand the code, fix complex logical errors, compute Space/Time complexity (Big-O), and format the remediation output into a strict, parseable JSON schema.

### Persistence Layer (MongoDB Atlas)

ACID-compliant document storage ensuring referential integrity of Audit Logs, Project States, and Code Snapshots.

### Reporting Engine

Asynchronously formats successful scans into downloadable forensic PDF artifacts via fpdf2.

---

## ✨ Core Capabilities

### 🔍 1. Static Analysis & Sentinel Gate

* Algorithmic Complexity Analysis: Automatic Big-O estimation for Time (Best / Average / Worst) and Space complexity
* Code Integrity Scanning: Detects vulnerabilities, plagiarism patterns (SourceSense Monitor), and code integrity violations
* Sentinel CI/CD Gate: Blocks builds if Quality Score < 70, emitting real CI-style logs: EXIT CODE 1 (Build Aborted)

---

### 🛠️ 2. AI Remediation & Forensic Reporting

* Deterministic AI Fixes: Generates compilable, safe remediation for detected bugs and vulnerabilities
* Automated PDF Reports: Forensic reports generated using fpdf2 (modern Unicode support)
* Downloadable Artifacts: One-click export bundle containing:

  * Original source code
  * Error & vulnerability logs
  * Remediation steps
  * Complexity metrics

---

### ⚡ 3. Asynchronous Execution

* Background Tasks: Heavy data processing operations and database writes are offloaded using FastAPI BackgroundTasks to keep the UI strictly non-blocking

---

## ⚙️ Backend Architecture

### 🧩 Tech Stack

* Runtime: Python 3.13 / 3.10 (compatible)
* Framework: FastAPI (async/await architecture)
* Containerization: Docker (multi-stage builds)
* Database: MongoDB Atlas (Cloud NoSQL) / SQLite / MySQL
* PDF Engine: fpdf2
* Template Engine: Jinja2 (server-side rendering)

---

## 📂 Key Files

* run.py → Complete backend: API routing, AI pipelines, DB persistence, and PDF generation
* analysis_engine.py → 500+ signature deterministic static analyzer
* templates/tool.html → Main forensic workspace dashboard
* Dockerfile → Production-grade container definition

---

## 🔧 Configuration (.env)

The application requires a `.env` file in the project root.

⚠️ **Do NOT commit this file to version control.**

```env
# --- Database ---
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
MONGO_DB=codestatic_db
DATABASE_URL=sqlite:///./codestatic.db

# --- AI Integration ---
GEMINI_API_KEY=your_google_gemini_api_key
GOOGLE_API_KEY=your_google_gemini_api_key
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
http://localhost:10000

---

## 🔌 API Documentation

Once running, interactive Swagger docs are automatically generated and available at:
http://localhost:10000/docs

### Key Endpoints

| Method | Endpoint      | Description                                      |
| ------ | ------------- | ------------------------------------------------ |
| POST   | /process_code | Core static analysis and AI remediation endpoint |
| POST   | /generate_pdf | Generate forensic PDF artifact                   |
| POST   | /save-project | Persists code snapshot to MongoDB layer          |
| POST   | /ai_chat      | Context-aware generative AI assistant            |

---

## 🏁 Final Note

CodeStatic is not a tutorial project. It is a portfolio-grade engineering system aligned with real enterprise hiring standards.

It demonstrates expertise in:

* DevOps (Docker, CI/CD Sentinel simulation)
* Advanced Backend Engineering (FastAPI, async systems, regex compilation)
* Defensive Programming (Strict input sanitization, Pydantic validation)

---

**Author:** Aayush Thakur
**Role:** Full-Stack Engineer | AI-Focused Systems

⭐ If this repository impressed you or added value, consider starring it.
