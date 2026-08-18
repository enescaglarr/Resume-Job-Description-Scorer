import os
import time
import streamlit as st
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from sklearn.metrics.pairwise import cosine_similarity
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from constants import GOOGLE_API_KEY, GROQ_API_KEY, GROQ_MODEL_NAME, EMBEDDING_MODEL_NAME, TEMPLATE_CONTENT, \
    comparison_prompt, resume_analysis_prompt, job_description_analysis_prompt, gap_analysis_prompt, \
    actionable_steps_prompt, experience_enhancement_prompt, additional_qualifications_prompt, \
    resume_tailoring_prompt, relevant_skills_highlight_prompt, resume_formatting_prompt, resume_length_prompt
from directory_reader import DirectoryReader

st.set_page_config(page_title="Resume Reviewer")
os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY
os.environ['GROQ_API_KEY'] = GROQ_API_KEY


with st.sidebar:
    st.header('Resume Reviewer')
    st.write("Upload your resume and JD for my recommendations.")
    # Resume and JD file uploader in the sidebar
    resume_file = st.file_uploader("Upload your resume (pdf file only)", type=["pdf"])
    jd_file = st.file_uploader("Upload your JD (txt file only)", type=["txt"])
    st.caption("...or paste the job description text directly")
    jd_pasted_text = st.text_area("Job description text", height=120, label_visibility="collapsed")


def compute_match_score(resume_text, jd_text):
    embedder = GoogleGenerativeAIEmbeddings(google_api_key=GOOGLE_API_KEY, model=EMBEDDING_MODEL_NAME)
    resume_vector = embedder.embed_query(resume_text)
    jd_vector = embedder.embed_query(jd_text)
    similarity = cosine_similarity([resume_vector], [jd_vector])[0][0]
    return int(round(similarity * 100))


st.title('Resume Reviewer')

jd_provided = bool(jd_pasted_text and jd_pasted_text.strip()) or jd_file is not None


def calculate_score():
    if resume_file is None or not jd_provided:
        st.warning("Please upload both your resume and a job description before calculating the match score.")
        return

    directory_reader = DirectoryReader("", "")
    resume_file.seek(0)
    resume_text = directory_reader.extract_text_from_pdf(resume_file)
    if len(resume_text) <= 1:
        # Text-layer extraction found nothing (e.g. a scanned/image-only PDF) - fall back to OCR
        with st.spinner("No text layer found, running OCR..."):
            resume_text = directory_reader.extract_text_from_image(resume_file.getvalue())

    # Pasted text takes priority over an uploaded file if both are given
    if jd_pasted_text and jd_pasted_text.strip():
        jd_text = jd_pasted_text.strip()
    else:
        jd_text = jd_file.getvalue().decode("utf-8")

    if len(resume_text) <= 1 or len(jd_text.strip()) == 0:
        st.error("Couldn't extract any text from the uploaded resume. Try a different file (or a text-based PDF).")
        return

    try:
        with st.spinner("Calculating match score..."):
            match_score_value = compute_match_score(resume_text, jd_text)
        st.session_state["resume_content"] = resume_text
        st.session_state["job_description_content"] = jd_text
        st.session_state["match_score"] = match_score_value
    except Exception as e:
        st.error(f"Couldn't calculate the match score: {e}")


resume_content = st.session_state.get("resume_content")
job_description_content = st.session_state.get("job_description_content")
match_score = st.session_state.get("match_score")

if match_score is not None:
    st.subheader("Match Score")
    score_col, detail_col = st.columns([1, 3])
    with score_col:
        st.metric("Resume ↔ JD", f"{match_score}%")
    with detail_col:
        st.progress(match_score / 100)
        if match_score >= 70:
            st.success("Strong match")
        elif match_score >= 50:
            st.warning("Moderate match")
        else:
            st.error("Weak match")
    st.divider()

match_score_context = f"Match score (embedding similarity between resume and job description): {match_score}%.\n\n" \
    if match_score is not None else ""
SYSTEM_PROMPT = "\n\n" + TEMPLATE_CONTENT + match_score_context + "<RESUME STARTS HERE> {}. <RESUME ENDS HERE> with the job description: <JOB DESCRIPTION STARTS HERE> {}.<JOB DESCRIPTION ENDS HERE>\n\nBe crisp and clear in response.DO NOT provide the resume and job description in the response\n\n".format(resume_content or "", job_description_content or "")
llm = ChatGroq(temperature=0.0, model=GROQ_MODEL_NAME)


# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]


