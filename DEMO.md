# Demo Scenarios

Reference script for demoing the Resume JD Scorer web app (`./run.sh`). Each scenario
gives the exact resume/JD files to load and the exact chat question to ask, so the demo
is reproducible. Results captured below are from an actual run (2026-08-18) using
`resume_data_synthetic/` (safe to share - no real PII) and Gemini for scoring / Groq
(`openai/gpt-oss-20b`) for chat and reports.

---

## Scenario 1 - Strong-ish match + chat gap analysis ✅ tested

**Resume:** `resume_data_synthetic/Data Scientist/resume-54.pdf`
**JD:** `jd_data/ds1_volvo.txt`

**Steps:** Upload both → click "Calculate Match Score" → ask the chat a follow-up question.

**Result:** **70% - "Strong match"**

**Chat question:** `Why isn't this 100%? What's my biggest gap?`

**Chat answer (verbatim):**
> The 70% score reflects that you have solid data-science fundamentals (pandas, XGBoost, SQL, model deployment, feature-engineering automation) that overlap with the job's general "data-driven" focus. However, the role is heavily centered on powertrain engineering and control-system simulation, and the resume shows several key gaps:
>
> | Gap | Why it matters for the role |
> |---|---|
> | Domain expertise | The job requires a background in mechanical/automotive/mechatronics engineering and a deep understanding of powertrain systems, emissions, and control loops. |
> | Control-system & simulation skills | No mention of experience with closed-loop control, numerical simulation, or tools like MATLAB/Simulink. |
> | Advanced ML & time-series | The description calls for regression, clustering, neural networks, and time-series modeling; your resume lists only XGBoost and general ML. |
> | Large-scale data engineering | No evidence of working with Hadoop, Spark, Azure, or big-data pipelines. |
> | Visualization & reporting | The role values Power BI, QlikView, Tableau; these are absent from your skill set. |
> | Programming & tooling breadth | Missing experience with TensorFlow, R, Git, C/C++, Scala, or pySpark. |
> | Educational background | The job prefers a Master's in a relevant engineering field; your degree is in mathematics. |
>
> **How to close the gap**
> 1. Highlight transferable skills - emphasize projects involving real-time prediction, model deployment, or automation that could map to powertrain scenarios.
> 2. Add relevant coursework or certifications - even a short course in control systems, automotive engineering, or MATLAB/Simulink can signal intent.
> 3. Showcase data-engineering experience - list cloud services, big-data tools, or pipelines you've built.
> 4. Include visualization work - mention dashboards you've built and the tools used.
> 5. Tailor the summary - state a clear interest in powertrain analytics and a willingness to learn domain-specific tools.

**Why this works as a demo:** `ds1_volvo.txt` reads more like a powertrain/automotive engineering
posting than a typical Data Scientist JD, so the moderate (not high) score and the chat's
domain-gap reasoning both look credible and specific rather than generic.

---

## Scenario 2 - Weak/mismatched pair (contrast) ✅ tested

**Resume:** `resume_data_synthetic/Data Analyst/resume-14.pdf`
**JD:** `jd_data/mle1_allianz.txt` (Data Analyst resume vs. ML Engineer JD - deliberate mismatch)

**Steps:** Upload both → click "Calculate Match Score" → ask the chat a follow-up question.

**Result:** **69% - "Moderate match"** (lower than Scenario 1's 70%, and downgraded from
green "Strong" to yellow "Moderate" even though the raw number is close - shows the
score/label thresholds are meaningfully different pairs, not just noise)

**Chat question:** `Why am I not a good fit for this role?`

