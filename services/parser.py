import re
import spacy
from datetime import datetime
from services.llm import generate_text

nlp = spacy.load("en_core_web_sm")

CURRENT_YEAR = datetime.now().year

COMMON_HEADERS = {
    "resume", "curriculum vitae", "life philosophy",
    "personal details", "objective", "summary",
    "experience", "education", "skills", "profile",
    "contact", "about me", "work experience",
    "professional experience", "career objective",
    "technical skills", "core competencies",
    "certifications", "projects", "references",
    "bachelor of science", "master of science",
}

TITLE_WORDS = {
    "engineer", "developer", "manager", "analyst", "designer",
    "consultant", "specialist", "director", "lead", "architect",
    "intern", "associate", "senior", "junior", "fresher",
    "software", "data", "product", "marketing", "sales",
    "university", "college", "institute", "school", "bachelor",
    "master", "doctor", "phd", "mba", "bsc", "msc",
    "street", "avenue", "road", "city", "state", "usa",
    "india", "new", "york", "san", "francisco", "remote",
    "framework", "server", "angular", "entity", "react",
    "spring", "django", "docker", "linux", "windows",
    "express", "flutter", "kotlin", "swift", "oracle",
    "visual", "studio", "azure", "google", "amazon",
    "cloud", "native", "mobile", "web", "api", "rest",
    "agile", "scrum", "devops", "github", "gitlab",
}


def is_valid_name(name):
    if not name:
        return False
    name = name.strip()
    words = name.split()
    if len(words) < 2 or len(words) > 4:
        return False
    if any(char.isdigit() for char in name):
        return False
    if re.search(r"[^a-zA-Z\s'\-]", name):
        return False
    for word in words:
        if not word[0].isupper():
            return False
        if re.search(r"[A-Z]{2,}", word):
            return False
    if any(w.lower() in TITLE_WORDS for w in words):
        return False
    if name.lower() in COMMON_HEADERS:
        return False
    if len(name) > 40:
        return False
    return True


def extract_name_llm(text):
    try:
        prompt = (
            "You are extracting a person's full name from a resume. "
            "The name is typically at the very top of the document. "
            "It may be a Western, Indian, Asian, or other non-English name. "
            "Return ONLY the full name as it appears, nothing else — "
            "no job titles, no skills, no location. "
            "If you cannot confidently identify a name, return NULL.\n\n"
            f"{text[:1500]}"
        )
        result, _ = generate_text(prompt)
        result = result.strip().strip('"').strip("'").split("\n")[0]
        if result and result.upper() != "NULL":
            return result
    except:
        pass
    return None


def extract_name(text, filename=None):
    doc = nlp(text[:2000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            candidate = ent.text.strip().title()
            if is_valid_name(candidate):
                return candidate

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:6]:
        if line.isupper():
            line = line.title()
        if is_valid_name(line):
            return line

    if filename:
        name_part = re.sub(r"\.(pdf|docx|txt|doc)$", "", filename, flags=re.IGNORECASE)
        clean = re.sub(r"[_\-\.]", " ", name_part)
        clean = re.sub(r"\s+", " ", clean).strip().title()
        if is_valid_name(clean):
            return clean

    return extract_name_llm(text)


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
    years = extract_years_regex(text)
    if years:
        return years
    years = extract_years_from_dates(text)
    if years:
        return years
    years = extract_years_llm(text)
    if years:
        return years
    return 0


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


def parse_resume(text, filename=None):
    return {
        "name": extract_name(text, filename),
        "years_experience": extract_years_experience(text),
        "skills": extract_skills(text),
        "summary": text[:1000]
    }


def parse_jd(text):
    return {
        "summary": text[:1500],
        "skills": extract_skills(text),
        "years_required": extract_years_regex(text) or 0
    }
