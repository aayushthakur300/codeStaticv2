#!/usr/bin/env node
const fetch = require('node-fetch'); // npm install node-fetch@2
const fs = require('fs');
const path = require('path');

// CONFIGURATION
const SERVER_URL = "http://localhost:10000/process_code"; // Port matches run.py default
const args = process.argv.slice(2);
const filePath = args[0];
let targetLang = args[1]; // Optional: User can override

// ANSI Colors for Terminal "Red Box" Effect
const TERM = {
    reset: "\x1b[0m",
    red: "\x1b[31m",
    green: "\x1b[32m",
    yellow: "\x1b[33m",
    cyan: "\x1b[36m",
    bold: "\x1b[1m",
    bgRed: "\x1b[41m",
    white: "\x1b[37m",
    magenta: "\x1b[35m"
};

// --- LANGUAGE DETECTION ENGINE (20+ Languages) ---
function detectLanguage(file) {
    const ext = path.extname(file).toLowerCase();
    const map = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.jsx': 'JavaScript (React)',
        '.ts': 'TypeScript',
        '.tsx': 'TypeScript (React)',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.cc': 'C++',
        '.cxx': 'C++',
        '.h': 'C++',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.kts': 'Kotlin',
        '.scala': 'Scala',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.sql': 'SQL',
        '.sh': 'Bash/Shell',
        '.bash': 'Bash/Shell',
        '.r': 'R',
        '.m': 'MATLAB',
        '.pl': 'Perl',
        '.lua': 'Lua',
        '.dart': 'Dart',
        '.json': 'JSON',
        '.xml': 'XML',
        '.yaml': 'YAML',
        '.yml': 'YAML'
    };
    return map[ext] || 'Python'; // Default fallback
}

// VALIDATION
if (!filePath) {
    console.log(`${TERM.red}❌ Usage: node cli/codestatic_ci.js <path_to_code_file> [target_language]${TERM.reset}`);
    process.exit(1);
}

if (!fs.existsSync(filePath)) {
    console.log(`${TERM.red}❌ Error: File not found at ${filePath}${TERM.reset}`);
    process.exit(1);
}

// AUTO-DETECT IF NOT PROVIDED
if (!targetLang) {
    targetLang = detectLanguage(filePath);
}

async function runCiCheck() {
    console.log(`${TERM.cyan}🔍 CODESTATIC CI: Reading source file...${TERM.reset}`);
    console.log(`${TERM.cyan}📂 Target File: ${TERM.bold}${filePath}${TERM.reset}`);
    console.log(`${TERM.cyan}🧠 Detected Language: ${TERM.magenta}${targetLang}${TERM.reset}`);
    
    const sourceCode = fs.readFileSync(filePath, 'utf8');

    console.log(`${TERM.cyan}🚀 Sending code to Supreme Code Architect...${TERM.reset}`);

    try {
        const response = await fetch(SERVER_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                code: sourceCode, 
                target_lang: targetLang,
                is_ci_build: true // Triggers logging to 'ci_logs' table in MySQL
            })
        });

        if (!response.ok) throw new Error(`Server responded with ${response.status}`);

        const result = await response.json();
        
        // Safety Fallback for Score
        const finalScore = (result.quality_score !== undefined && result.quality_score !== null) ? result.quality_score : 0;

        // --- 1. DISPLAY REPORT ---
        console.log(`\n${TERM.cyan}════════════════ CODESTATIC BUILD REPORT ════════════════${TERM.reset}`);

        // QUALITY SCORE VISUALIZATION
        let scoreColor = TERM.green;
        if (finalScore < 50) scoreColor = TERM.red;
        else if (finalScore < 70) scoreColor = TERM.yellow;

        console.log(`${TERM.bold}QUALITY SCORE:${TERM.reset}   ${scoreColor}${finalScore}/100${TERM.reset}`);
        console.log(`${TERM.bold}INTEGRITY:${TERM.reset}       ${result.integrity_check || "N/A"}`);
        console.log(`${TERM.bold}PLAGIARISM:${TERM.reset}      ${result.plagiarism_check || "N/A"}`);
        console.log(`${TERM.bold}COMPLEXITY:${TERM.reset}      ${result.target_complexity || "O(?)"}`);

        // ERROR TABLE SUMMARY
        const errorCount = result.error_table ? result.error_table.length : 0;
        
        // --- 2. CI/CD GATE LOGIC (UPDATED) ---
        
        if (finalScore >= 70) {
            // === SUCCESS SCENARIO ===
            console.log(`\n${TERM.green}✅ DEPLOYMENT SENTINEL: BUILD SUCCESS${TERM.reset}`);
            console.log(`${TERM.green}   Score: ${finalScore} (Threshold >= 70 passed)${TERM.reset}`);
            
            if (errorCount > 0) {
                // Treat errors as Warnings if score is high
                console.log(`\n${TERM.yellow}⚠️  WARNING: ${errorCount} Errors detected (Non-blocking due to high score):${TERM.reset}`);
                result.error_table.forEach(err => {
                    console.log(`${TERM.yellow}   [Line ${err.line}] ${err.error}${TERM.reset}`);
                });
            } else {
                console.log(`${TERM.green}   ✨ Clean build. No errors found.${TERM.reset}`);
            }
            
            console.log(`${TERM.cyan}═════════════════════════════════════════════════════════${TERM.reset}\n`);
            process.exit(0); // EXIT CODE 0 (Success)

        } else {
            // === FAILURE SCENARIO ===
            console.error(`\n${TERM.red}⛔ DEPLOYMENT SENTINEL: FAILED${TERM.reset}`);
            console.error(`${TERM.red}   FATAL: Quality Score ${finalScore} is below threshold (70).${TERM.reset}`);
            
            if (errorCount > 0) {
                console.log(`\n${TERM.bgRed}${TERM.white}${TERM.bold} 💀 CRITICAL ERRORS CAUSING FAILURE: ${TERM.reset}`);
                result.error_table.forEach(err => {
                    console.log(`${TERM.red}   [Line ${err.line}] ${err.error}${TERM.reset}`);
                });
            }
            
            console.log(`${TERM.cyan}═════════════════════════════════════════════════════════${TERM.reset}\n`);
            process.exit(1); // EXIT CODE 1 (Fail)
        }

    } catch (error) {
        console.error(`${TERM.red}❌ CI/CD SYSTEM FAILURE: ${error.message}${TERM.reset}`);
        console.error(`${TERM.yellow}Ensure local server is running on port 10000 (python run.py)${TERM.reset}`);
        process.exit(1);
    }
}

runCiCheck();