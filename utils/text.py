import fitz
from docx import Document
import io

def extract_text(file):
    if file.name.endswith(".pdf"):
        doc = fitz.open(stream=file.read(), filetype="pdf")
        return "".join([page.get_text() for page in doc])

    if file.name.endswith(".docx"):
        doc = Document(io.BytesIO(file.read()))
        return "\n".join([p.text for p in doc.paragraphs])

    return file.read().decode("utf-8")