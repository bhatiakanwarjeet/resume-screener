import streamlit as st
import pandas as pd
import io
from services.parser import parse_resume, parse_jd
from services.scorer import score_candidate, embed
from services.interview import generate_questions
from services.llm import generate_text
from utils.text import extract_text
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

st.set_page_config(page_title="Resume Screener", layout="wide")

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Job Description"
if "user_jd" not in st.session_state:
    st.session_state.user_jd = ""
if "ai_jd" not in st.session_state:
    st.session_state.ai_jd = ""
if "selected_jd" not in st.session_state:
    st.session_state.selected_jd = ""
if "jd_struct" not in st.session_state:
    st.session_state.jd_struct = None
if "jd_emb" not in st.session_state:
    st.session_state.jd_emb = None
if "results" not in st.session_state:
    st.session_state.results = None
if "questions" not in st.session_state:
    st.session_state.questions = {}
if "notes" not in st.session_state:
    st.session_state.notes = {}
if "jd_confirmed_banner" not in st.session_state:
    st.session_state.jd_confirmed_banner = False

st.title("Resume Screener")

tab_choice = st.radio(
    "",
    ["Job Description", "Resume Screening"],
    index=0 if st.session_state.active_tab == "Job Description" else 1,
    horizontal=True
)

if tab_choice == "Job Description":

    col1, col2 = st.columns(2)

    with col1:
        jd_file = st.file_uploader("Upload JD", type=["pdf","docx","txt"])
        jd_text_input = st.text_area("Or Paste JD", height=250)

        if st.button("Load User JD"):
            jd_text = extract_text(jd_file) if jd_file else jd_text_input
            if jd_text.strip():
                st.session_state.user_jd = jd_text
                with st.spinner("Generating improved JD..."):
                    improved, _ = generate_text(f"Improve this JD:\n\n{jd_text}")
                st.session_state.ai_jd = improved
                st.success("JD loaded and improved.")
            else:
                st.error("Provide a job description.")

    with col2:
        st.markdown("Generate JD")
        title = st.text_input("Job Title")
        department = st.text_input("Department")
        seniority = st.selectbox("Seniority", ["Junior","Mid","Senior","Lead","Manager"])
        key_req = st.text_area("Key Requirements")

        if st.button("Generate JD"):
            if title.strip():
                with st.spinner("Generating JD..."):
                    jd_text, _ = generate_text(
                        f"Generate a professional job description.\n\n"
                        f"Title: {title}\nDepartment: {department}\n"
                        f"Seniority: {seniority}\nRequirements: {key_req}"
                    )
                st.session_state.user_jd = jd_text
                with st.spinner("Improving JD..."):
                    improved, _ = generate_text(f"Improve this JD:\n\n{jd_text}")
                st.session_state.ai_jd = improved
                st.success("JD generated and improved.")
            else:
                st.error("Job title required.")

    if st.session_state.user_jd:

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### User JD")
            st.text_area("", value=st.session_state.user_jd, height=400, disabled=True)

        with col2:
            st.markdown("### AI Improved JD")
            st.text_area("", value=st.session_state.ai_jd, height=400, disabled=True)

        choice = st.radio(
            "Select JD for screening:",
            ["User JD", "AI Improved JD"]
        )

        if st.button("Confirm JD for Screening"):

            selected = (
                st.session_state.user_jd
                if choice == "User JD"
                else st.session_state.ai_jd
            )

            with st.spinner("Preparing JD..."):
                st.session_state.selected_jd = selected
                st.session_state.jd_struct = parse_jd(selected)
                st.session_state.jd_emb = embed(
                    st.session_state.jd_struct["summary"]
                )

            st.session_state.jd_confirmed_banner = True
            st.session_state.active_tab = "Resume Screening"
            st.rerun()

