// // ==========================================
// // 1. THEME & UI UTILITIES
// // ==========================================

// function toggleTheme() {
//     const body = document.body;
//     const icon = document.getElementById('themeIcon');
    
//     body.classList.toggle('light-mode');
    
//     // Save preference
//     const isLight = body.classList.contains('light-mode');
//     localStorage.setItem('cp_theme', isLight ? 'light' : 'dark');
    
//     if (isLight) {
//         icon.classList.remove('fa-moon');
//         icon.classList.add('fa-sun');
//     } else {
//         icon.classList.remove('fa-sun');
//         icon.classList.add('fa-moon');
//     }
// }

// function togglePanel(buttonId, panelId) {
//     const btn = document.getElementById(buttonId);
//     const panel = document.getElementById(panelId);

//     if (btn && panel) {
//         btn.addEventListener("click", () => {
//             panel.style.display =
//                 panel.style.display === "flex" ? "none" : "flex";
//         });
//     }
// }

// function toggleChat() {
//     const widget = document.getElementById('chatWidget');
//     if (widget.style.display === 'flex') {
//         widget.style.display = 'none';
//     } else {
//         widget.style.display = 'flex';
//         document.getElementById('chatInput').focus();
//     }
// }

// // --- NEW FEEDBACK MODAL LOGIC ---
// function toggleFeedback() {
//     const modal = document.getElementById('feedbackModal');
//     if (!modal) return;
    
//     if (modal.classList.contains('modal-show')) {
//         modal.classList.remove('modal-show');
//         setTimeout(() => { modal.style.display = 'none'; }, 300); // Wait for fade out animation
//     } else {
//         modal.style.display = 'flex';
//         // Small delay to allow display:flex to apply before opacity transition
//         setTimeout(() => { modal.classList.add('modal-show'); }, 10);
//     }
// }

// async function submitFeedback() {
//     const msg = document.getElementById('feedbackMsg').value;
//     const rate = document.getElementById('feedbackRating').value;
//     const btn = document.querySelector('#feedbackModal button'); // Select the submit button inside modal

//     if (!msg.trim()) return alert("Please enter a message.");

//     // UI Feedback
//     const originalText = btn.innerText;
//     btn.innerText = "Sending...";
//     btn.disabled = true;

//     try {
//         const res = await fetch('/submit-feedback', {
//             method: 'POST',
//             headers: {'Content-Type': 'application/json'},
//             body: JSON.stringify({ message: msg, rating: parseInt(rate) })
//         });
        
//         if (res.ok) {
//             alert("Feedback sent successfully! Thank you.");
//             document.getElementById('feedbackMsg').value = ""; // Clear input
//             toggleFeedback(); // Close modal
//         } else {
//             alert("Error submitting feedback. Please try again.");
//         }
//     } catch (e) {
//         console.error(e);
//         alert("Network error.");
//     } finally {
//         btn.innerText = originalText; // Restore button text
//         btn.disabled = false;
//     }
// }

// // ==========================================
// // 2. EDITOR SYNC LOGIC
// // ==========================================

// function updateLineNumbers(textareaId, linesId) {
//     const textarea = document.getElementById(textareaId);
//     const linesDiv = document.getElementById(linesId);
//     if (!textarea || !linesDiv) return;
    
//     const lines = textarea.value.split('\n').length;
//     linesDiv.innerHTML = Array(lines).fill(0).map((_, i) => i + 1).join('<br>');
// }

// function syncScroll(textareaId, linesId) {
//     const textarea = document.getElementById(textareaId);
//     const linesDiv = document.getElementById(linesId);
//     if (linesDiv && textarea) {
//         linesDiv.scrollTop = textarea.scrollTop;
//     }
// }

// // ==========================================
// // 3. PROJECT MANAGEMENT & DATABASE
// // ==========================================

// async function saveCodeToDB() {
//     const el = document.getElementById("codeInput") || document.getElementById("inputCode");
//     const code = el.value.trim();
//     const language = document.getElementById("languageSelect") ? document.getElementById("languageSelect").value : document.getElementById("targetLang").value;

//     if (!code) return;

//     try {
//         await fetch("/save-code", {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({ code, language })
//         });
//     } catch (err) {
//         console.error("Auto-save failed", err);
//     }
// }

// async function loadLastSavedCode() {
//     try {
//         const res = await fetch("/load-last-code");
//         const data = await res.json();

//         if (data.status === "success" && data.data) {
//             const codeInput = document.getElementById("codeInput") || document.getElementById("inputCode");
//             const langSelect = document.getElementById("languageSelect") || document.getElementById("targetLang");
            
//             if(codeInput) {
//                 codeInput.value = data.data.code;
//                 codeInput.dispatchEvent(new Event('input'));
//             }
//             if(langSelect) {
//                 langSelect.value = data.data.language;
//             }
//             // Auto-run removed: User must manually click "Run Assessment"
//         }
//     } catch (err) {
//         console.error("Error loading last code", err);
//     }
// }

// async function saveProject() {
//     const name = prompt("Enter project name:");
//     if (!name) return;

//     const el = document.getElementById("codeInput") || document.getElementById("inputCode");
//     const code = el.value.trim();
//     const language = document.getElementById("languageSelect") ? document.getElementById("languageSelect").value : document.getElementById("targetLang").value;

//     try {
//         const res = await fetch("/save-project", {
//             method: "POST",
//             headers: { "Content-Type": "application/json" },
//             // Bundle the lastReportData snapshot with the save request!
//             body: JSON.stringify({ 
//                 projectName: name, 
//                 code: code, 
//                 language: language,
//                 report_data: typeof lastReportData !== 'undefined' ? lastReportData : null
//             })
//         });

//         const data = await res.json();

//         if (data.status === "success") {
//             alert("Project & Analysis Snapshot saved successfully!");
//             loadProjects();
//         }
//     } catch (err) {
//         console.error("Error saving project", err);
//     }
// }

// async function loadProjects() {
//     const list = document.getElementById("projectList");
//     if (!list) return;

//     try {
//         const res = await fetch("/projects");
//         const data = await res.json();

//         list.innerHTML = "";

//         // MONGODB FIX: Wrapped ${p.id} in quotes because Mongo IDs are strings
//         data.projects.forEach(p => {
//             list.innerHTML += `
//                 <div class="project-item">
//                     <h4>${p.project_name}</h4>
//                     <div class="project-actions">
//                         <button onclick="loadProject('${p.id}')">Load</button>
//                         <button onclick="favoriteProject('${p.id}', ${p.is_favorite ? 0 : 1})">
//                             ${p.is_favorite ? "Unfav" : "Fav"}
//                         </button>
//                         <button onclick="deleteProject('${p.id}')">Del</button>
//                     </div>
//                 </div>`;
//         });

//     } catch (err) {
//         console.error("Error loading projects", err);
//     }
// }

// async function loadProject(id) {
//     try {
//         const res = await fetch("/projects");
//         const data = await res.json();

//         // Match the project using the MongoDB string ID
//         const project = data.projects.find(p => p.id === id);
//         if (!project) return;

//         const codeInput = document.getElementById("codeInput") || document.getElementById("inputCode");
//         const langSelect = document.getElementById("languageSelect") || document.getElementById("targetLang");

//         // 1. Restore original code
//         if (codeInput) {
//             codeInput.value = project.code;
//             codeInput.dispatchEvent(new Event('input'));
//         }
//         if (langSelect) {
//             langSelect.value = project.language;
//         }

