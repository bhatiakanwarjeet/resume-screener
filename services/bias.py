import re

SENSITIVE_TERMS = [
    "male","female","married","single",
    "indian","american","asian","christian",
    "muslim","hindu","black","white"
]

def redact(text):
    redacted = text
    for term in SENSITIVE_TERMS:
        redacted = re.sub(term, "[REDACTED]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"[A-Z][a-z]+\s[A-Z][a-z]+", "[REDACTED]", redacted)
    return redacted

def analyze_bias(original_score, redacted_score):
    delta = abs(original_score - redacted_score)
    if delta > 0.07:
        return f"Score changed by {round(delta,3)} after redaction"
    return "No material bias detected"