def clear_chat_history():
    global resume_chain
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    resume_chain = ConversationChain(
        llm=llm,
        prompt=prompt_template,
        memory=memory,
        verbose=False
    )


# Display chat messages, with a Clear Chat History button aligned to the first message
messages_col, clear_col = st.columns([5, 1])
with clear_col:
    st.button('Clear Chat History', on_click=clear_chat_history)
with messages_col:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def generate_report_pdf(report_text, title="Resume Report"):
    # fpdf2's core fonts only support Latin-1, so swap common "smart" punctuation
    # the LLM tends to produce for plain ASCII before rendering.
    replacements = {
        "–": "-", "—": "-", "‑": "-", "‐": "-",
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "→": "->", "↔": "<->", "•": "-", "…": "...",
        "≈": "~", "×": "x",
    }
    for old, new in replacements.items():
        report_text = report_text.replace(old, new)
    report_text = report_text.encode("latin-1", errors="replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.set_font("Helvetica", size=10)
    for line in report_text.split("\n"):
        if line:
            pdf.multi_cell(0, 5, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.ln(5)
    return bytes(pdf.output())


def generate_report_section(prompt_text, max_retries=4):
    # Stateless call (no shared conversation memory) so each section only sends its own
    # prompt - keeps token usage per-request low instead of growing with each section.
    messages = [SystemMessage(content=TEMPLATE_CONTENT), HumanMessage(content=prompt_text)]
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages).content
        except Exception as e:
            if "429" in str(e) or "413" in str(e) or "rate_limit" in str(e).lower():
                time.sleep(3 * (attempt + 1))
            else:
                raise
    return llm.invoke(messages).content


def generate_report():
    if not (resume_content and job_description_content):
        st.warning("Calculate the match score first for a detailed report.")
        return

    user_message = {"role": "user", "content": "Generate a Report!"}
    st.session_state.messages.append(user_message)
    with st.chat_message("assistant"):
        sections = {
            "Comparison Analysis": comparison_prompt.format(resume_content, job_description_content),
            "Resume Analysis": resume_analysis_prompt.format(resume_content),
            "Job Description Analysis": job_description_analysis_prompt.format(job_description_content),
            "Gap Analysis": gap_analysis_prompt.format(resume_content, job_description_content),
            "Actionable Steps": actionable_steps_prompt.format(resume_content, job_description_content),
            "Experience Enhancement": experience_enhancement_prompt.format(resume_content, job_description_content),
            "Additional Qualifications": additional_qualifications_prompt.format(resume_content, job_description_content),
            "Resume Tailoring": resume_tailoring_prompt.format(resume_content, job_description_content),
            "Relevant Skills Highlight": relevant_skills_highlight_prompt.format(resume_content, job_description_content),
            "Resume Formatting": resume_formatting_prompt.format(resume_content, job_description_content),
            "Resume Length": resume_length_prompt.format(resume_content, job_description_content),
        }

        progress = st.empty()
        results = {}
        for i, (title, prompt_text) in enumerate(sections.items(), start=1):
            progress.text(f"Generating report... {i}/{len(sections)}: {title}")
            results[title] = generate_report_section(prompt_text)
        progress.empty()

        report = "\n\n".join(f"{title}:\n{content}" for title, content in results.items())

    report_message = {"role": "assistant", "content": report}
    st.session_state.messages.append(report_message)
    st.session_state["last_report"] = report


system_message = SystemMessage(content=TEMPLATE_CONTENT)
human_message = HumanMessagePromptTemplate.from_template("{history} User:{input} Assistant:")
prompt_template = ChatPromptTemplate(messages=[system_message, human_message], validate_template=True)
memory = ConversationBufferWindowMemory(k=2)

if llm is not None:
    resume_chain = ConversationChain(
        llm=llm,
        prompt=prompt_template,
        memory=memory,
        verbose=False
    )
else:
    resume_chain = None


def generate_response(prompt_input):
    output = resume_chain.predict(input=prompt_input)
    return output


calc_col, report_col = st.sidebar.columns(2)
calc_col.button("📊 Calculate Match Score", use_container_width=True, type="primary", on_click=calculate_score)
report_col.button('Generate Report', use_container_width=True, on_click=generate_report,
                   help="Calculate score first for a detailed report")

if "last_report" in st.session_state:
    st.sidebar.download_button(
        "⬇️ Download Report as PDF",
        data=generate_report_pdf(st.session_state["last_report"]),
        file_name="resume_report.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)


def get_llm_response():
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt + SYSTEM_PROMPT)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)


# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    get_llm_response()