//         // 2. OFFLINE SNAPSHOT RESTORATION
//         // If this project was saved with an analysis snapshot, restore the UI instantly!
//         if (project.report_data) {
//             console.log("Restoring saved analysis state offline...");
//             const report = project.report_data;
//             lastReportData = report; // Re-bind it so PDF downloads still work!

//             // Restore Output Code
//             const outputBox = document.getElementById('outputCode');
//             if (outputBox) {
//                 outputBox.value = report.final_code || "// No fix generated";
//                 updateLineNumbers('outputCode', 'outputLines');
//             }

//             // Restore Badges & Scores
//             const detectedBadge = document.getElementById('detectedLang');
//             const integrityBadge = document.getElementById('integrityCheck');
//             const qualityScoreDisplay = document.getElementById('qualityScoreDisplay'); 
//             const plagiarismCheck = document.getElementById('plagiarismCheck');
//             const complianceStatus = document.getElementById('complianceStatus');

//             if (detectedBadge) detectedBadge.innerText = report.detected_language || project.language;
//             if (integrityBadge) integrityBadge.innerText = "Integrity: " + (report.integrity_check || "--");
//             if (qualityScoreDisplay) qualityScoreDisplay.innerHTML = `<i class="fas fa-star"></i> Quality Score: ${report.quality_score || 0}/100`;
            
//             if (plagiarismCheck) {
//                 plagiarismCheck.innerHTML = `<i class="fas fa-shield-alt"></i> Plagiarism Check: ${report.plagiarism_check || "N/A"}`;
//                 plagiarismCheck.className = (report.plagiarism_check && report.plagiarism_check.toLowerCase().includes("high match")) 
//                     ? 'plagiarism-high' : 'plagiarism-low';
//             }

//             // Restore Critical Error Log Table
//             const errorTableBody = document.querySelector('#errorTable tbody');
//             let errorCount = 0;
//             if (report.error_table && report.error_table.length > 0) {
//                 errorCount = report.error_table.length;
//                 if(errorTableBody) {
//                     errorTableBody.innerHTML = "";
//                     report.error_table.forEach(err => {
//                         errorTableBody.innerHTML += `<tr><td><strong>${err.line}</strong></td><td><strong>${err.error}</strong></td></tr>`;
//                     });
//                 }
//             } else if (errorTableBody) {
//                 errorTableBody.innerHTML = `<tr><td colspan="2">No critical errors found.</td></tr>`;
//             }

//             // Restore Line-by-Line Explanation Table
//             const explanationTableBody = document.querySelector('#explanationTable tbody');
//             if (report.code_explanation && report.code_explanation.length > 0) {
//                 if(explanationTableBody) {
//                     explanationTableBody.innerHTML = "";
//                     report.code_explanation.forEach(item => {
//                         explanationTableBody.innerHTML += `<tr><td><strong>${item.code}</strong></td><td><strong>${item.explanation}</strong></td></tr>`;
//                     });
//                 }
//             }

//             // Restore Time & Space Complexity
//             if (report.complexity) {
//                 const t = report.complexity.time;
//                 const s = report.complexity.space;
                
//                 if(t && document.getElementById('timeBest')) {
//                     document.getElementById('timeBest').innerHTML = `<strong>${t.best}</strong>`;
//                     document.getElementById('timeAvg').innerHTML = `<strong>${t.average}</strong>`;
//                     document.getElementById('timeWorst').innerHTML = `<strong>${t.worst}</strong>`;
//                     if(document.getElementById('timeDesc')) document.getElementById('timeDesc').innerHTML = `<strong>${t.desc}</strong>`;
//                 }
//                 if(s && document.getElementById('spaceBest')) {
//                     document.getElementById('spaceBest').innerHTML = `<strong>${s.best}</strong>`;
//                     document.getElementById('spaceAvg').innerHTML = `<strong>${s.average}</strong>`;
//                     document.getElementById('spaceWorst').innerHTML = `<strong>${s.worst}</strong>`;
//                     if(document.getElementById('spaceDesc')) document.getElementById('spaceDesc').innerHTML = `<strong>${s.desc}</strong>`;
//                 }
//             }

//             // Restore Deployment Sentinel (CI/CD) Status
//             const score = report.quality_score || 0;
//             const passed = score >= 70;
//             const ciBadge = document.getElementById('ciStatusBadge');
//             const ciText = document.getElementById('ciStatusText');
//             const ciConsole = document.getElementById('ciConsoleOutput');

//             if (ciBadge) {
//                 ciBadge.innerText = passed ? "PASSED" : "FAILED";
//                 ciBadge.className = passed ? "ci-badge ci-pass" : "ci-badge ci-fail";
//                 ciBadge.style.border = "none";
//                 ciBadge.style.color = passed ? "#22c55e" : "#ef4444";
                
//                 let consoleHtml = `$ codestatic-ci --verify<br>`;
//                 if (passed) {
//                     ciText.innerHTML = `Build Allowed. Quality Score <b>${score}</b> passed threshold (70).`;
//                     consoleHtml += `<span style="color:#22c55e">> SUCCESS: Code passed deployment gates.</span><br>`;
//                     consoleHtml += errorCount > 0 ? `<span style="color:#eab308">> WARNING: ${errorCount} Errors (Non-blocking).</span>` : `<span style="color:#22c55e">> CLEAN BUILD.</span>`;
//                 } else {
//                     ciText.innerHTML = `Build Blocked. Quality Score <b>${score}</b> is too low.`;
//                     consoleHtml += `<span style="color:#ef4444">> FATAL: Score ${score} < 70.</span><br>`;
//                     consoleHtml += `<span style="color:#ef4444">> EXIT CODE 1 (Build Aborted)</span>`;
//                 }
//                 if(ciConsole) ciConsole.innerHTML = consoleHtml;
//             }

//             if(complianceStatus) {
//                  complianceStatus.innerHTML = passed ? `<i class="fas fa-check-circle"></i> Compliance: PASS` : `<i class="fas fa-exclamation-triangle"></i> Compliance: FAIL`;
//                  complianceStatus.className = passed ? "compliance-pass" : "compliance-fail";
//             }
//         } else {
//             console.log("No snapshot found. Only raw code restored.");
//         }

//     } catch (err) {
//         console.error("Error loading project:", err);
//     }
// }

// async function favoriteProject(id, fav) {
//     await fetch("/favorite-project", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ id, fav })
//     });
//     loadProjects();
// }

// async function deleteProject(id) {
//     if(!confirm("Are you sure you want to delete this project?")) return;
    
//     await fetch("/delete-project", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ id })
//     });
//     loadProjects();
// }
// // ==========================================
// // 4. CHAT SYSTEM
// // ==========================================

// async function loadSavedChat() {
//     try {
//         const res = await fetch("/load-chat");
//         const data = await res.json();

//         const chatBody = document.getElementById('chatBody');
//         if (!chatBody) return;

//         if (data.status === "success") {
//             data.chat.forEach(msg => {
//                 if(msg.user_message) chatBody.innerHTML += `<div class="chat-msg user-msg">${msg.user_message}</div>`;
//                 if(msg.ai_response) chatBody.innerHTML += `<div class="chat-msg ai-msg">${msg.ai_response.replace(/\n/g, '<br>')}</div>`;
//             });
//             chatBody.scrollTop = chatBody.scrollHeight;
//         }
//     } catch (err) {
//         console.error("Chat load failed", err);
//     }
// }

// async function sendChatMessage() {
//     const input = document.getElementById('chatInput');
//     const msg = input.value.trim();
//     const chatBody = document.getElementById('chatBody');
//     const currentCode = document.getElementById('inputCode') ? document.getElementById('inputCode').value : document.getElementById('codeInput').value;

//     if (!msg) return;

