"""
End-to-end test: scores every resume (real + synthetic) against every JD, checks whether
the highest-scoring JD for each resume belongs to the resume's own job category, and
generates a handful of sample "Generate Report" outputs for manual review.

Usage:
    python scripts/test_scoring.py

Writes results to the directory given by TEST_OUTPUT_DIR (env var) or ./test_output/:
    score_matrix.csv      - every (resume, jd) pair with its similarity score
    accuracy_summary.txt  - top-1 category accuracy, per-category breakdown
    sample_reports/*.txt  - full 11-section reports for a few sample resume/JD pairs
"""
import glob
import os
import re
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from directory_reader import DirectoryReader
from constants import (
    GOOGLE_API_KEY, GROQ_API_KEY, EMBEDDING_MODEL_NAME, GROQ_MODEL_NAME, TEMPLATE_CONTENT,
    comparison_prompt, resume_analysis_prompt, job_description_analysis_prompt,
    gap_analysis_prompt, actionable_steps_prompt, experience_enhancement_prompt,
    additional_qualifications_prompt, resume_tailoring_prompt,
    relevant_skills_highlight_prompt, resume_formatting_prompt, resume_length_prompt,
)
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUTPUT_DIR = os.environ.get("TEST_OUTPUT_DIR", os.path.join(ROOT, "test_output"))
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "sample_reports"), exist_ok=True)

RESUME_GLOBS = {
    "real": os.path.join(ROOT, "resume_data", "*", "*"),
    "synthetic": os.path.join(ROOT, "resume_data_synthetic", "*", "*"),
}
JD_GLOB = os.path.join(ROOT, "jd_data", "*")

CATEGORY_TO_JD_PREFIX = {
    "data_engineer": "de", "data_analyst": "dataanalyst", "big_data_analyst": "bigdataanalyst",
    "mlops_engineer": "mlops", "data_scientist": "ds", "data_architect": "da",
    "machine_learning_engineer": "mle", "business_intelligence_analyst": "bianalyst",
}

BATCH_SIZE = 10


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def extract_resume_text(dr, path):
    text = dr.extract_text_from_pdf(path)
    if len(text) <= 1:
        with open(path, "rb") as f:
            text = dr.extract_text_from_image(f.read())
    return text


def load_resumes():
    dr = DirectoryReader("", "")
    records = []
    for source, pattern in RESUME_GLOBS.items():
        paths = sorted(glob.glob(pattern))
        for i, path in enumerate(paths):
            parts = os.path.normpath(path).split(os.sep)
            category = parts[-2].replace(" ", "_").lower()
            resume_name = os.path.basename(parts[-1]).replace("-", "_").lower().replace(".pdf", "")
            key = f"{source}_{category}_{resume_name}"
            text = extract_resume_text(dr, path)
            records.append({"key": key, "source": source, "category": category, "text": text})
            log(f"  [{source}] {i + 1}/{len(paths)} {resume_name} ({len(text)} chars)")
    return records


def load_jds():
    records = []
    for path in sorted(glob.glob(JD_GLOB)):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read().strip().lower()
        name = os.path.basename(path).replace(".txt", "")
        category = re.sub(r"\d+_[a-z]+$", "", name)
        records.append({"key": name, "category": category, "text": text})
    return records


def embed_with_retry(embedder, batch, max_retries=6):
    for attempt in range(max_retries):
        try:
            return embedder.embed_documents(batch)
        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in type(e).__name__:
                wait = min(60, 5 * (2 ** attempt))
                log(f"  rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Exceeded max retries due to rate limiting")


def embed_texts(embedder, texts):
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        vectors.extend(embed_with_retry(embedder, batch))
        log(f"  embedded {min(i + BATCH_SIZE, len(texts))}/{len(texts)}")
        time.sleep(2)  # stay under free-tier requests-per-minute limits
    return np.array(vectors)


