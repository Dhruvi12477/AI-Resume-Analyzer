// ==================== DOM ELEMENTS ====================
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("resumeFile");
const filePreview = document.getElementById("filePreview");
const analyzeBtn = document.getElementById("analyzeBtn");
const loading = document.getElementById("loading");
const resultsSection = document.getElementById("results");
const targetRoleSelect = document.getElementById("targetRole");

// ==================== EVENT LISTENERS ====================

// Click to upload
dropzone.addEventListener("click", () => {
    fileInput.click();
});

// File selected
fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        displayFile(fileInput.files[0]);
    }
});

// Drag over
dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
});

// Drag leave
dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
});

// Drop file
dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        displayFile(files[0]);
    }
});

// ==================== FILE HANDLING ====================
function displayFile(file) {
    // Validate file
    const allowedTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
    
    if (!allowedTypes.includes(file.type)) {
        showNotification("Please upload a PDF or DOCX file.", "error");
        fileInput.value = "";
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        showNotification("File size must be below 10MB.", "error");
        fileInput.value = "";
        return;
    }
    
    // Display file preview
    const fileName = file.name;
    filePreview.textContent = `📄 ${fileName}`;
    filePreview.classList.add("show");
}

// ==================== ANALYZE FUNCTION ====================
async function analyzeResume() {
    const file = fileInput.files[0];
    const targetRole = targetRoleSelect.value;
    
    // Validation
    if (!file) {
        showNotification("Please upload your resume first.", "error");
        return;
    }
    
    if (!targetRole) {
        showNotification("Please select a target job role.", "error");
        return;
    }
    
    // Prepare form data
    const formData = new FormData();
    formData.append("file", file);
    
    // Show loading state
    analyzeBtn.disabled = true;
    loading.style.display = "flex";
    resultsSection.style.display = "none";
    
    try {
        const response = await fetch(
            `/api/analyze?target_role=${encodeURIComponent(targetRole)}`,
            {
                method: "POST",
                body: formData
            }
        );
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || "Analysis failed. Please try again.");
        }
        
        // Display results with animation
        displayResults(result);
        
    } catch (error) {
        showNotification(`Error: ${error.message}`, "error");
        console.error("Analysis error:", error);
    } finally {
        // Hide loading state
        analyzeBtn.disabled = false;
        loading.style.display = "none";
    }
}

// ==================== DISPLAY RESULTS ====================
function displayResults(data) {
    // Update overall score
    animateValue("overallScore", parseInt(data.overall_score));
    
    // Update percentage scores
    updatePercentageScore("readinessScore", data.job_readiness_score);
    updatePercentageScore("atsScore", data.ats_score);
    updatePercentageScore("shortlistScore", data.shortlist_probability);
    updatePercentageScore("skillMatch", data.skill_match);
    
    // Update result header
    document.getElementById("resultTitle").textContent = `${data.level} Resume Profile`;
    document.getElementById("resultMessage").textContent = data.message;
    
    // Update status badge
    const statusBadge = document.getElementById("statusBadge");
    statusBadge.textContent = data.status;
    statusBadge.className = `status-badge status-${data.status.toLowerCase()}`;
    
    // Update candidate profile
    document.getElementById("targetRoleResult").textContent = data.target_role;
    document.getElementById("experience").textContent = `${data.years_experience} years`;
    document.getElementById("projects").textContent = data.projects;
    document.getElementById("quality").textContent = data.resume_quality_score || "-";
    document.getElementById("level").textContent = data.level;
    
    // Update progress bars
    animateProgressBar("readinessProgress", data.job_readiness_score);
    animateProgressBar("atsProgress", data.ats_score);
    animateProgressBar("shortlistProgress", data.shortlist_probability);
    
    // Render tags
    renderTags("skillsFound", data.skills_found);
    renderTags("missingSkills", data.missing_skills, true);
    
    // Render recommendations
    renderRecommendations("strengths", data.strengths);
    renderRecommendations("recommendations", data.recommendations);
    
    // Show results section
    resultsSection.style.display = "block";
    
    // Smooth scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
}

// ==================== ANIMATION UTILITIES ====================
function animateValue(elementId, targetValue) {
    const element = document.getElementById(elementId);
    const startValue = 0;
    const duration = 1000;
    const startTime = Date.now();
    
    function update() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentValue = Math.floor(startValue + (targetValue - startValue) * easeOutQuad(progress));
        element.textContent = currentValue;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    update();
}

function updatePercentageScore(elementId, value) {
    const element = document.getElementById(elementId);
    animateValue(elementId, parseInt(value));
    // Update text manually after animation starts
    setTimeout(() => {
        element.textContent = `${value}%`;
    }, 1000);
}

function animateProgressBar(elementId, value) {
    const element = document.getElementById(elementId);
    const targetWidth = Math.min(value, 100);
    
    setTimeout(() => {
        element.style.width = targetWidth + "%";
    }, 100);
}

