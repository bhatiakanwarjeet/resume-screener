from services.llm import generate_text

def generate_questions(jd_summary, resume_summary):
    prompt = f"""
    You are a senior technical interviewer.

    Job Description:
    {jd_summary}

    Candidate Profile:
    {resume_summary}

    Generate 5 targeted interview questions.
    Mix technical and behavioral.
    Keep concise.
    """
    return generate_text(prompt)

def generate_summary(jd_summary, resume_summary):
    prompt = f"""
    Job Description:
    {jd_summary}

    Candidate Profile:
    {resume_summary}

    Provide a concise executive evaluation summary (5-6 sentences).
    Highlight strengths, risks, and hiring recommendation.
    """
    return generate_text(prompt)