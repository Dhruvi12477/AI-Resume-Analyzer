import os
import re
import joblib
import pandas as pd
import numpy as np

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pypdf import PdfReader
from docx import Document


# ============================================================
# APP
# ============================================================

app = FastAPI(title="AI Resume Analyzer API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "best_resume_analyzer_model.pkl"
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "models",
    "resume_analyzer_scaler.pkl"
)

DATASET_PATH = os.path.join(
    BASE_DIR,
    "data",
    "ai_resume_analyzer_dataset.csv"
)


# ============================================================
# LOAD MODEL
# ============================================================

try:

    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)

    print("✓ ML model loaded")
    print("✓ Scaler loaded")

except Exception as e:

    print("Model loading error:", e)

    model = None
    scaler = None


# ============================================================
# SKILL DATABASE
# ============================================================

SKILLS = {

    "UI/UX Designer": [
        "figma",
        "adobe xd",
        "sketch",
        "photoshop",
        "illustrator",
        "wireframing",
        "prototyping",
        "user research",
        "usability testing",
        "design systems",
        "interaction design",
        "visual design",
        "user experience",
        "user interface",
        "html",
        "css",
        "responsive design"
    ],

    "Frontend Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "angular",
        "vue",
        "typescript",
        "bootstrap",
        "tailwind",
        "git",
        "github",
        "responsive design",
        "rest api"
    ],

    "Backend Developer": [
        "python",
        "java",
        "node.js",
        "fastapi",
        "flask",
        "django",
        "sql",
        "mysql",
        "postgresql",
        "mongodb",
        "rest api",
        "git",
        "docker"
    ],

    "Data Scientist": [
        "python",
        "pandas",
        "numpy",
        "scikit-learn",
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "sql",
        "matplotlib",
        "seaborn",
        "statistics"
    ],

    "ML Engineer": [
        "python",
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "numpy",
        "pandas",
        "docker",
        "kubernetes",
        "mlops",
        "fastapi",
        "git"
    ],

    "Full Stack Developer": [
        "html",
        "css",
        "javascript",
        "react",
        "node.js",
        "python",
        "fastapi",
        "django",
        "sql",
        "mongodb",
        "git",
        "github",
        "rest api",
        "docker"
    ]
}


# ============================================================
# RESUME TEXT EXTRACTION
# ============================================================

def extract_pdf_text(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_docx_text(file_path):

    document = Document(file_path)

    text = ""

    for paragraph in document.paragraphs:

        text += paragraph.text + "\n"

    return text


def extract_resume_text(file_path, extension):

    extension = extension.lower()

    if extension == ".pdf":

        return extract_pdf_text(file_path)

    elif extension == ".docx":

        return extract_docx_text(file_path)

    else:

        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported."
        )


# ============================================================
# TEXT ANALYSIS
# ============================================================

def detect_skills(text, target_role):

    text_lower = text.lower()

    required_skills = SKILLS.get(
        target_role,
        SKILLS["Frontend Developer"]
    )

    found = []
    missing = []

    for skill in required_skills:

        if skill.lower() in text_lower:

            found.append(skill)

        else:

            missing.append(skill)

    return found, missing


def detect_experience(text):

    patterns = [

        r"(\d+)\+?\s+years?\s+of\s+experience",

        r"(\d+)\+?\s+years?\s+experience",

        r"experience\s*[:\-]?\s*(\d+)\+?\s*years?"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text.lower()
        )

        if match:

            return int(match.group(1))

    return 0


