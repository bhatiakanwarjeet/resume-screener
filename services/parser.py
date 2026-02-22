import re
import spacy
from datetime import datetime
from services.llm import generate_text

nlp = spacy.load("en_core_web_sm")

COMMON_HEADERS = {
    "resume", "curriculum vitae", "life philosophy",
    "personal details", "objective", "summary",
    "experience", "education", "skills",
    "profile", "contact", "about me"
}

CURRENT_YEAR = datetime.now().year


# ---------------------------------------------------------
# NAME EXTRACTION
# ---------------------------------------------------------

def is_valid_name(name):
    if not name:
        return False
    name = name.strip()
    if len(name.split()) < 2 or len(name.split()) > 4:
        return False
    if any(char.isdigit() for char in name):
        return False
    if name.lower() in COMMON_HEADERS:
        return False
    return True


def extract_name(text, filename=None):

    # 1. NER
    doc = nlp(text[:3000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            if is_valid_name(ent.text):
                return ent.text

    # 2. Heuristic
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:10]:
        if is_valid_name(line):
            return line

    # 3. Filename fallback
    if filename:
        clean = re.sub(r"[_\-0-9]", " ", filename)
        clean = re.sub(r"\s+", " ", clean).strip()
        if len(clean.split()) >= 2:
            return clean.title()

    return None


# ---------------------------------------------------------
# EXPERIENCE EXTRACTION (HYBRID)
# ---------------------------------------------------------

def extract_years_regex(text):
    matches = re.findall(r"(\d+)\+?\s+years?", text.lower())
    if matches:
        return max([int(m) for m in matches])
    return None


def extract_years_from_dates(text):
    years = re.findall(r"(19\d{2}|20\d{2})", text)
    years = [int(y) for y in years if 1970 < int(y) <= CURRENT_YEAR]

    if len(years) >= 2:
        return max(years) - min(years)

    return None


def extract_years_llm(text):
    try:
        prompt = f"""
        Extract total years of professional work experience from this resume.
        Return only an integer.

        {text[:2000]}
        """
        result, _ = generate_text(prompt)
        result = re.findall(r"\d+", result)
        if result:
            return int(result[0])
    except:
        pass
    return None


def extract_years_experience(text):

    # 1. Regex
    years = extract_years_regex(text)
    if years:
        return years

    # 2. Date range calculation
    years = extract_years_from_dates(text)
    if years:
        return years

    # 3. LLM fallback
    years = extract_years_llm(text)
    if years:
        return years

    return 0


# ---------------------------------------------------------
# SKILL EXTRACTION (LIGHTWEIGHT)
# ---------------------------------------------------------

SKILL_KEYWORDS = [
    "python", "sql", "java", "aws", "docker",
    "kubernetes", "excel", "tableau",
    "machine learning", "deep learning",
    "project management", "react", "node"
]

def extract_skills(text):
    text_lower = text.lower()
    found = []
    for skill in SKILL_KEYWORDS:
        if skill in text_lower:
            found.append(skill)
    return list(set(found))


# ---------------------------------------------------------
# PARSE RESUME
# ---------------------------------------------------------

def parse_resume(text, filename=None):

    structured = {
        "name": extract_name(text, filename),
        "years_experience": extract_years_experience(text),
        "skills": extract_skills(text),
        "summary": text[:1000]
    }

    return structured


# ---------------------------------------------------------
# PARSE JD
# ---------------------------------------------------------

def parse_jd(text):

    structured = {
        "summary": text[:1500],
        "skills": extract_skills(text),
        "years_required": extract_years_regex(text) or 0
    }

    return structured