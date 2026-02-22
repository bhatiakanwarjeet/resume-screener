import re
import textstat
from services.llm import generate_text

BIASED_TERMS = [
    "rockstar","ninja","aggressive","dominant",
    "young","digital native","competitive"
]

REQUIRED_SECTIONS = [
    "responsibilities",
    "requirements",
    "benefits",
    "equal opportunity"
]

def generate_jd(title, department, seniority, requirements):
    prompt = f"""
    Generate a professional job description.

    Title: {title}
    Department: {department}
    Seniority: {seniority}
    Key Requirements: {requirements}

    Include:
    - Responsibilities
    - Required Qualifications
    - Preferred Qualifications
    - Benefits
    - Equal Opportunity statement
    """
    text, latency = generate_text(prompt)
    return text, latency

def inclusivity_score(text):
    found = [term for term in BIASED_TERMS if term in text.lower()]
    score = 1 - (len(found) / max(len(BIASED_TERMS),1))
    return round(score,3), found

def completeness_score(text):
    text_lower = text.lower()
    present = [sec for sec in REQUIRED_SECTIONS if sec in text_lower]
    score = len(present) / len(REQUIRED_SECTIONS)
    return round(score,3), present

def readability_score(text):
    score = textstat.flesch_reading_ease(text)
    normalized = min(max(score / 100, 0), 1)
    return round(normalized,3)

def optimize_jd(text):
    prompt = f"""
    Review this job description for:
    - Inclusivity
    - Clarity
    - SEO keyword strength

    Highlight problematic phrases and suggest specific rewrites.

    Job Description:
    {text}
    """
    result, latency = generate_text(prompt)
    return result, latency