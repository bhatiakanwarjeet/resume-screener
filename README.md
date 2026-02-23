# ResumeScreener

**AI-powered resume screening and job description optimization — go from a job brief to a ranked, explainable shortlist in minutes.**

 **Live Demo:** [resume-screener-tanmay.streamlit.app](https://resume-screener-tanmay.streamlit.app)
 **Source Code:** [github.com/bhatiakanwarjeet/resume-screener](https://github.com/bhatiakanwarjeet/resume-screener)

---

## What It Does

ResumeScreener automates the first stage of hiring. It parses resumes, scores them against a job description using four weighted signals (skill match, experience fit, semantic similarity, skill gap), and produces a ranked shortlist with per-candidate explanations, AI-generated interview questions, and exportable PDF reports — all with a built-in bias audit.

It also includes a JD Generator and Optimizer: write a job description from scratch using AI, or paste an existing one to receive inclusivity, completeness, and readability scores along with specific rewrite suggestions.

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/tanmay1304/resume-screener.git
cd resume-screener
pip install -r requirements.txt
```

> The spaCy model is listed in `requirements.txt` and installs automatically. If it doesn't, run:
> ```bash
> python -m spacy download en_core_web_sm
> ```

### 2. Set your API key

The app uses [Groq](https://console.groq.com) (free tier available) to power LLM features. Set your key as an environment variable:

```bash
export GROQ_API_KEY=your_groq_api_key_here
```

Or create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Project Structure

```
resume-screener/
│
├── app.py                  # Main Streamlit app — routing, UI, PDF export
│
├── services/
│   ├── parser.py           # Resume + JD parsing (name, skills, experience)
│   ├── scorer.py           # 4-signal weighted scoring engine + MiniLM embeddings
│   ├── interview.py        # LLM interview question + evaluation summary generation
│   ├── llm.py              # Groq API wrapper (llama-3.1-8b-instant)
│   ├── bias.py             # Demographic redaction + bias delta analysis
│   └── jd_optimizer.py     # JD quality scoring (inclusivity, completeness, readability) + LLM rewrites
│
├── utils/
│   └── text.py             # PDF / DOCX / TXT text extraction
│
└── requirements.txt
```

---

## User Flow

### Tab 1 — Job Description

This is the starting point. You need to load or generate a JD before screening resumes.

#### Option A: Upload or paste an existing JD

1. Upload a `.pdf`, `.docx`, or `.txt` file — **or** paste the JD text directly into the text area.
2. Click **Load User JD**.
3. The app automatically sends the JD to the LLM and generates an improved version.
4. Both versions (original and AI-improved) appear side-by-side.
5. Select which version to use and click **Confirm JD for Screening**.

#### Option B: Generate a JD from scratch

Fill in the four fields on the right panel and click **Generate JD**:

| Field | Example                                             |
|---|-----------------------------------------------------|
| **Job Title** | Software Engineer                                   |
| **Department** | Engineering                                         |
| **Seniority** | Junior                                              |
| **Key Requirements** | Python, REST APIs, AWS, 3+ years backend experience |

The LLM generates a full JD (Responsibilities, Required Qualifications, Preferred Qualifications, Benefits, Equal Opportunity statement), then automatically improves it. Both versions are shown side-by-side for you to choose from.

> **What "AI Improved" means:** The LLM reviews the JD for clarity, structure, tone, and completeness and produces a rewritten version. You always have the option to stick with the original.

---

### Tab 2 — Resume Screening

Unlocks after a JD is confirmed.

#### Sidebar — Scoring Weights

Adjust how much each signal contributes to the final score using sliders (0.0 – 1.0):

| Weight | What It Measures |
|---|---|
| **Skills** | Fraction of JD-required skills present in the resume (keyword match) |
| **Experience** | Candidate's years of experience vs. years required in the JD |
| **Semantic** | Cosine similarity between JD and resume embeddings (MiniLM, 384-dim) |
| **Skill Gap** | Inverse of missing skills — penalises candidates lacking JD-listed skills |

**Top N Candidates** — set how many candidates appear in the ranked output (1–50).

> Weights do not need to sum to 1. The final score is a weighted sum:
> `score = w_skills × skill_score + w_exp × experience_score + w_sem × semantic_score + w_gap × gap_score`

#### Upload and Run

1. Upload one or more resumes (`.pdf`, `.docx`, `.txt`) — up to 15 at a time.
2. Click **Run Screening**.
3. The app extracts structured data from each resume and scores it against the confirmed JD.

#### Results Table

Candidates are ranked by total weighted score. The table shows Candidate Name and Score. Adjust sidebar weights and re-run to see the list re-rank.

#### Per-Candidate Expander

Click any candidate row to expand:

- **Resume Overview** — extracted name, detected skills, and first 1000 characters of the resume as a summary
- **Score Breakdown** — `skill_score`, `experience_score`, `semantic_score`, `gap_score` (all 0–1)
- **Interview Questions** — 5 tailored questions generated by the LLM based on the JD and the candidate's resume (mix of technical and behavioural)
- **Recruiter Notes** — free-text field; notes are saved in session state and included in PDF exports

#### Exports

- **Download [Candidate] Report** — individual PDF per candidate with score, resume summary, interview questions, and recruiter notes
- **Download Full Screening Report** — single PDF covering all top-N candidates plus the selected JD

---

## JD Quality Scores (jd_optimizer.py)

When generating or loading a JD, three quality dimensions are computed automatically:

| Dimension | How It's Calculated |
|---|---|
| **Inclusivity** | `1 − (biased_terms_found / 7)` — detects: *rockstar, ninja, aggressive, dominant, young, digital native, competitive* |
| **Completeness** | `sections_present / 4` — checks for: *responsibilities, requirements, benefits, equal opportunity* |
| **Readability** | Flesch Reading Ease score normalized to [0, 1] via `textstat` |

The **Optimize JD** function sends the JD to the LLM with a structured prompt asking it to flag problematic phrases and suggest specific rewrites for inclusivity, clarity, and SEO keyword strength.

---

## Bias Audit (bias.py)

The bias auditor redacts demographic signals from a resume before re-scoring it and compares the result to the original score.

**Redacted terms:** `male, female, married, single, indian, american, asian, christian, muslim, hindu, black, white`

**Name redaction:** Any pattern matching `[Capitalized] [Capitalized]` (two-word names) is replaced with `[REDACTED]`.

**Flag threshold:** If the score changes by more than `0.07` after redaction, the audit returns:
`"Score changed by X.XXX after redaction"`

Otherwise: `"No material bias detected"`

---

## How Parsing Works (parser.py)

### Resume Name Extraction — 3-layer waterfall
1. **spaCy NER** — looks for `PERSON` entities in the first 3000 characters
2. **Heuristic** — scans the first 10 lines for a 2–4 word capitalized string that isn't a common header
3. **Filename fallback** — strips numbers and underscores from the filename and title-cases it

### Experience Extraction — 3-layer waterfall
1. **Regex** — finds patterns like `"5+ years"`, `"3 years experience"`
2. **Date range** — extracts all 4-digit years from the text and computes `max_year − min_year`
3. **LLM fallback** — sends the first 2000 characters to the LLM with the prompt `"Return only an integer"`

### Skill Extraction
Deterministic keyword match against a fixed list of 13 skills:
`python, sql, java, aws, docker, kubernetes, excel, tableau, machine learning, deep learning, project management, react, node`

---

## Sample Data

### Sample JD (paste directly into the app)

```
Software Engineer — Backend
Engineering | Mid-Level | 3+ Years Experience

We are looking for a backend Software Engineer to join our growing platform team.

Responsibilities:
- Design and build scalable REST APIs using Python and FastAPI
- Manage and optimize SQL and NoSQL databases
- Deploy and monitor services on AWS (EC2, Lambda, RDS)
- Collaborate with frontend engineers and product managers
- Participate in code reviews and technical design discussions

Required Qualifications:
- 3+ years of professional backend development experience
- Strong proficiency in Python
- Experience with SQL databases (PostgreSQL preferred)
- Familiarity with AWS services and Docker
- Understanding of RESTful API design principles

Preferred Qualifications:
- Experience with Kubernetes or container orchestration
- Exposure to machine learning pipelines or data engineering
- React or Node.js experience is a plus

Benefits:
- Competitive salary and equity
- Remote-first culture
- Health, dental, and vision coverage
- $1,500 annual learning budget

We are an equal opportunity employer. We celebrate diversity and are committed to creating an inclusive environment for all employees.
```

### Or use the Generate JD form:

| Field | Value |
|---|---|
| Job Title | Software Engineer |
| Department | Engineering |
| Seniority | Mid |
| Key Requirements | Python, SQL, AWS, Docker, REST APIs, 3+ years backend experience |



## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `openai` | API client (pointed at Groq's OpenAI-compatible endpoint) |
| `sentence-transformers` | MiniLM embeddings for semantic scoring |
| `scikit-learn` | Cosine similarity calculation |
| `spacy` + `en_core_web_sm` | Named entity recognition for name extraction |
| `PyMuPDF` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `reportlab` | PDF report generation |
| `textstat` | Flesch readability scoring for JD optimizer |
| `pandas` | Results table handling |
| `numpy==1.26.4` | Pinned for sentence-transformers compatibility |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` |  Yes | API key from [console.groq.com](https://console.groq.com) — free tier available |

---

## Notes & Known Limitations

- **Skill detection is keyword-based** — only the 13 listed skills are detected. Resumes using different terminology (e.g. `FastAPI` instead of `python`, `dbt` instead of `sql`) may score lower than expected.
- **Session state only** — results, notes, and questions are lost on page refresh. There is no database persistence.
- **Synchronous LLM calls** — screening 10+ resumes or running the JD optimizer may take 15–25 seconds depending on Groq API latency.
- **English only** — parsing and scoring are optimised for English-language resumes and JDs.
- **Experience parsing edge cases** — resumes without explicit year mentions or date ranges will fall back to the LLM, which may return 0 for ambiguous inputs.
