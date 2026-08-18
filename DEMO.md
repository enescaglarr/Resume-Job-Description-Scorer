# Demo Scenarios

Reference script for demoing the Resume JD Scorer web app (`./run.sh`). Each scenario
gives the exact resume/JD files to load and the exact chat question to ask, so the demo
is reproducible. Results captured below are from actual runs (2026-08-18/19) using
`resume_data_synthetic/` (safe to share - no real PII) and Gemini for scoring / Groq
(`openai/gpt-oss-20b`) for chat and reports.

---

## Scenario 1 - Strong match + chat gap analysis ✅ tested

**Resume:** `resume_data_synthetic/Data Engineer/resume-40.pdf`
**JD:** `jd_data/de3_amazon.txt`

**Steps:** Upload both → click "Calculate Match Score" → ask the chat a follow-up question.

**Result:** **78% - "Strong match"**

**Chat question:** `Why isn't this 100%? What's my biggest gap?`

**Chat answer (verbatim):**
> The 78% score reflects that your résumé covers many core data-engineering skills, but it falls short on several key areas the Amazon Prime role explicitly requires:
>
> | Gap | Why it matters for the job | How to address it |
> |---|---|---|
> | AWS-specific services (Redshift, S3, Glue, EMR, Kinesis, Firehose, Lambda, IAM) | The role is built around the AWS stack; experience with these services is listed as a preferred qualification. | Add any projects where you used these services. If you haven't, consider a short course or a side project that demonstrates your ability to work with them. |
> | SQL & data modeling | The description stresses "data modeling, warehousing, and building ETL pipelines." | Highlight any SQL work, schema design, or ETL logic you've written. If you used Spark or Airflow for ETL, frame it in terms of data modeling and warehouse design. |
> | Business Intelligence / reporting | The team delivers real-time insights to marketing, finance, and analytics stakeholders. | Mention any dashboards, metrics, or reporting you've built, and the impact on business decisions. |
> | Non-relational data stores | Preferred to show versatility with object, document, or key-value stores. | If you've used DynamoDB, S3, or similar, list it. If not, note your familiarity or willingness to learn. |
> | Leadership / mentoring | The role expects technical leadership and mentoring of a data-engineering team. | If you've led projects, mentored junior engineers, or coordinated cross-functional teams, quantify that experience. |
>
> **Bottom line:** Your résumé demonstrates solid engineering chops, but it lacks explicit evidence of AWS-centric tooling, SQL/data-modeling depth, BI/reporting focus, and leadership - all of which are central to the Amazon Prime Data Engineer position. Adding concrete examples in these areas will push the match score closer to 100%.

**Why this works as a demo:** A Data Engineer resume against Amazon Prime's Data Engineer JD -
same discipline, so the score lands well into green "Strong match" territory, and the chat still
finds real, specific gaps (AWS service names pulled straight from the JD) instead of generic praise.

---

## Scenario 2 - Weak/mismatched pair (contrast) ✅ tested

**Resume:** `resume_data_synthetic/Big Data Analyst/resume-1.pdf`
**JD:** `jd_data/mlops2_convin.txt` (Big Data Analyst resume vs. startup backend/AI-product JD - deliberate mismatch)

**Steps:** Upload both → click "Calculate Match Score" → ask the chat a follow-up question.

**Result:** **66% - "Moderate match"** (12 points below Scenario 1's 78%, and downgraded from
green "Strong" to yellow "Moderate" - a clear, visible contrast between a same-discipline
pair and a cross-discipline one)

**Chat question:** `Why am I not a good fit for this role?`

**Chat answer (verbatim):**
> **Why the fit isn't strong**
>
> | Job Requirement | Resume Evidence | Gap |
> |---|---|---|
> | Python backend development | No mention of Python or backend coding | Core language for the role is missing |
> | ChatGPT / NLP integration | No NLP or language-model experience | Key AI component absent |
> | DevOps & CI/CD | No explicit DevOps, deployment, or monitoring experience | Required for cloud-scale operations |
> | Cloud services breadth | AWS EMR experience only | Limited exposure to the full AWS stack and other clouds |
> | Backend architecture/design | Focus on data pipelines, not API or service design | Lacks architectural depth for SaaS products |
>
> **Match score context (66%)**
> A 66% similarity indicates that while you have relevant data-engineering skills, the resume does not cover the critical backend-development, Python, NLP, or DevOps aspects that the role demands.
>
> **What to improve**
> 1. Add Python projects - Highlight any scripts, micro-services, or data-processing code written in Python.
> 2. Show NLP experience - If you've used libraries like Hugging Face, spaCy, or integrated language models, list them.
> 3. DevOps exposure - Mention CI/CD pipelines, containerization (Docker), orchestration (Kubernetes), or cloud deployment scripts.
> 4. Broader cloud skills - Include other AWS services (Lambda, ECS, RDS) or experience with Azure/GCP.
> 5. Backend architecture - Briefly describe any API design, micro-service patterns, or system scalability work.
>
> By addressing these gaps, your resume will align more closely with the backend-focused, AI-centric nature of the Convin role.

**Why this works as a demo:** The 78% → 66% drop (and the green → yellow label flip) makes the
contrast between a matched and mismatched pair immediately visible. The chat answer is fully
grounded in a specific requirement-vs-resume table, not generic advice.

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
