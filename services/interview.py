from services.llm import generate_text

def generate_questions(jd_summary, resume_summary):
    prompt = (
        "You are a senior technical interviewer.\n\n"
        f"Job Description:\n{jd_summary}\n\n"
        f"Candidate Profile:\n{resume_summary}\n\n"
        "Generate 5 targeted interview questions. "
        "Mix technical and behavioral. Keep each question concise."
    )
    return generate_text(prompt)

def generate_summary(jd_summary, resume_summary):
    prompt = (
        f"Job Description:\n{jd_summary}\n\n"
        f"Candidate Profile:\n{resume_summary}\n\n"
        "Provide a concise executive evaluation summary (5-6 sentences). "
        "Highlight strengths, risks, and hiring recommendation."
    )
    return generate_text(prompt)