def main():
    log("Loading resumes (real + synthetic)...")
    resumes = load_resumes()
    log(f"Loaded {len(resumes)} resumes")

    log("Loading JDs...")
    jds = load_jds()
    log(f"Loaded {len(jds)} JDs")

    embedder = GoogleGenerativeAIEmbeddings(google_api_key=GOOGLE_API_KEY, model=EMBEDDING_MODEL_NAME)

    log("Embedding resumes...")
    resume_vectors = embed_texts(embedder, [r["text"] for r in resumes])
    log("Embedding JDs...")
    jd_vectors = embed_texts(embedder, [j["text"] for j in jds])

    log("Computing similarity matrix...")
    sim_matrix = cosine_similarity(resume_vectors, jd_vectors)

    rows = []
    for i, r in enumerate(resumes):
        for j, jd in enumerate(jds):
            score = int(round(sim_matrix[i, j] * 100))
            rows.append({
                "resume_key": r["key"], "resume_source": r["source"], "resume_category": r["category"],
                "jd_key": jd["key"], "jd_category": jd["category"], "score": score,
            })
    df = pd.DataFrame(rows)
    csv_path = os.path.join(OUTPUT_DIR, "score_matrix.csv")
    df.to_csv(csv_path, index=False)
    log(f"Wrote {len(df)} rows to {csv_path}")

    # Top-1 accuracy: does the highest-scoring JD for each resume belong to its own category?
    summary_lines = []
    correct = 0
    per_category = {}
    for r in resumes:
        expected_prefix = CATEGORY_TO_JD_PREFIX[r["category"]]
        sub = df[df["resume_key"] == r["key"]].sort_values("score", ascending=False)
        top = sub.iloc[0]
        is_correct = top["jd_category"] == expected_prefix
        correct += int(is_correct)
        per_category.setdefault(r["category"], {"correct": 0, "total": 0})
        per_category[r["category"]]["total"] += 1
        per_category[r["category"]]["correct"] += int(is_correct)
        summary_lines.append(
            f"{r['key']:55s} top_jd={top['jd_key']:25s} score={top['score']:3d}  expected_prefix={expected_prefix:12s} {'OK' if is_correct else 'MISMATCH'}"
        )

    accuracy = correct / len(resumes) * 100
    summary_path = os.path.join(OUTPUT_DIR, "accuracy_summary.txt")
    with open(summary_path, "w") as f:
        f.write(f"Overall top-1 category accuracy: {correct}/{len(resumes)} ({accuracy:.1f}%)\n\n")
        f.write("Per-category accuracy:\n")
        for cat, stats in sorted(per_category.items()):
            f.write(f"  {cat:35s} {stats['correct']}/{stats['total']}\n")
        f.write("\nPer-resume detail:\n")
        f.write("\n".join(summary_lines))
    log(f"Overall top-1 accuracy: {correct}/{len(resumes)} ({accuracy:.1f}%) -> {summary_path}")

    # Generate a handful of sample "Generate Report" outputs for manual review
    log("Generating sample reports...")
    llm = ChatGroq(temperature=0.0, model=GROQ_MODEL_NAME, groq_api_key=GROQ_API_KEY)

    def generate_response(prompt_input, max_retries=6):
        messages = [SystemMessage(content=TEMPLATE_CONTENT), HumanMessage(content=prompt_input)]
        for attempt in range(max_retries):
            try:
                return llm.invoke(messages).content
            except Exception as e:
                if "429" in str(e) or "413" in str(e) or "rate_limit" in str(e).lower():
                    wait = min(30, 3 * (attempt + 1))
                    log(f"    rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError("Exceeded max retries due to rate limiting")

    sample_pairs = []
    # one real, one synthetic, matched with their best JD
    for source in ["real", "synthetic"]:
        candidates = [r for r in resumes if r["source"] == source]
        if candidates:
            r = candidates[0]
            sub = df[df["resume_key"] == r["key"]].sort_values("score", ascending=False)
            best_jd_key = sub.iloc[0]["jd_key"]
            jd = next(j for j in jds if j["key"] == best_jd_key)
            sample_pairs.append(("best_match", r, jd))
    # one deliberately mismatched pair for contrast
    r0 = resumes[0]
    wrong_category_jds = [j for j in jds if j["category"] != CATEGORY_TO_JD_PREFIX[r0["category"]]]
    if wrong_category_jds:
        sample_pairs.append(("mismatch", r0, wrong_category_jds[0]))

    for label, r, jd in sample_pairs:
        log(f"  generating report for {label}: {r['key']} vs {jd['key']}")
        resume_content, job_description_content = r["text"], jd["text"]
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
        report_lines = [f"RESUME: {r['key']}  |  JD: {jd['key']}\n"]
        for title, prompt in sections.items():
            report_lines.append(f"--- {title} ---\n{generate_response(prompt)}\n")
        report_path = os.path.join(OUTPUT_DIR, "sample_reports", f"{label}_{r['key']}_vs_{jd['key']}.txt")
        with open(report_path, "w") as f:
            f.write("\n".join(report_lines))
        log(f"  wrote {report_path}")

    log("Done.")


if __name__ == "__main__":
    main()
