import fitz
import re
import os
import json
import requests
from typing import Tuple, List


SKILLS_KEYWORDS = [
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "scala",
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "numpy", "pandas",
    "matplotlib", "seaborn", "jupyter", "cuda", "gpu",
    "machine learning", "deep learning", "neural network", "nlp", "computer vision",
    "reinforcement learning", "supervised learning", "unsupervised learning",
    "random forest", "gradient boosting", "xgboost", "lightgbm", "svm", "lstm",
    "transformer", "bert", "gpt", "llm", "rag", "embedding", "vector database",
    "fastapi", "flask", "django", "express", "node.js", "spring boot",
    "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
    "rest api", "graphql", "microservices", "ci/cd", "git", "linux",
    "data pipeline", "etl", "spark", "hadoop", "kafka", "airflow",
    "statistics", "probability", "linear algebra", "calculus",
    "a/b testing", "feature engineering", "model deployment", "mlops",
]


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def extract_candidate_name(text: str) -> str:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        first_line = lines[0]
        if len(first_line.split()) <= 5 and not any(c.isdigit() for c in first_line):
            return first_line
    return "Candidate"


def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    found_skills = []
    for skill in SKILLS_KEYWORDS:
        if skill in text_lower:
            found_skills.append(skill.title() if len(skill.split()) == 1 else skill)
    if not found_skills:
        found_skills = ["Python", "Machine Learning", "Data Science"]
    return list(dict.fromkeys(found_skills))[:15]


def detect_experience_level(text: str, skills: List[str]) -> str:
    text_lower = text.lower()

    senior_keywords = ["senior", "lead", "principal", "architect", "manager", "head of", "director", "staff engineer"]
    junior_keywords = ["fresher", "graduate", "intern", "entry", "junior", "student", "trainee", "recent grad"]

    has_senior = any(kw in text_lower for kw in senior_keywords)
    has_junior = any(kw in text_lower for kw in junior_keywords)

    years_matches = re.findall(r'(\d+)\s*(?:year|yr)', text_lower)
    max_years = max((int(y) for y in years_matches), default=0)

    skill_count = len(skills)

    if has_senior or max_years > 4 or skill_count > 12:
        return "advanced"
    if has_junior or max_years < 1 or skill_count < 5:
        return "beginner"
    return "intermediate"


SKILLS_LLM_PROMPT = """You are a technical resume parser.
Extract all technical skills, technologies, frameworks, programming languages, and domain expertise from the resume text below.

Rules:
- Return ONLY a valid JSON array of strings, no other text
- Max 15 items
- Each item should be a concise skill name (e.g. "Python", "PyTorch", "REST APIs", "Machine Learning")
- No duplicates, no generic soft skills like "communication"

Resume text:
{resume_text}

Return ONLY a JSON array like: ["Python", "PyTorch", "FastAPI"]
"""


def extract_skills_llm(resume_text: str) -> List[str]:
    """
    LLM-based skill extraction using Claude-3-Haiku via OpenRouter.
    Raises on any failure so the caller can fall back to keyword matching.
    """
    prompt = SKILLS_LLM_PROMPT.format(resume_text=resume_text[:4000])
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
        json={
            "model": "anthropic/claude-3-haiku",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=15,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"].strip()

    start = content.find("[")
    end = content.rfind("]") + 1
    if start != -1 and end > start:
        content = content[start:end]

    skills = json.loads(content)
    if not isinstance(skills, list):
        raise ValueError("LLM did not return a list")

    return [str(s).strip() for s in skills if str(s).strip()][:15]


def parse_resume(pdf_bytes: bytes) -> Tuple[str, List[str], str]:
    text = extract_text_from_pdf(pdf_bytes)
    candidate_name = extract_candidate_name(text)
    try:
        skills = extract_skills_llm(text)
        if not skills:
            raise ValueError("LLM returned empty skills list")
    except Exception as e:
        print(f"LLM skill extraction failed ({e}), falling back to keyword matching")
        skills = extract_skills(text)
    return candidate_name, skills, text