if tab_choice == "Resume Screening":

    if not st.session_state.jd_struct:
        st.warning("Select a Job Description first.")
        st.stop()

    if st.session_state.jd_confirmed_banner:
        st.success("Job Description confirmed. Ready for resume screening.")
        st.session_state.jd_confirmed_banner = False

    st.markdown("<a name='upload_section'></a>", unsafe_allow_html=True)

    st.sidebar.header("Scoring Weights")

    weights = {
        "Skills": st.sidebar.slider("Skills", 0.0, 1.0, 0.3),
        "Experience": st.sidebar.slider("Experience", 0.0, 1.0, 0.2),
        "Semantic": st.sidebar.slider("Semantic", 0.0, 1.0, 0.3),
        "Skill Gap": st.sidebar.slider("Skill Gap", 0.0, 1.0, 0.2)
    }

    top_n = st.sidebar.number_input("Top N Candidates", 1, 50, 5)

    files = st.file_uploader(
        "Upload Resumes",
        type=["pdf","docx","txt"],
        accept_multiple_files=True
    )

    if st.session_state.active_tab == "Resume Screening":
        st.markdown(
            """
            <script>
            window.location.hash = "upload_section";
            </script>
            """,
            unsafe_allow_html=True
        )

    if st.button("Run Screening"):

        if not files:
            st.error("Upload at least one resume.")
            st.stop()

        results = []

        for file in files:
            raw = extract_text(file)
            resume_struct = parse_resume(raw, file.name)

            _, breakdown, _ = score_candidate(
                st.session_state.jd_struct,
                resume_struct,
                st.session_state.jd_emb,
                weights
            )

            results.append({
                "Candidate": resume_struct["name"] or file.name,
                "Breakdown": breakdown,
                "Resume": resume_struct
            })

        st.session_state.results = results

    if st.session_state.results:

        df = pd.DataFrame(st.session_state.results)

        df["Score"] = df.apply(
            lambda row:
            weights["Skills"] * row["Breakdown"]["skill_score"] +
            weights["Experience"] * row["Breakdown"]["experience_score"] +
            weights["Semantic"] * row["Breakdown"]["semantic_score"] +
            weights["Skill Gap"] * row["Breakdown"]["gap_score"],
            axis=1
        )

        df = df.sort_values("Score", ascending=False)
        df = df[df["Candidate"].notna()]
        df_top = df.head(int(top_n))

        st.subheader("Ranked Candidates")

        st.data_editor(
            df_top[["Candidate", "Score"]],
            height=400,
            use_container_width=True,
            hide_index=True,
            disabled=True
        )

        for _, row in df_top.iterrows():

            candidate = row["Candidate"]

            with st.expander(f"{candidate} — {round(row['Score'],3)}"):

                st.markdown("### Resume Overview")
                st.markdown(f"**Name:** {candidate}")
                st.markdown(f"**Skills:** {', '.join(row['Resume']['skills'])}")
                st.markdown("**Professional Summary:**")
                st.write(row["Resume"]["summary"])

                if candidate not in st.session_state.questions:
                    questions, _ = generate_questions(
                        st.session_state.jd_struct["summary"],
                        row["Resume"]["summary"]
                    )
                    st.session_state.questions[candidate] = questions

                st.markdown("### Interview Questions")
                st.write(st.session_state.questions[candidate])

                st.markdown("### Recruiter Notes")
                note = st.text_area(
                    "",
                    value=st.session_state.notes.get(candidate, ""),
                    key=f"note_{candidate}"
                )
                st.session_state.notes[candidate] = note

        styles = getSampleStyleSheet()

        full_buffer = io.BytesIO()
        full_doc = SimpleDocTemplate(full_buffer)
        full_elements = []

        full_elements.append(Paragraph("Full Screening Report", styles["Heading1"]))
        full_elements.append(Spacer(1, 0.3 * inch))
        full_elements.append(Paragraph("Selected Job Description:", styles["Heading2"]))
        full_elements.append(Paragraph(st.session_state.selected_jd, styles["Normal"]))
        full_elements.append(Spacer(1, 0.5 * inch))

        for _, row in df_top.iterrows():

            candidate = row["Candidate"]

            if candidate not in st.session_state.questions:
                questions, _ = generate_questions(
                    st.session_state.jd_struct["summary"],
                    row["Resume"]["summary"]
                )
                st.session_state.questions[candidate] = questions

            recruiter_note = st.session_state.notes.get(candidate, "")

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer)
            elements = []

            elements.append(Paragraph(f"Candidate: {candidate}", styles["Heading2"]))
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph(f"Score: {round(row['Score'], 3)}", styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Resume Summary:", styles["Heading3"]))
            elements.append(Paragraph(row["Resume"]["summary"], styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Interview Questions:", styles["Heading3"]))
            elements.append(Paragraph(st.session_state.questions[candidate], styles["Normal"]))
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Recruiter Notes:", styles["Heading3"]))
            elements.append(Paragraph(recruiter_note or "None", styles["Normal"]))
            elements.append(Spacer(1, 0.5 * inch))

            doc.build(elements)

            st.download_button(
                f"Download {candidate} Report",
                buffer.getvalue(),
                f"{candidate}_report.pdf",
                mime="application/pdf"
            )

            full_elements.append(Paragraph(f"Candidate: {candidate}", styles["Heading2"]))
            full_elements.append(Spacer(1, 0.2 * inch))
            full_elements.append(Paragraph(f"Score: {round(row['Score'], 3)}", styles["Normal"]))
            full_elements.append(Spacer(1, 0.2 * inch))
            full_elements.append(Paragraph("Resume Summary:", styles["Heading3"]))
            full_elements.append(Paragraph(row["Resume"]["summary"], styles["Normal"]))
            full_elements.append(Spacer(1, 0.2 * inch))
            full_elements.append(Paragraph("Interview Questions:", styles["Heading3"]))
            full_elements.append(Paragraph(st.session_state.questions[candidate], styles["Normal"]))
            full_elements.append(Spacer(1, 0.2 * inch))
            full_elements.append(Paragraph("Recruiter Notes:", styles["Heading3"]))
            full_elements.append(Paragraph(recruiter_note or "None", styles["Normal"]))
            full_elements.append(Spacer(1, 0.5 * inch))

        full_doc.build(full_elements)

        st.download_button(
            "Download Full Screening Report",
            full_buffer.getvalue(),
            "full_screening_report.pdf",
            mime="application/pdf"
        )