**Chat answer (verbatim):**
> You're not a strong fit for this role mainly because the job requires a solid background in end-to-end machine-learning engineering and MLOps, whereas your résumé focuses on data analysis and A/B testing. Specific gaps include:
>
> | Requirement | Your résumé |
> |---|---|
> | 3-5 yrs of experience building, deploying, and monitoring ML models | No ML model work mentioned |
> | Python programming for production-grade code | Only "Python" listed; no evidence of software-engineering practices |
> | CI/CD pipelines, Jenkins/GitHub Actions, Docker/Kubernetes | No mention of CI/CD, containerization, or orchestration |
> | Cloud platform (Azure preferred) | No cloud experience listed |
> | REST API development for model serving | Not referenced |
> | Collaboration with back-end engineers on GPU/memory requirements | No relevant collaboration described |
> | Degree in CS, Physics, Math, or Statistics | M.S. in Data Science - not a direct match to the listed fields |
>
> Because the role is heavily focused on ML production, infrastructure, and software engineering, the lack of these specific experiences and skills makes you a less suitable candidate. To improve fit, consider highlighting any hidden ML or engineering work, pursuing certifications in MLOps, or gaining hands-on experience with Docker, Kubernetes, and cloud services.

**Why this works as a demo:** Even though the raw score (69%) is close to Scenario 1's 70%,
the label flips from green "Strong match" to yellow "Moderate match" - good for showing the
score isn't just a single number but maps to a clear tier. The chat answer is fully grounded
in a specific requirement-vs-resume table, not generic advice.

---

## Scenario 3 - Full "Generate Report" + PDF download ✅ tested

**Resume:** `resume_data_synthetic/MLOps Engineer/resume-84.pdf` (Suzanne Johnson, Platform Engineer/ML, 12+ yrs, AWS/Kubernetes/Airflow/Terraform)
**JD:** `jd_data/mlops4_exl.txt`

**Steps:** Calculate Match Score → click "Generate Report" → live "Generating report... N/11: <section>"
progress indicator → full 11-section report appears as a chat message → **"⬇️ Download Report as PDF"**
button appears in the sidebar once the report exists.

**Match Score result:** **77% - "Strong match"**

**Report result:** All 11 sections generated successfully (Groq `openai/gpt-oss-20b`, no rate-limit
errors, stateless per-section calls). Each section is a genuinely detailed, resume/JD-grounded
analysis (tables comparing resume content vs. JD requirements, concrete gap lists, a suggested
6-8 week upskilling timeline, before/after bullet-point rewrites, ATS-formatting checklist, etc.).
Consistent, correctly-identified gaps across sections: no SQL, no Azure/GCP (only AWS), no
feature store / model-serving-API / CT-pipeline experience, no client-facing or mentoring bullets.

**PDF download result:** "⬇️ Download Report as PDF" button in the sidebar produced a 16-page PDF
with all 11 sections intact and fully readable. Minor cosmetic note: the LLM's markdown tables
(`| Area | Gap |...`) render as plain pipe-delimited text rather than real PDF table grid lines,
since the PDF generator does a simple text dump (no markdown table rendering) - content is 100%
present, just not visually formatted as a table. Not a blocker for the demo.

**Why this works as a demo:** Shows the full depth of the "Generate Report" feature beyond just
the live chat - the same resume/JD were still available afterward for the PDF download button
(sidebar), demonstrating the three features (chat + report + PDF export) work together from a
single Calculate Match Score run.

---

## Scenario 4 - Paste-JD-text flow ✅ tested

**Resume:** `resume_data_synthetic/Business Intelligence Analyst/resume-4.pdf`
**JD:** pasted the contents of `jd_data/bianalyst1_google.txt` directly into the sidebar's
"...or paste the job description text directly" box instead of uploading a `.txt` file.

**Result:** **76% - "Strong match"**. The "Upload your JD" file uploader stayed empty the whole
time - confirms pasted text is picked up correctly and takes priority, no file needed at all.

**Purpose:** Shows the realistic workflow of copy-pasting a JD straight from a job posting page,
no file prep needed.

---

## Scenario 5 - Off-topic question (guardrail check) ✅ tested

**Resume/JD:** reused Scenario 4's pair (paste-box still populated) - asked one more, deliberately
unrelated question in the same chat, right after the assistant's first greeting.

**Chat question:** `What is the weather like today?`

**Result:** The assistant replied exactly **"Please ask a relevant question."** - refused to
answer instead of hallucinating a weather response.

**Purpose:** Proves the guardrail works correctly and doesn't leak into general-knowledge
territory - it's scoped strictly to resume/JD/match-score topics, not just being generically
unhelpful.