//     chatBody.innerHTML += `<div class="chat-msg user-msg">${msg}</div>`;
//     input.value = '';
//     chatBody.scrollTop = chatBody.scrollHeight;

//     const loadingDiv = document.createElement('div');
//     loadingDiv.className = 'chat-msg ai-msg';
//     loadingDiv.innerText = 'Thinking...';
//     chatBody.appendChild(loadingDiv);

//     try {
//         const response = await fetch('/ai_chat', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ message: msg, code_context: currentCode })
//         });
//         const data = await response.json();
        
//         chatBody.removeChild(loadingDiv);

//         if(data.status === 'success') {
//             const reply = data.reply.replace(/\n/g, '<br>');
//             chatBody.innerHTML += `<div class="chat-msg ai-msg">${reply}</div>`;
//         } else {
//             chatBody.innerHTML += `<div class="chat-msg ai-msg" style="color:red">Error: ${data.message}</div>`;
//         }
//     } catch(err) {
//         chatBody.removeChild(loadingDiv);
//         chatBody.innerHTML += `<div class="chat-msg ai-msg" style="color:red">Network Error</div>`;
//     }
//     chatBody.scrollTop = chatBody.scrollHeight;
// }

// function handleChatEnter(e) {
//     if (e.key === 'Enter' && !e.shiftKey) {
//         e.preventDefault(); 
//         sendChatMessage();
//     }
// }

// // ==========================================
// // 5. LAYOUT RESIZER
// // ==========================================

// const gutter = document.getElementById('resizeHandle');
// const colLeft = document.getElementById('colLeft');
// const container = document.getElementById('mainContainer');
// let isResizing = false;

// if (gutter && colLeft && container) {
//     gutter.addEventListener('mousedown', (e) => {
//         isResizing = true;
//         document.body.style.cursor = 'col-resize';
//     });

//     document.addEventListener('mousemove', (e) => {
//         if (!isResizing) return;
//         const containerWidth = container.offsetWidth;
//         const newLeftWidth = (e.clientX / containerWidth) * 100;
//         if (newLeftWidth > 10 && newLeftWidth < 90) {
//             colLeft.style.width = `${newLeftWidth}%`;
//         }
//     });

//     document.addEventListener('mouseup', () => {
//         if(isResizing) {
//             isResizing = false;
//             document.body.style.cursor = 'default';
//         }
//     });
// }
// // ==========================================
// // 6. CODE ASSESSMENT & ANALYSIS API
// // ==========================================

// let lastReportData = null; 

// async function handleAssessment() {
//     const inputCode = document.getElementById('inputCode') ? document.getElementById('inputCode').value : "";
//     const targetLang = document.getElementById('targetLang') ? document.getElementById('targetLang').value : "Python";
    
//     // --- 1. GET OVERLAY ELEMENT ---
//     const overlay = document.getElementById('loadingOverlay');
    
//     // --- 2. ACTIVATE BLUR OVERLAY (The Update) ---
//     if (overlay) {
//         overlay.style.display = "flex";           // Show it
//         overlay.style.backdropFilter = "blur(15px)"; // FORCE BLUR EFFECT
//         overlay.style.webkitBackdropFilter = "blur(15px)"; // Safari support
//         overlay.style.zIndex = "10000";           // Ensure it's on top of everything
//     }

//     if (!inputCode.trim()) {
//         alert("Please input code.");
//         if (overlay) overlay.style.display = "none";
//         return;
//     }

//     // UI References
//     const errorTableBody = document.querySelector('#errorTable tbody');
//     const explanationTableBody = document.querySelector('#explanationTable tbody');
//     const outputBox = document.getElementById('outputCode');
    
//     // UI Metrics
//     const integrityBadge = document.getElementById('integrityCheck');
//     const detectedBadge = document.getElementById('detectedLang');
//     const plagiarismCheck = document.getElementById('plagiarismCheck');
//     const qualityScoreDisplay = document.getElementById('qualityScoreDisplay'); 
//     const complianceStatus = document.getElementById('complianceStatus');

//     // Complexity References
//     const timeBest = document.getElementById('timeBest');
//     const timeAvg = document.getElementById('timeAvg');
//     const timeWorst = document.getElementById('timeWorst');
//     const timeDesc = document.getElementById('timeDesc');
//     const spaceBest = document.getElementById('spaceBest');
//     const spaceAvg = document.getElementById('spaceAvg');
//     const spaceWorst = document.getElementById('spaceWorst');
//     const spaceDesc = document.getElementById('spaceDesc');

//     // Sentinel References
//     const ciBadge = document.getElementById('ciStatusBadge');
//     const ciText = document.getElementById('ciStatusText');
//     const ciConsole = document.getElementById('ciConsoleOutput');

//     try {
//         console.log("🚀 Sending request to /process_code...");
        
//         // --- 3. PERFORM ANALYSIS ---
//         const response = await fetch('/process_code', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ code: inputCode, target_lang: targetLang })
//         });
//         const data = await response.json();
//         console.log("✅ Data received:", data); 

//         if (data.status === "error") {
//             if (outputBox) outputBox.value = "Error: " + data.message;
//             return;
//         }

//         // --- 4. UPDATE UI (Keep everything same as before) ---
//         if (outputBox) {
//             outputBox.value = data.final_code || "// No fix generated";
//             updateLineNumbers('outputCode', 'outputLines');
//         }

//         // Basic Metrics
//         if (detectedBadge) detectedBadge.innerText = data.detected_language || "Unknown";
//         if (integrityBadge) integrityBadge.innerText = "Integrity: " + (data.integrity_check || "--");
//         if (qualityScoreDisplay) qualityScoreDisplay.innerHTML = `<i class="fas fa-star"></i> Quality Score: ${data.quality_score || 0}/100`;
        
//         // Plagiarism
//         if (plagiarismCheck) {
//             plagiarismCheck.innerHTML = `<i class="fas fa-shield-alt"></i> Plagiarism Check: ${data.plagiarism_check || "N/A"}`;
//             plagiarismCheck.className = (data.plagiarism_check && data.plagiarism_check.toLowerCase().includes("high match")) 
//                 ? 'plagiarism-high' : 'plagiarism-low';
//         }

//         // Update Tables & PDF Data (Preserved from your code)
//         let pdfErrorLog = "No critical errors found.";
//         let errorCount = 0;
//         let errorsListForConsole = "";
        
//         if (data.error_table && data.error_table.length > 0) {
//             errorCount = data.error_table.length;
//             if(errorTableBody) {
//                 errorTableBody.innerHTML = "";
//                 data.error_table.forEach(err => {
//                     errorTableBody.innerHTML += `<tr><td><strong>${err.line}</strong></td><td><strong>${err.error}</strong></td></tr>`;
//                     errorsListForConsole += `   [Line ${err.line}] ${err.error}<br>`;
//                 });
//             }
//             pdfErrorLog = data.error_table.map(e => `[Line ${e.line}] ${e.error}`).join("\n");
//         } else if(errorTableBody) {
//             errorTableBody.innerHTML = `<tr><td colspan="2">No critical errors found.</td></tr>`;
//         }

//         let pdfExplanation = "No explanation provided.";
//         if (data.code_explanation && data.code_explanation.length > 0) {
//             if(explanationTableBody) {
//                 explanationTableBody.innerHTML = "";
//                 data.code_explanation.forEach(item => {
//                     explanationTableBody.innerHTML += `<tr><td><strong>${item.code}</strong></td><td><strong>${item.explanation}</strong></td></tr>`;
//                 });
//             }
//             pdfExplanation = data.code_explanation.map(e => `[${e.code}]\n -> ${e.explanation}`).join("\n\n");
//         }