def count_projects(text):

    keywords = [
        "project",
        "projects",
        "developed",
        "built",
        "created"
    ]

    count = 0

    for keyword in keywords:

        count += text.lower().count(keyword)

    return min(max(count // 3, 1), 15)


def calculate_ats_score(text):

    score = 50

    sections = [
        "education",
        "experience",
        "skills",
        "projects",
        "certifications",
        "summary"
    ]

    for section in sections:

        if section in text.lower():

            score += 7

    return min(score, 100)


def calculate_resume_quality(text):

    score = 40

    if len(text) > 1000:
        score += 15

    if len(text) > 2000:
        score += 10

    if "education" in text.lower():
        score += 10

    if "experience" in text.lower():
        score += 10

    if "skills" in text.lower():
        score += 10

    if "projects" in text.lower():
        score += 5

    return min(score, 100)


# ============================================================
# ML PREDICTION
# ============================================================

FEATURE_NAMES = [
    "target_job_role",
    "education_level",
    "degree_field",
    "years_of_experience",
    "num_projects",
    "num_certifications",
    "num_internships",
    "technical_skills_count",
    "relevant_skills_count",
    "required_skills_count",
    "skill_match_percentage",
    "soft_skills_count",
    "project_relevance_score",
    "experience_relevance_score",
    "education_relevance_score",
    "resume_quality_score",
    "ats_score",
    "keyword_match_percentage",
    "overall_resume_score",
    "job_readiness_score",
    "experience_level",
    "missing_skills_count",
    "job_readiness"
]


def get_experience_level(years):

    if years == 0:
        return "Fresher"

    if years <= 2:
        return "Junior"

    if years <= 5:
        return "Mid-Level"

    return "Senior"


def ml_prediction(
    target_role,
    years,
    projects,
    found_skills,
    missing_skills,
    ats_score,
    resume_quality,
    skill_match
):

    if model is None or scaler is None:

        return {
            "prediction": 1 if skill_match >= 60 else 0,
            "probability": skill_match
        }

    required = len(found_skills) + len(missing_skills)

    experience_level = get_experience_level(years)

    job_readiness_score = (
        skill_match * 0.40
        + ats_score * 0.25
        + resume_quality * 0.20
        + min(years * 10, 100) * 0.15
    )

    overall_score = (
        skill_match * 0.35
        + ats_score * 0.25
        + resume_quality * 0.25
        + min(projects * 8, 100) * 0.15
    )

    # Use dataset to obtain valid categorical values
    try:

        df = pd.read_csv(DATASET_PATH)

        role_values = df["target_job_role"].astype(str).unique()
        education_values = df["education_level"].astype(str).unique()
        degree_values = df["degree_field"].astype(str).unique()
        experience_values = df["experience_level"].astype(str).unique()
        readiness_values = df["job_readiness"].astype(str).unique()

        # The frontend uses roles that exist in the training dataset.
        # If a custom/unknown role is received, fail safely instead of
        # silently predicting for a different role.
        if target_role not in role_values:
            raise ValueError(
                f"Unsupported target role '{target_role}'. "
                f"Use one of: {list(role_values)}"
            )

        role = target_role

        education = (
            "Bachelor's"
            if "Bachelor's" in education_values
            else education_values[0]
        )

        degree = (
            "Design"
            if "Design" in degree_values
            else degree_values[0]
        )

        experience = (
            experience_level
            if experience_level in experience_values
            else experience_values[0]
        )

        readiness = (
            "Intermediate"
            if "Intermediate" in readiness_values
            else readiness_values[0]
        )

        encoders = {}

        from sklearn.preprocessing import LabelEncoder

        for col in [
            "target_job_role",
            "education_level",
            "degree_field",
            "experience_level",
            "job_readiness"
        ]:

            le = LabelEncoder()

            le.fit(df[col].astype(str))

            encoders[col] = le

        values = {

            "target_job_role":
                encoders["target_job_role"].transform([role])[0],

            "education_level":
                encoders["education_level"].transform([education])[0],

            "degree_field":
                encoders["degree_field"].transform([degree])[0],

            "years_of_experience":
                years,

            "num_projects":
                projects,

            "num_certifications":
                2,

            "num_internships":
                1,

            "technical_skills_count":
                len(found_skills),

            "relevant_skills_count":
                len(found_skills),

            "required_skills_count":
                required,

            "skill_match_percentage":
                skill_match,

            "soft_skills_count":
                5,

            "project_relevance_score":
                min(projects * 10, 100),

            "experience_relevance_score":
                min(years * 12, 100),

            "education_relevance_score":
                70,

            "resume_quality_score":
                resume_quality,

            "ats_score":
                ats_score,

            "keyword_match_percentage":
                skill_match,

            "overall_resume_score":
                overall_score,

            "job_readiness_score":
                job_readiness_score,

            "experience_level":
                encoders["experience_level"].transform([experience])[0],

            "missing_skills_count":
                len(missing_skills),

            "job_readiness":
                encoders["job_readiness"].transform([readiness])[0]
        }

        X = pd.DataFrame(
            [[values[col] for col in FEATURE_NAMES]],
            columns=FEATURE_NAMES
        )

        X_scaled = scaler.transform(X)

        # Keep feature names for scikit-learn models trained with
        # pandas DataFrames.
        X_scaled_df = pd.DataFrame(
            X_scaled,
            columns=FEATURE_NAMES
        )

        prediction = int(
            model.predict(X_scaled_df)[0]
        )

        probabilities = model.predict_proba(
            X_scaled_df
        )[0]

        probability = float(
            probabilities[1] * 100
        )

        return {
            "prediction": prediction,
            "probability": round(probability, 2)
        }

    except Exception as e:

        print("ML prediction fallback:", e)

        return {
            "prediction": 1 if skill_match >= 60 else 0,
            "probability": round(skill_match, 2)
        }


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_resume(text, target_role):

    found_skills, missing_skills = detect_skills(
        text,
        target_role
    )

    required_count = len(found_skills) + len(missing_skills)

    skill_match = (
        len(found_skills) / required_count * 100
        if required_count
        else 0
    )

    years = detect_experience(text)

    projects = count_projects(text)

    ats_score = calculate_ats_score(text)

    resume_quality = calculate_resume_quality(text)

    overall_score = round(
        skill_match * 0.35
        + ats_score * 0.25
        + resume_quality * 0.25
        + min(projects * 8, 100) * 0.15
    )

    job_readiness = round(
        skill_match * 0.40
        + ats_score * 0.25
        + resume_quality * 0.20
        + min(years * 10, 100) * 0.15
    )

    ml_result = ml_prediction(
        target_role,
        years,
        projects,
        found_skills,
        missing_skills,
        ats_score,
        resume_quality,
        skill_match
    )

    shortlist_probability = ml_result["probability"]

    if overall_score >= 80:

        level = "Excellent"
        message = "Your resume is highly competitive."

    elif overall_score >= 65:

        level = "Good"
        message = "Your resume has a good foundation but can be improved."

    elif overall_score >= 50:

        level = "Average"
        message = "Your resume needs improvement before applying."

    else:

        level = "Needs Improvement"
        message = "Your resume needs significant improvement."

    strengths = []

    if skill_match >= 70:
        strengths.append("Strong skill match")

    if ats_score >= 70:
        strengths.append("Good ATS compatibility")

    if projects >= 3:
        strengths.append("Good project experience")

    if years >= 2:
        strengths.append("Relevant experience")

    if not strengths:
        strengths.append("Resume structure is a starting point")

    recommendations = []

    if missing_skills:
        recommendations.append(
            "Learn missing skills: "
            + ", ".join(missing_skills[:5])
        )

    if ats_score < 70:
        recommendations.append(
            "Improve ATS keywords and resume formatting."
        )

    if projects < 3:
        recommendations.append(
            "Add more relevant projects."
        )

    if years == 0:
        recommendations.append(
            "Add internships, freelance work, or practical experience."
        )

    return {

        "overall_score": overall_score,

        "job_readiness_score":
            min(job_readiness, 100),

        "ats_score":
            ats_score,

        "resume_quality_score":
            resume_quality,

        "skill_match":
            round(skill_match, 2),

        "shortlist_probability":
            round(shortlist_probability, 2),

        "status":
            "Shortlisted"
            if ml_result["prediction"] == 1
            else "Needs Improvement",

        "level":
            level,

        "message":
            message,

        "target_role":
            target_role,

        "years_experience":
            years,

        "projects":
            projects,

        "skills_found":
            found_skills,

        "missing_skills":
            missing_skills,

        "strengths":
            strengths,

        "recommendations":
            recommendations,

        "resume_text_length":
            len(text)
    }


# ============================================================
# UPLOAD API
# ============================================================

@app.post("/api/analyze")
async def analyze_resume_api(
    file: UploadFile = File(...),
    target_role: str = "UI/UX Designer"
):

    allowed_extensions = [
        ".pdf",
        ".docx"
    ]

    original_filename = file.filename or "resume"
    filename = os.path.basename(original_filename)

    extension = os.path.splitext(
        filename
    )[1].lower()

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF or DOCX resume."
        )

    upload_dir = os.path.join(
        BASE_DIR,
        "uploads"
    )

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_dir,
        filename
    )

    content = await file.read()

    # Keep uploads small enough to avoid accidental large requests.
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be below 10MB."
        )

    with open(file_path, "wb") as f:
        f.write(content)

    try:

        text = extract_resume_text(
            file_path,
            extension
        )

        if not text.strip():

            raise HTTPException(
                status_code=400,
                detail="Could not extract text from this resume."
            )

        result = analyze_resume(
            text,
            target_role
        )

        result["filename"] = filename

        return result

    finally:

        if os.path.exists(file_path):

            os.remove(file_path)


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {

        "status": "healthy",

        "model_loaded":
            model is not None,

        "message":
            "AI Resume Analyzer API is running"
    }


# ============================================================
# FRONTEND
# ============================================================

FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "..",
    "frontend"
)

if os.path.exists(FRONTEND_DIR):

    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR),
        name="static"
    )


@app.get("/")
def home():

    index_path = os.path.join(
        FRONTEND_DIR,
        "index.html"
    )

    return FileResponse(index_path)