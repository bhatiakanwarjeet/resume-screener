import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

def embed(text):
    return model.encode(text)

def score_candidate(jd_struct, resume_struct, jd_embedding, weights):

    jd_skills = set(jd_struct.get("skills", []))
    resume_skills = set(resume_struct.get("skills", []))

    years_required = jd_struct.get("years_required", 0)
    years_experience = resume_struct.get("years_experience", 0)

    # Skill Match
    skill_score = (
        len(jd_skills.intersection(resume_skills)) / len(jd_skills)
        if jd_skills else 0
    )

    # Experience Fit
    experience_score = (
        min(years_experience / years_required, 1)
        if years_required > 0 else 0
    )

    # Semantic Match
    resume_embedding = embed(resume_struct["summary"])
    semantic_score = cosine_similarity(
        [jd_embedding], [resume_embedding]
    )[0][0]

    # Skill Gap
    gap_score = (
        1 - (len(jd_skills - resume_skills) / len(jd_skills))
        if jd_skills else 0
    )

    breakdown = {
        "skill_score": round(float(skill_score), 3),
        "experience_score": round(float(experience_score), 3),
        "semantic_score": round(float(semantic_score), 3),
        "gap_score": round(float(gap_score), 3)
    }

    total_score = (
        weights["Skills"] * breakdown["skill_score"] +
        weights["Experience"] * breakdown["experience_score"] +
        weights["Semantic"] * breakdown["semantic_score"] +
        weights["Skill Gap"] * breakdown["gap_score"]
    )

    return round(float(total_score), 3), breakdown, resume_embedding