//         let pdfTime = "N/A", pdfSpace = "N/A";
//         if (data.complexity) {
//             const t = data.complexity.time;
//             const s = data.complexity.space;
            
//             if(t && timeBest) {
//                 timeBest.innerHTML = `<strong>${t.best}</strong>`;
//                 timeAvg.innerHTML = `<strong>${t.average}</strong>`;
//                 timeWorst.innerHTML = `<strong>${t.worst}</strong>`;
//                 if(timeDesc) timeDesc.innerHTML = `<strong>${t.desc}</strong>`;
//                 pdfTime = `Time Complexity:\nBest: ${t.best}\nAvg: ${t.average}\nWorst: ${t.worst}\n\nDetails: ${t.desc}`;
//             }
//             if(s && spaceBest) {
//                 spaceBest.innerHTML = `<strong>${s.best}</strong>`;
//                 spaceAvg.innerHTML = `<strong>${s.average}</strong>`;
//                 spaceWorst.innerHTML = `<strong>${s.worst}</strong>`;
//                 if(spaceDesc) spaceDesc.innerHTML = `<strong>${s.desc}</strong>`;
//                 pdfSpace = `Space Complexity:\nBest: ${s.best}\nAvg: ${s.average}\nWorst: ${s.worst}\n\nDetails: ${s.desc}`;
//             }
//         }

//         // Sentinel UI
//         const score = data.quality_score || 0;
//         const passed = score >= 70;
        
//         if (ciBadge) {
//             ciBadge.innerText = passed ? "PASSED" : "FAILED";
//             ciBadge.className = passed ? "ci-badge ci-pass" : "ci-badge ci-fail";
//             ciBadge.style.border = "none";
//             ciBadge.style.color = passed ? "#22c55e" : "#ef4444";
            
//             let consoleHtml = `$ codestatic-ci --verify<br>`;
//             if (passed) {
//                 ciText.innerHTML = `Build Allowed. Quality Score <b>${score}</b> passed threshold (70).`;
//                 consoleHtml += `<span style="color:#22c55e">> SUCCESS: Code passed deployment gates.</span><br>`;
//                 consoleHtml += errorCount > 0 ? `<span style="color:#eab308">> WARNING: ${errorCount} Errors (Non-blocking).</span>` : `<span style="color:#22c55e">> CLEAN BUILD.</span>`;
//             } else {
//                 ciText.innerHTML = `Build Blocked. Quality Score <b>${score}</b> is too low.`;
//                 consoleHtml += `<span style="color:#ef4444">> FATAL: Score ${score} < 70.</span><br>`;
//                 consoleHtml += `<span style="color:#ef4444">> EXIT CODE 1 (Build Aborted)</span>`;
//             }
//             ciConsole.innerHTML = consoleHtml;
//         }

//         if(complianceStatus) {
//              complianceStatus.innerHTML = passed ? `<i class="fas fa-check-circle"></i> Compliance: PASS` : `<i class="fas fa-exclamation-triangle"></i> Compliance: FAIL`;
//              complianceStatus.className = passed ? "compliance-pass" : "compliance-fail";
//         }

//         // Save for PDF
//         lastReportData = {
//             ...data,
//             original_code: inputCode,
//             error_log_text: pdfErrorLog, 
//             explanation_text: pdfExplanation,
//             time_analysis: pdfTime,
//             space_analysis: pdfSpace
//         };

//     } catch (err) {
//         console.error("Analysis Failed:", err);
//         alert("Analysis failed. Check console.");
//     } finally {
//         // --- 5. HIDE BLUR OVERLAY (Only removes after everything is done) ---
//         if (overlay) overlay.style.display = "none";
//     }
// }
// // ==========================================
// // 7. REPORTING & UTILITIES
// // ==========================================

// async function downloadPdf() {
//     if (!lastReportData) {
//         alert("No data found. Please run 'Run Analysis' first.");
//         return;
//     }

//     console.log("📤 Sending PDF Data:", lastReportData);

//     const btn = document.querySelector('.pdf-nav-btn');
//     if(btn) btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i>`;

//     try {
//         const response = await fetch('/generate_pdf', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(lastReportData)
//         });

//         if (response.ok) {
//             const blob = await response.blob();
//             const url = window.URL.createObjectURL(blob);
//             const a = document.createElement('a');
//             a.href = url;
//             a.download = `CodeStatic_Report_${Date.now()}.pdf`;
//             document.body.appendChild(a);
//             a.click();
//             a.remove();
//         } else {
//             const text = await response.text();
//             console.error("PDF Server Error:", text);
//             alert("PDF Generation Failed: " + text);
//         }
//     } catch (e) {
//         console.error("Network Error:", e);
//         alert("Network Error generating PDF.");
//     } finally {
//         if(btn) btn.innerHTML = `<i class="fas fa-file-pdf"></i>`;
//     }
// }

// // --- Real Copy Utilities ---

// function copyContent(id) {
//     const el = document.getElementById(id);
//     if(el) {
//         el.select();
//         navigator.clipboard.writeText(el.value);
//         alert("Code Copied!");
//     }
// }

// function copyTable() {
//     const rows = document.querySelectorAll('#errorTable tbody tr');
//     let text = "--- CODESTATIC CRITICAL ERROR LOG ---\n";
//     if(rows.length === 0 || rows[0].innerText.includes("No critical errors")) {
//         text += "No critical errors found.";
//     } else {
//         rows.forEach(row => {
//             text += row.innerText.replace(/\t/g, " | ") + "\n";
//         });
//     }
//     navigator.clipboard.writeText(text);
//     alert("Critical Log Copied!");
// }

// function copyExplanationTable() {
//     const rows = document.querySelectorAll('#explanationTable tbody tr');
//     let text = "--- CODESTATIC LINE EXPLANATION ---\n";
//     rows.forEach(row => {
//         text += row.innerText.replace(/\t/g, " | ") + "\n";
//     });
//     navigator.clipboard.writeText(text);
//     alert("Explanation Copied!");
// }

// function copyComplexity() {
//     const timeBest = document.getElementById('timeBest').innerText;
//     const timeAvg = document.getElementById('timeAvg').innerText;
//     const timeWorst = document.getElementById('timeWorst').innerText;
//     const timeDesc = document.getElementById('timeDesc').innerText;
    
//     const spaceBest = document.getElementById('spaceBest').innerText;
//     const spaceAvg = document.getElementById('spaceAvg').innerText;
//     const spaceWorst = document.getElementById('spaceWorst').innerText;
//     const spaceDesc = document.getElementById('spaceDesc').innerText;

//     const text = `--- COMPLEXITY ANALYSIS ---\n\nTIME COMPLEXITY:\nBest: ${timeBest}\nAverage: ${timeAvg}\nWorst: ${timeWorst}\nDetails: ${timeDesc}\n\nSPACE COMPLEXITY:\nBest: ${spaceBest}\nAverage: ${spaceAvg}\nWorst: ${spaceWorst}\nDetails: ${spaceDesc}`;
    
//     navigator.clipboard.writeText(text);
//     alert("Complexity Log Copied!");
// }

// function copyCICDLog() {
//     const badge = document.getElementById('ciStatusBadge');
//     const textDetails = document.getElementById('ciStatusText');
//     const consoleOut = document.getElementById('ciConsoleOutput');

//     if(!badge || !textDetails || !consoleOut) {
//         alert("Run an assessment first to generate CI logs.");
//         return;
//     }