function easeOutQuad(t) {
    return t * (2 - t);
}

// ==================== RENDER TAGS ====================
function renderTags(elementId, items, isMissing = false) {
    const container = document.getElementById(elementId);
    container.innerHTML = "";
    
    if (!items || items.length === 0) {
        container.innerHTML = '<span style="color: var(--text-secondary);">None detected</span>';
        return;
    }
    
    items.forEach((item, index) => {
        const tag = document.createElement("span");
        tag.textContent = item;
        tag.style.animation = `tagPop 0.3s ease-out ${index * 0.1}s both`;
        container.appendChild(tag);
    });
}

// ==================== RENDER RECOMMENDATIONS ====================
function renderRecommendations(elementId, items) {
    const container = document.getElementById(elementId);
    container.innerHTML = "";
    
    if (!items || items.length === 0) {
        const div = document.createElement("div");
        div.textContent = "None available";
        div.style.color = "var(--text-secondary)";
        container.appendChild(div);
        return;
    }
    
    items.forEach((item, index) => {
        const div = document.createElement("div");
        div.textContent = item;
        div.style.animation = `slideIn 0.3s ease-out ${index * 0.1}s both`;
        container.appendChild(div);
    });
}

// ==================== UTILITY FUNCTIONS ====================
function showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add styles if not already in CSS
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === "error" ? "var(--error)" : "var(--success)"};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        z-index: 2000;
        animation: slideIn 0.3s ease-out;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = "slideOut 0.3s ease-out";
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function analyzeAgain() {
    // Reset form
    fileInput.value = "";
    filePreview.textContent = "";
    filePreview.classList.remove("show");
    targetRoleSelect.value = "";
    resultsSection.style.display = "none";
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: "smooth" });
    
    // Focus on file input
    setTimeout(() => fileInput.click(), 300);
}

function downloadReport() {
    // Get all results data
    const reportData = {
        title: "Resume Analysis Report",
        overallScore: document.getElementById("overallScore").textContent,
        jobReadiness: document.getElementById("readinessScore").textContent,
        atsScore: document.getElementById("atsScore").textContent,
        shortlistProbability: document.getElementById("shortlistScore").textContent,
        skillMatch: document.getElementById("skillMatch").textContent,
        targetRole: document.getElementById("targetRoleResult").textContent,
        experience: document.getElementById("experience").textContent,
        projects: document.getElementById("projects").textContent,
        quality: document.getElementById("quality").textContent,
        level: document.getElementById("level").textContent,
        timestamp: new Date().toLocaleString()
    };
    
    // Create report content
    const reportContent = `
RESUME ANALYSIS REPORT
${"=".repeat(50)}

Generated: ${reportData.timestamp}

OVERALL ASSESSMENT
${"-".repeat(50)}
Overall Score:        ${reportData.overallScore} / 100
Level:                ${reportData.level}
Job Readiness:        ${reportData.jobReadiness}
ATS Score:            ${reportData.atsScore}
Shortlist Probability: ${reportData.shortlistProbability}

CANDIDATE PROFILE
${"-".repeat(50)}
Target Role:          ${reportData.targetRole}
Experience:           ${reportData.experience}
Projects:             ${reportData.projects}
Resume Quality:       ${reportData.quality}
Skill Match:          ${reportData.skillMatch}

Generated by ResumeAI - AI-Powered Resume Analyzer
    `;
    
    // Create and download file
    const blob = new Blob([reportContent], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Resume_Analysis_Report_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showNotification("Report downloaded successfully!", "success");
}

// ==================== ENHANCE LOADING STATE ====================
function updateLoadingMessage() {
    const loadingMessages = [
        "AI is analyzing your resume...",
        "Extracting key information...",
        "Matching skills to job requirements...",
        "Calculating compatibility scores...",
        "Almost done..."
    ];
    
    let messageIndex = 0;
    const messageParagraph = loading.querySelector("p");
    
    const interval = setInterval(() => {
        if (messageParagraph && loading.style.display !== "none") {
            messageParagraph.textContent = loadingMessages[messageIndex];
            messageIndex = (messageIndex + 1) % loadingMessages.length;
        } else {
            clearInterval(interval);
        }
    }, 2000);
}

// ==================== INITIALIZE ====================
document.addEventListener("DOMContentLoaded", () => {
    // Add keyboard shortcuts
    document.addEventListener("keydown", (e) => {
        // Enter to analyze
        if (e.key === "Enter" && !analyzeBtn.disabled) {
            analyzeResume();
        }
    });
    
    // Update loading message periodically
    const originalAnalyze = analyzeResume;
    window.analyzeResume = function() {
        updateLoadingMessage();
        return originalAnalyze.call(this);
    };
    
    console.log("✓ ResumeAI initialized");
});

// ==================== ADD SLIDEOUT ANIMATION ====================
const style = document.createElement("style");
style.textContent = `
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .loading-state {
        display: none !important;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }
`;
document.head.appendChild(style);