//     const text = `--- DEPLOYMENT SENTINEL (CI/CD) ---\nSTATUS: ${badge.innerText}\nDETAILS: ${textDetails.innerText}\n\nCONSOLE OUTPUT:\n${consoleOut.innerText}`;
//     navigator.clipboard.writeText(text);
//     alert("Deployment Sentinel Log Copied!");
// }

// // ==========================================
// // 8. INIT
// // ==========================================
// togglePanel("projectsButton", "projectsPanel");
// document.addEventListener('DOMContentLoaded', () => {
//     // Restore Theme
//     const storedTheme = localStorage.getItem('cp_theme');
//     if (storedTheme === 'light') {
//         document.body.classList.add('light-mode');
//         const icon = document.getElementById('themeIcon');
//         if(icon) {
//             icon.classList.remove('fa-moon');
//             icon.classList.add('fa-sun');
//         }
//     }

//     loadLastSavedCode();
//     loadProjects();
//     loadSavedChat();
//     const codeInput = document.getElementById("codeInput") || document.getElementById("inputCode");
//     if (codeInput) codeInput.addEventListener('keyup', saveCodeToDB);
// });
//----------------------------------------------------------------------------------------------------------------------------------
// ==========================================
// 1. THEME & UI UTILITIES
// ==========================================

function toggleTheme() {
    const body = document.body;
    const icon = document.getElementById('themeIcon');
    
    body.classList.toggle('light-mode');
    
    // Save preference
    const isLight = body.classList.contains('light-mode');
    localStorage.setItem('cp_theme', isLight ? 'light' : 'dark');
    
    if (isLight) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
}

function togglePanel(buttonId, panelId) {
    const btn = document.getElementById(buttonId);
    const panel = document.getElementById(panelId);

    if (btn && panel) {
        btn.addEventListener("click", () => {
            panel.style.display =
                panel.style.display === "flex" ? "none" : "flex";
        });
    }
}

function toggleChat() {
    const widget = document.getElementById('chatWidget');
    if (widget.style.display === 'flex') {
        widget.style.display = 'none';
    } else {
        widget.style.display = 'flex';
        document.getElementById('chatInput').focus();
    }
}

// --- NEW FEEDBACK MODAL LOGIC ---
function toggleFeedback() {
    const modal = document.getElementById('feedbackModal');
    if (!modal) return;
    
    if (modal.classList.contains('modal-show')) {
        modal.classList.remove('modal-show');
        setTimeout(() => { modal.style.display = 'none'; }, 300); // Wait for fade out animation
    } else {
        modal.style.display = 'flex';
        // Small delay to allow display:flex to apply before opacity transition
        setTimeout(() => { modal.classList.add('modal-show'); }, 10);
    }
}

async function submitFeedback() {
    const msg = document.getElementById('feedbackMsg').value;
    const rate = document.getElementById('feedbackRating').value;
    const btn = document.querySelector('#feedbackModal button'); // Select the submit button inside modal

    if (!msg.trim()) return alert("Please enter a message.");

    // UI Feedback
    const originalText = btn.innerText;
    btn.innerText = "Sending...";
    btn.disabled = true;

    try {
        const res = await fetch('/submit-feedback', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: msg, rating: parseInt(rate) })
        });
        
        if (res.ok) {
            alert("Feedback sent successfully! Thank you.");
            document.getElementById('feedbackMsg').value = ""; // Clear input
            toggleFeedback(); // Close modal
        } else {
            alert("Error submitting feedback. Please try again.");
        }
    } catch (e) {
        console.error(e);
        alert("Network error.");
    } finally {
        btn.innerText = originalText; // Restore button text
        btn.disabled = false;
    }
}

// ==========================================
// 2. EDITOR SYNC LOGIC
// ==========================================

function updateLineNumbers(textareaId, linesId) {
    const textarea = document.getElementById(textareaId);
    const linesDiv = document.getElementById(linesId);
    if (!textarea || !linesDiv) return;
    
    const lines = textarea.value.split('\n').length;
    linesDiv.innerHTML = Array(lines).fill(0).map((_, i) => i + 1).join('<br>');
}

function syncScroll(textareaId, linesId) {
    const textarea = document.getElementById(textareaId);
    const linesDiv = document.getElementById(linesId);
    if (linesDiv && textarea) {
        linesDiv.scrollTop = textarea.scrollTop;
    }
}

// ==========================================
// 3. PROJECT MANAGEMENT & DATABASE
// ==========================================

async function saveCodeToDB() {
    const el = document.getElementById("inputCode") || document.getElementById("codeInput");
    const code = el.value.trim();
    const language = document.getElementById("targetLang") ? document.getElementById("targetLang").value : document.getElementById("languageSelect").value;

    if (!code) return;

    try {
        await fetch("/save-code", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, language })
        });
    } catch (err) {
        console.error("Auto-save failed", err);
    }
}

async function loadLastSavedCode() {
    try {
        const res = await fetch("/load-last-code");
        const data = await res.json();

        if (data.status === "success" && data.data) {
            const codeInput = document.getElementById("inputCode") || document.getElementById("codeInput");
            const langSelect = document.getElementById("targetLang") || document.getElementById("languageSelect");
            
            if(codeInput) {
                codeInput.value = data.data.code;
                codeInput.dispatchEvent(new Event('input'));
            }
            if(langSelect) {
                langSelect.value = data.data.language;
            }
        }
    } catch (err) {
        console.error("Error loading last code", err);
    }
}

async function saveProject() {
    const name = prompt("Enter project name:");
    if (!name) return;

    const el = document.getElementById("inputCode") || document.getElementById("codeInput");
    const code = el.value.trim();
    const language = document.getElementById("targetLang") ? document.getElementById("targetLang").value : document.getElementById("languageSelect").value;

    try {
        const res = await fetch("/save-project", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // Bundle the lastReportData snapshot with the save request!
            body: JSON.stringify({ 
                projectName: name, 
                code: code, 
                language: language,
                report_data: typeof lastReportData !== 'undefined' ? lastReportData : null
            })
        });

        const data = await res.json();

        if (data.status === "success") {
            alert("Project & Analysis Snapshot saved successfully!");
            loadProjects();
        }
    } catch (err) {
        console.error("Error saving project", err);
    }
}

async function loadProjects() {
    const list = document.getElementById("projectList");
    if (!list) return;

    try {
        const res = await fetch("/projects");
        const data = await res.json();

        list.innerHTML = "";

        // UPDATE: Secure DOM element creation (Prevents XSS)
        data.projects.forEach(p => {
            const item = document.createElement('div');
            item.className = 'project-item';
            item.innerHTML = `
                <h4 id="title-${p.id}"></h4>
                <div class="project-actions">
                    <button onclick="loadProject('${p.id}')">Load</button>
                    <button onclick="favoriteProject('${p.id}', ${p.is_favorite ? 0 : 1})">
                        ${p.is_favorite ? "Unfav" : "Fav"}
                    </button>
                    <button onclick="deleteProject('${p.id}')">Del</button>
                </div>`;
            
            list.appendChild(item);
            // .textContent treats data as safe text, not HTML
            document.getElementById(`title-${p.id}`).textContent = p.project_name;
        });

    } catch (err) {
        console.error("Error loading projects", err);
    }
}

async function loadProject(id) {
    try {
        const res = await fetch("/projects");
        const data = await res.json();

        // Match the project using the MongoDB string ID
        const project = data.projects.find(p => p.id === id);
        if (!project) return;

        const codeInput = document.getElementById("inputCode") || document.getElementById("codeInput");
        const langSelect = document.getElementById("targetLang") || document.getElementById("languageSelect");

        // 1. Restore original code
        if (codeInput) {
            codeInput.value = project.code;
            codeInput.dispatchEvent(new Event('input'));
        }
        if (langSelect) {
            langSelect.value = project.language;
        }

        // 2. OFFLINE SNAPSHOT RESTORATION
        // If this project was saved with an analysis snapshot, restore the UI instantly!
        if (project.report_data) {
            console.log("Restoring saved analysis state offline...");
            const report = project.report_data;
            lastReportData = report; // Re-bind it so PDF downloads still work!

            // Restore Output Code
            const outputBox = document.getElementById('outputCode');
            if (outputBox) {
                outputBox.value = report.final_code || "// No fix generated";
                updateLineNumbers('outputCode', 'outputLines');
            }

            // Restore Badges & Scores
            const detectedBadge = document.getElementById('detectedLang');
            const integrityBadge = document.getElementById('integrityCheck');
            const qualityScoreDisplay = document.getElementById('qualityScoreDisplay'); 
            const plagiarismCheck = document.getElementById('plagiarismCheck');
            const complianceStatus = document.getElementById('complianceStatus');

            if (detectedBadge) detectedBadge.innerText = report.detected_language || project.language;
            if (integrityBadge) integrityBadge.innerText = "Integrity: " + (report.integrity_check || "--");
            if (qualityScoreDisplay) qualityScoreDisplay.innerHTML = `<i class="fas fa-star"></i> Quality Score: ${report.quality_score || 0}/100`;
            
            if (plagiarismCheck) {
                plagiarismCheck.innerHTML = `<i class="fas fa-shield-alt"></i> Plagiarism Check: ${report.plagiarism_check || "N/A"}`;
                plagiarismCheck.className = (report.plagiarism_check && report.plagiarism_check.toLowerCase().includes("high match")) 
                    ? 'plagiarism-high' : 'plagiarism-low';
            }

            // Restore Critical Error Log Table
            const errorTableBody = document.querySelector('#errorTable tbody');
            let errorCount = 0;
            if (report.error_table && report.error_table.length > 0) {
                errorCount = report.error_table.length;
                if(errorTableBody) {
                    errorTableBody.innerHTML = "";
                    report.error_table.forEach(err => {
                        errorTableBody.innerHTML += `<tr><td><strong>${err.line}</strong></td><td><strong>${err.error}</strong></td></tr>`;
                    });
                }
            } else if (errorTableBody) {
                errorTableBody.innerHTML = `<tr><td colspan="2">No critical errors found.</td></tr>`;
            }

            // Restore Line-by-Line Explanation Table
            const explanationTableBody = document.querySelector('#explanationTable tbody');
            if (report.code_explanation && report.code_explanation.length > 0) {
                if(explanationTableBody) {
                    explanationTableBody.innerHTML = "";
                    report.code_explanation.forEach(item => {
                        explanationTableBody.innerHTML += `<tr><td><strong>${item.code}</strong></td><td><strong>${item.explanation}</strong></td></tr>`;
                    });
                }
            }

            // Restore Time & Space Complexity
            if (report.complexity) {
                const t = report.complexity.time;
                const s = report.complexity.space;
                
                if(t && document.getElementById('timeBest')) {
                    document.getElementById('timeBest').innerHTML = `<strong>${t.best}</strong>`;
                    document.getElementById('timeAvg').innerHTML = `<strong>${t.average}</strong>`;
                    document.getElementById('timeWorst').innerHTML = `<strong>${t.worst}</strong>`;
                    if(document.getElementById('timeDesc')) document.getElementById('timeDesc').innerHTML = `<strong>${t.desc}</strong>`;
                }
                if(s && document.getElementById('spaceBest')) {
                    document.getElementById('spaceBest').innerHTML = `<strong>${s.best}</strong>`;
                    document.getElementById('spaceAvg').innerHTML = `<strong>${s.average}</strong>`;
                    document.getElementById('spaceWorst').innerHTML = `<strong>${s.worst}</strong>`;
                    if(document.getElementById('spaceDesc')) document.getElementById('spaceDesc').innerHTML = `<strong>${s.desc}</strong>`;
                }
            }

            // Restore Deployment Sentinel (CI/CD) Status
            const score = report.quality_score || 0;
            const passed = score >= 70;
            const ciBadge = document.getElementById('ciStatusBadge');
            const ciText = document.getElementById('ciStatusText');
            const ciConsole = document.getElementById('ciConsoleOutput');

            if (ciBadge) {
                ciBadge.innerText = passed ? "PASSED" : "FAILED";
                ciBadge.className = passed ? "ci-badge ci-pass" : "ci-badge ci-fail";
                ciBadge.style.border = "none";
                ciBadge.style.color = passed ? "#22c55e" : "#ef4444";
                
                let consoleHtml = `$ codestatic-ci --verify<br>`;
                if (passed) {
                    ciText.innerHTML = `Build Allowed. Quality Score <b>${score}</b> passed threshold (70).`;
                    consoleHtml += `<span style="color:#22c55e">> SUCCESS: Code passed deployment gates.</span><br>`;
                    consoleHtml += errorCount > 0 ? `<span style="color:#eab308">> WARNING: ${errorCount} Errors (Non-blocking).</span>` : `<span style="color:#22c55e">> CLEAN BUILD.</span>`;
                } else {
                    ciText.innerHTML = `Build Blocked. Quality Score <b>${score}</b> is too low.`;
                    consoleHtml += `<span style="color:#ef4444">> FATAL: Score ${score} < 70.</span><br>`;
                    consoleHtml += `<span style="color:#ef4444">> EXIT CODE 1 (Build Aborted)</span>`;
                }
                if(ciConsole) ciConsole.innerHTML = consoleHtml;
            }

            if(complianceStatus) {
                 complianceStatus.innerHTML = passed ? `<i class="fas fa-check-circle"></i> Compliance: PASS` : `<i class="fas fa-exclamation-triangle"></i> Compliance: FAIL`;
                 complianceStatus.className = passed ? "compliance-pass" : "compliance-fail";
            }
        } else {
            console.log("No snapshot found. Only raw code restored.");
        }

    } catch (err) {
        console.error("Error loading project:", err);
    }
}

async function favoriteProject(id, fav) {
    await fetch("/favorite-project", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id, fav })
    });
    loadProjects();
}

async function deleteProject(id) {
    if(!confirm("Are you sure you want to delete this project?")) return;
    
    await fetch("/delete-project", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id })
    });
    loadProjects();
}

// ==========================================
// 4. CHAT SYSTEM
// ==========================================

async function loadSavedChat() {
    try {
        const res = await fetch("/load-chat");
        const data = await res.json();

        const chatBody = document.getElementById('chatBody');
        if (!chatBody) return;

        if (data.status === "success") {
            data.chat.forEach(msg => {
                if(msg.user_message) chatBody.innerHTML += `<div class="chat-msg user-msg">${msg.user_message}</div>`;
                if(msg.ai_response) {
                    const cleanReply = msg.ai_response.replace(/\n/g, '<br>');
                    chatBody.innerHTML += `<div class="chat-msg ai-msg">${cleanReply}</div>`;
                }
            });
            chatBody.scrollTop = chatBody.scrollHeight;
        }
    } catch (err) {
        console.error("Chat load failed", err);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    const chatBody = document.getElementById('chatBody');
    const currentCode = document.getElementById('inputCode') ? document.getElementById('inputCode').value : document.getElementById('codeInput').value;

    if (!msg) return;

    chatBody.innerHTML += `<div class="chat-msg user-msg">${msg}</div>`;
    input.value = '';
    chatBody.scrollTop = chatBody.scrollHeight;

    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-msg ai-msg';
    loadingDiv.innerText = 'Thinking...';
    chatBody.appendChild(loadingDiv);

    try {
        const response = await fetch('/ai_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, code_context: currentCode })
        });
        const data = await response.json();
        
        chatBody.removeChild(loadingDiv);

        if(data.status === 'success') {
            // UPDATE: Safe AI Code Rendering
            const aiMsgDiv = document.createElement('div');
            aiMsgDiv.className = 'chat-msg ai-msg';
            
            if (data.reply.includes('```')) {
                aiMsgDiv.style.fontFamily = 'monospace';
                aiMsgDiv.style.whiteSpace = 'pre-wrap';
            }
            aiMsgDiv.innerHTML = data.reply.replace(/\n/g, '<br>');
            chatBody.appendChild(aiMsgDiv);
        } else {
            chatBody.innerHTML += `<div class="chat-msg ai-msg" style="color:red">Error: ${data.message}</div>`;
        }
    } catch(err) {
        if(chatBody.contains(loadingDiv)) chatBody.removeChild(loadingDiv);
        chatBody.innerHTML += `<div class="chat-msg ai-msg" style="color:red">Network Error</div>`;
    }
    chatBody.scrollTop = chatBody.scrollHeight;
}

function handleChatEnter(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault(); 
        sendChatMessage();
    }
}

// ==========================================
// 5. LAYOUT RESIZER
// ==========================================

const gutter = document.getElementById('resizeHandle');
const colLeft = document.getElementById('colLeft');
const container = document.getElementById('mainContainer');
let isResizing = false;

if (gutter && colLeft && container) {
    gutter.addEventListener('mousedown', (e) => {
        isResizing = true;
        document.body.style.cursor = 'col-resize';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const containerWidth = container.offsetWidth;
        const newLeftWidth = (e.clientX / containerWidth) * 100;
        if (newLeftWidth > 10 && newLeftWidth < 90) {
            colLeft.style.width = `${newLeftWidth}%`;
        }
    });

    document.addEventListener('mouseup', () => {
        if(isResizing) {
            isResizing = false;
            document.body.style.cursor = 'default';
        }
    });
}

// ==========================================
// 6. CODE ASSESSMENT & ANALYSIS API
// ==========================================

let lastReportData = null; 

async function handleAssessment() {
    const inputCode = document.getElementById('inputCode') ? document.getElementById('inputCode').value : "";
    const targetLang = document.getElementById('targetLang') ? document.getElementById('targetLang').value : "Python";
    
    // --- 1. GET OVERLAY ELEMENT ---
    const overlay = document.getElementById('loadingOverlay');
    
    // --- 2. ACTIVATE BLUR OVERLAY (The Update) ---
    if (overlay) {
        overlay.style.display = "flex";           // Show it
        overlay.style.backdropFilter = "blur(15px)"; // FORCE BLUR EFFECT
        overlay.style.webkitBackdropFilter = "blur(15px)"; // Safari support
        overlay.style.zIndex = "10000";           // Ensure it's on top of everything
    }

    if (!inputCode.trim()) {
        alert("Please input code.");
        if (overlay) overlay.style.display = "none";
        return;
    }

    // UI References
    const errorTableBody = document.querySelector('#errorTable tbody');
    const explanationTableBody = document.querySelector('#explanationTable tbody');
    const outputBox = document.getElementById('outputCode');
    
    // UI Metrics
    const integrityBadge = document.getElementById('integrityCheck');
    const detectedBadge = document.getElementById('detectedLang');
    const plagiarismCheck = document.getElementById('plagiarismCheck');
    const qualityScoreDisplay = document.getElementById('qualityScoreDisplay'); 
    const complianceStatus = document.getElementById('complianceStatus');

    // Complexity References
    const timeBest = document.getElementById('timeBest');
    const timeAvg = document.getElementById('timeAvg');
    const timeWorst = document.getElementById('timeWorst');
    const timeDesc = document.getElementById('timeDesc');
    const spaceBest = document.getElementById('spaceBest');
    const spaceAvg = document.getElementById('spaceAvg');
    const spaceWorst = document.getElementById('spaceWorst');
    const spaceDesc = document.getElementById('spaceDesc');

    // Sentinel References
    const ciBadge = document.getElementById('ciStatusBadge');
    const ciText = document.getElementById('ciStatusText');
    const ciConsole = document.getElementById('ciConsoleOutput');

    try {
        console.log("🚀 Sending request to /process_code...");
        
        // --- 3. PERFORM ANALYSIS ---
        const response = await fetch('/process_code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: inputCode, target_lang: targetLang })
        });
        const data = await response.json();
        console.log("✅ Data received:", data); 

        if (data.status === "error") {
            if (outputBox) outputBox.value = "Error: " + data.message;
            return;
        }

        // --- 4. UPDATE UI (Keep everything same as before) ---
        if (outputBox) {
            outputBox.value = data.final_code || "// No fix generated";
            updateLineNumbers('outputCode', 'outputLines');
        }

        // Basic Metrics
        if (detectedBadge) detectedBadge.innerText = data.detected_language || "Unknown";
        if (integrityBadge) integrityBadge.innerText = "Integrity: " + (data.integrity_check || "--");
        if (qualityScoreDisplay) qualityScoreDisplay.innerHTML = `<i class="fas fa-star"></i> Quality Score: ${data.quality_score || 0}/100`;
        
        // Plagiarism
        if (plagiarismCheck) {
            plagiarismCheck.innerHTML = `<i class="fas fa-shield-alt"></i> Plagiarism Check: ${data.plagiarism_check || "N/A"}`;
            plagiarismCheck.className = (data.plagiarism_check && data.plagiarism_check.toLowerCase().includes("high match")) 
                ? 'plagiarism-high' : 'plagiarism-low';
        }

        // Update Tables & PDF Data (Preserved from your code)
        let pdfErrorLog = "No critical errors found.";
        let errorCount = 0;
        let errorsListForConsole = "";
        
        if (data.error_table && data.error_table.length > 0) {
            errorCount = data.error_table.length;
            if(errorTableBody) {
                errorTableBody.innerHTML = "";
                data.error_table.forEach(err => {
                    errorTableBody.innerHTML += `<tr><td><strong>${err.line}</strong></td><td><strong>${err.error}</strong></td></tr>`;
                    errorsListForConsole += `   [Line ${err.line}] ${err.error}<br>`;
                });
            }
            pdfErrorLog = data.error_table.map(e => `[Line ${e.line}] ${e.error}`).join("\n");
        } else if(errorTableBody) {
            errorTableBody.innerHTML = `<tr><td colspan="2">No critical errors found.</td></tr>`;
        }

        let pdfExplanation = "No explanation provided.";
        if (data.code_explanation && data.code_explanation.length > 0) {
            if(explanationTableBody) {
                explanationTableBody.innerHTML = "";
                data.code_explanation.forEach(item => {
                    explanationTableBody.innerHTML += `<tr><td><strong>${item.code}</strong></td><td><strong>${item.explanation}</strong></td></tr>`;
                });
            }
            pdfExplanation = data.code_explanation.map(e => `[${e.code}]\n -> ${e.explanation}`).join("\n\n");
        }

        let pdfTime = "N/A", pdfSpace = "N/A";
        if (data.complexity) {
            const t = data.complexity.time;
            const s = data.complexity.space;
            
            if(t && timeBest) {
                timeBest.innerHTML = `<strong>${t.best}</strong>`;
                timeAvg.innerHTML = `<strong>${t.average}</strong>`;
                timeWorst.innerHTML = `<strong>${t.worst}</strong>`;
                if(timeDesc) timeDesc.innerHTML = `<strong>${t.desc}</strong>`;
                pdfTime = `Time Complexity:\nBest: ${t.best}\nAvg: ${t.average}\nWorst: ${t.worst}\n\nDetails: ${t.desc}`;
            }
            if(s && spaceBest) {
                spaceBest.innerHTML = `<strong>${s.best}</strong>`;
                spaceAvg.innerHTML = `<strong>${s.average}</strong>`;
                spaceWorst.innerHTML = `<strong>${s.worst}</strong>`;
                if(spaceDesc) spaceDesc.innerHTML = `<strong>${s.desc}</strong>`;
                pdfSpace = `Space Complexity:\nBest: ${s.best}\nAvg: ${s.average}\nWorst: ${s.worst}\n\nDetails: ${s.desc}`;
            }
        }

        // Sentinel UI
        const score = data.quality_score || 0;
        const passed = score >= 70;
        
        if (ciBadge) {
            ciBadge.innerText = passed ? "PASSED" : "FAILED";
            ciBadge.className = passed ? "ci-badge ci-pass" : "ci-badge ci-fail";
            ciBadge.style.border = "none";
            ciBadge.style.color = passed ? "#22c55e" : "#ef4444";
            
            let consoleHtml = `$ codestatic-ci --verify<br>`;
            if (passed) {
                ciText.innerHTML = `Build Allowed. Quality Score <b>${score}</b> passed threshold (70).`;
                consoleHtml += `<span style="color:#22c55e">> SUCCESS: Code passed deployment gates.</span><br>`;
                consoleHtml += errorCount > 0 ? `<span style="color:#eab308">> WARNING: ${errorCount} Errors (Non-blocking).</span>` : `<span style="color:#22c55e">> CLEAN BUILD.</span>`;
            } else {
                ciText.innerHTML = `Build Blocked. Quality Score <b>${score}</b> is too low.`;
                consoleHtml += `<span style="color:#ef4444">> FATAL: Score ${score} < 70.</span><br>`;
                consoleHtml += `<span style="color:#ef4444">> EXIT CODE 1 (Build Aborted)</span>`;
            }
            ciConsole.innerHTML = consoleHtml;
        }

        if(complianceStatus) {
             complianceStatus.innerHTML = passed ? `<i class="fas fa-check-circle"></i> Compliance: PASS` : `<i class="fas fa-exclamation-triangle"></i> Compliance: FAIL`;
             complianceStatus.className = passed ? "compliance-pass" : "compliance-fail";
        }

        // Save for PDF
        lastReportData = {
            ...data,
            original_code: inputCode,
            error_log_text: pdfErrorLog, 
            explanation_text: pdfExplanation,
            time_analysis: pdfTime,
            space_analysis: pdfSpace
        };

    } catch (err) {
        console.error("Analysis Failed:", err);
        alert("Analysis failed. Check console.");
    } finally {
        // --- 5. HIDE BLUR OVERLAY (Only removes after everything is done) ---
        if (overlay) overlay.style.display = "none";
    }
}

// ==========================================
// 7. REPORTING & UTILITIES
// ==========================================

async function downloadPdf() {
    if (!lastReportData) {
        alert("No data found. Please run 'Run Analysis' first.");
        return;
    }

    console.log("📤 Sending PDF Data:", lastReportData);

    const btn = document.querySelector('.pdf-nav-btn');
    if(btn) btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i>`;

    try {
        const response = await fetch('/generate_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastReportData)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `CodeStatic_Report_${Date.now()}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            const text = await response.text();
            console.error("PDF Server Error:", text);
            alert("PDF Generation Failed: " + text);
        }
    } catch (e) {
        console.error("Network Error:", e);
        alert("Network Error generating PDF.");
    } finally {
        if(btn) btn.innerHTML = `<i class="fas fa-file-pdf"></i>`;
    }
}

// --- Real Copy Utilities ---

function copyContent(id) {
    const el = document.getElementById(id);
    if(el) {
        el.select();
        navigator.clipboard.writeText(el.value);
        alert("Code Copied!");
    }
}

function copyTable() {
    const rows = document.querySelectorAll('#errorTable tbody tr');
    let text = "--- CODESTATIC CRITICAL ERROR LOG ---\n";
    if(rows.length === 0 || rows[0].innerText.includes("No critical errors")) {
        text += "No critical errors found.";
    } else {
        rows.forEach(row => {
            text += row.innerText.replace(/\t/g, " | ") + "\n";
        });
    }
    navigator.clipboard.writeText(text);
    alert("Critical Log Copied!");
}

function copyExplanationTable() {
    const rows = document.querySelectorAll('#explanationTable tbody tr');
    let text = "--- CODESTATIC LINE EXPLANATION ---\n";
    rows.forEach(row => {
        text += row.innerText.replace(/\t/g, " | ") + "\n";
    });
    navigator.clipboard.writeText(text);
    alert("Explanation Copied!");
}

function copyComplexity() {
    const timeBest = document.getElementById('timeBest').innerText;
    const timeAvg = document.getElementById('timeAvg').innerText;
    const timeWorst = document.getElementById('timeWorst').innerText;
    const timeDesc = document.getElementById('timeDesc').innerText;
    
    const spaceBest = document.getElementById('spaceBest').innerText;
    const spaceAvg = document.getElementById('spaceAvg').innerText;
    const spaceWorst = document.getElementById('spaceWorst').innerText;
    const spaceDesc = document.getElementById('spaceDesc').innerText;

    const text = `--- COMPLEXITY ANALYSIS ---\n\nTIME COMPLEXITY:\nBest: ${timeBest}\nAverage: ${timeAvg}\nWorst: ${timeWorst}\nDetails: ${timeDesc}\n\nSPACE COMPLEXITY:\nBest: ${spaceBest}\nAverage: ${spaceAvg}\nWorst: ${spaceWorst}\nDetails: ${spaceDesc}`;
    
    navigator.clipboard.writeText(text);
    alert("Complexity Log Copied!");
}

function copyCICDLog() {
    const badge = document.getElementById('ciStatusBadge');
    const textDetails = document.getElementById('ciStatusText');
    const consoleOut = document.getElementById('ciConsoleOutput');

    if(!badge || !textDetails || !consoleOut) {
        alert("Run an assessment first to generate CI logs.");
        return;
    }

    const text = `--- DEPLOYMENT SENTINEL (CI/CD) ---\nSTATUS: ${badge.innerText}\nDETAILS: ${textDetails.innerText}\n\nCONSOLE OUTPUT:\n${consoleOut.innerText}`;
    navigator.clipboard.writeText(text);
    alert("Deployment Sentinel Log Copied!");
}

// ==========================================
// 8. INIT (UPDATED)
// ==========================================
togglePanel("projectsButton", "projectsPanel");

// UPDATE: Added Auto-Save Debouncer to protect your server
let saveTimeout;
function debouncedSave() {
    clearTimeout(saveTimeout);
    saveTimeout = setTimeout(saveCodeToDB, 1500); // Wait 1.5 seconds after typing stops
}

document.addEventListener('DOMContentLoaded', () => {
    // Restore Theme
    const storedTheme = localStorage.getItem('cp_theme');
    if (storedTheme === 'light') {
        document.body.classList.add('light-mode');
        const icon = document.getElementById('themeIcon');
        if(icon) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
        }
    }

    loadLastSavedCode();
    loadProjects();
    loadSavedChat();
    
    // UPDATE: Now uses the Debounced Save function
    const codeInput = document.getElementById("inputCode") || document.getElementById("codeInput");
    if (codeInput) {
        codeInput.addEventListener('keyup', debouncedSave);
    }
});