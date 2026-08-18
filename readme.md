# Resume JD Scorer

Resume JD Scorer analyzes resumes against job descriptions using Google Gemini embeddings for match scoring and Groq for chat/report generation. It pairs an embedding-based match-scoring pipeline (with a batch scorer for local datasets) with a Streamlit web app that gives a live match score plus AI-generated, chat-based resume suggestions and a downloadable PDF report.

## Quick Start

For anyone who just wants the commands - see the Detailed Setup Guide below for explanations, verification steps, and troubleshooting.

```bash
# 1. Clone and configure environment
git clone https://github.com/enescaglarr/Resume-Job-Description-Scorer.git
cd Resume-Job-Description-Scorer
cp .env.example .env
# open .env and fill in GOOGLE_API_KEY (aistudio.google.com) and GROQ_API_KEY (console.groq.com) - both free

# 2. Install Poppler + Tesseract (needed for scanned/image-based PDF resumes)
brew install poppler tesseract   # macOS - see the Detailed Setup Guide for Windows

# 3. Run
./run.sh
```

Open the URL Streamlit prints (usually `http://localhost:8501`). `run.sh` creates the virtual environment and installs `requirements.txt` automatically on first run.

## Detailed Setup Guide

### 1. Install prerequisites

You need Python 3, Poppler, and Tesseract.

| Tool | Check if installed | Install if missing |
|---|---|---|
| Python 3 | `python3 --version` | [python.org/downloads](https://python.org/downloads) (developed against 3.10, tested working through 3.13) |
| Poppler | `pdftoppm -v` | macOS: `brew install poppler` · Windows: [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases/) |
| Tesseract | `tesseract --version` | macOS: `brew install tesseract` · Windows: [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki) |

Poppler and Tesseract are only used as a fallback: most resumes are text-based PDFs read directly, but scanned/image-only resumes are run through this OCR pipeline (`pdf2image` → deskew → `pytesseract`).

On Windows, after installing Poppler/Tesseract you need to add their `bin` folders to your system `PATH` (Environment Variables → System variables → `Path` → New), or point to them directly in code - see Troubleshooting below.

### 2. Clone the repo and set up the environment

```bash
git clone <this-repo-url>
cd ResumeJDScorer
```

The easiest path is `./run.sh` (see Quick Start) - it creates `.venv`, installs `requirements.txt`, and launches the app in one command, every time.

If you'd rather set it up manually:

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

This installs Streamlit, LangChain, the Gemini and Groq SDKs, pandas, scikit-learn, fpdf2, and the PDF/OCR stack into the virtual environment only - your system Python is untouched.

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

| Variable | What it is | Required? |
|---|---|---|
| `GOOGLE_API_KEY` | Gemini API key (used for match-score embeddings) - get a free one at [aistudio.google.com](https://aistudio.google.com) | Yes |
| `GROQ_API_KEY` | Groq API key (used for chat and report generation) - get a free one at [console.groq.com](https://console.groq.com) | Yes |

`.env` is gitignored - your real key never gets committed. `.env.example` (with a placeholder value) is the template that ships in the repo.

### 4. Run the application

```bash
./run.sh
```

You should see:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open that URL in your browser. To stop the server, press `Ctrl+C` in that terminal.

**Troubleshooting:**

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError` even after `pip install -r requirements.txt` | Both conda's `base` env and `.venv` are active, so `streamlit`/`python` resolve to the wrong install | Run `conda deactivate` before `source .venv/bin/activate`, or just use `./run.sh` which always activates the project's own `.venv` |
| `ModuleNotFoundError: No module named 'langchain.chains'` | This app's chat chain needs `langchain<1.0` / `langchain-core<1.0` | Make sure those pins in `requirements.txt` are intact and reinstall |
| `404 ... is not found for API version v1beta` from a Gemini call | The model name in `src/constants.py` (`EMBEDDING_MODEL_NAME`) has been deprecated by Google | Check available models for your key and update the constant |
| `model_not_found` / `does not exist or you do not have access to it` from a Groq call | The model name in `src/constants.py` (`GROQ_MODEL_NAME`) has been deprecated/renamed by Groq | List current models for your key (`Groq(api_key=...).models.list()`) and update the constant |
| `429` / `rate_limit_exceeded` (tokens per minute) from a Groq call | Free-tier Groq accounts have a low TPM cap per model | The app already retries with backoff; if it persists, wait a minute or switch `GROQ_MODEL_NAME` to a model with a higher free-tier TPM limit |
| Resume PDF fails to parse / OCR errors | Poppler or Tesseract not installed or not on `PATH` | Reinstall per the table above, or set the path manually (see below) |
| `KeyError` / empty API key at startup | `.env` is missing or incomplete | Make sure you ran `cp .env.example .env` and filled in both `GOOGLE_API_KEY` and `GROQ_API_KEY` |

**Manually pointing to Poppler/Tesseract (Windows):** if they're installed but not detected, set the paths directly in code:

```python
# Tesseract
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Poppler
from pdf2image import convert_from_path
images = convert_from_path('your_pdf_file.pdf', poppler_path=r'C:\path\to\poppler\bin')
```

On Mac, this step is usually unnecessary when both are installed via Homebrew.

## Description of Files and Folders

`src/`:
- `resume_suggestions.py` - the Streamlit web app: upload a resume + JD (or paste the JD text directly), click "Calculate Match Score" to see a live embedding-similarity score, chat (Groq) for tailored suggestions, or generate a full multi-section report with a "Download Report as PDF" button.
- `resume_scorer.py` - batch-scores every resume in `resume_data/` (or `resume_data_synthetic/`) against every JD in `jd_data/` using cached embeddings, and prints the best-matching JD per resume.
- `embedding_model.py` - wraps Gemini embeddings (`GoogleGenerativeAIEmbeddings`), including saving/loading a `.pkl` cache.
- `directory_reader.py` - reads JD `.txt` files and resume `.pdf` files; falls back to OCR (deskew + Tesseract) for scanned/image-only PDFs.
- `constants.py` - central config: paths, model names, prompt templates. Loads `GOOGLE_API_KEY` and `GROQ_API_KEY` from `.env`.

`jd_data/`: 32 real, publicly posted job descriptions (`.txt`) used as the sample dataset.

`resume_data/`: real resumes (`.pdf`, one folder per job category) - contains PII (names, emails, phone numbers), so it's **gitignored and never pushed**.

`resume_data_synthetic/`: a drop-in synthetic mirror of `resume_data/` - same folders and `resume-N.pdf` numbering, but every resume is entirely Faker-generated (fake name/contact/company/history). Safe to share and to use as sample data.

`scripts/generate_synthetic_resumes.py`: regenerates `resume_data_synthetic/` deterministically. Run with `pip install -r requirements-dev.txt` first (needs `faker` + `fpdf2`, dev-only deps not required to run the app).

`output/`: cached JD/resume embedding `.pkl` files produced by `resume_scorer.py` (gitignored - regenerated on demand).

`Resume_Scorer.ipynb` / `Resume_Suggestions.ipynb`: exploratory notebook versions of the scoring pipeline and the chat app.

`run.sh`: one-command launcher - creates/activates `.venv`, installs dependencies on first run, and starts the Streamlit app.

`requirements.txt`: dependencies to run the app. `requirements-dev.txt`: extra dependencies (`faker`, `fpdf2`) only needed to regenerate synthetic resumes.

`.env.example`: template for `.env` (`GOOGLE_API_KEY` + `GROQ_API_KEY`). `.env` itself is gitignored and never committed.

`DEMO.md`: reproducible demo script - exact resume/JD file pairs, chat questions, and the actual results from a real run, for walking someone through the app's features live.

## Features

**Match Scoring**
- Cosine similarity between Gemini embeddings of a resume and a job description, shown live in the web app as a 0-100% score with a strong/moderate/weak label.
- Batch mode (`resume_scorer.py`) scores an entire local dataset at once and reports each resume's best-matching JD.

**AI Resume Suggestions**
- Chat interface (Groq) scoped to the uploaded resume + JD (and aware of the match score), for questions like "why isn't this 100%?" or "what's my biggest gap?" - guardrailed to refuse off-topic questions.
- Optional JD paste box in the sidebar as an alternative to uploading a `.txt` file - useful for pasting a JD copied straight from a job posting.
- One-click **Generate Report**: comparison analysis, resume analysis, JD analysis, gap analysis, actionable steps, experience enhancement, additional qualifications, resume tailoring, relevant-skills highlighting, formatting advice, and length advice - eleven sections in one pass, each a stateless per-section call (keeps individual requests small).
- **Download Report as PDF** button (sidebar) once a report has been generated.

**Synthetic Data Generation**
- `scripts/generate_synthetic_resumes.py` produces a fully fake, shareable resume dataset (same category/file structure as the real one) so the repo can be published without exposing real people's PII.

## Technical Details

**AI / ML**
- Embeddings: Gemini `gemini-embedding-001` via `langchain-google-genai`.
- Chat: Groq `openai/gpt-oss-20b` via `langchain-groq`'s `ChatGroq`, orchestrated with LangChain's `ConversationChain` + `ConversationBufferWindowMemory` for the live chat (requires `langchain<1.0`). Report sections use stateless direct calls (not the shared chain) so per-section token usage doesn't grow with each section.
- Scoring: `scikit-learn`'s `cosine_similarity` over embedding vectors.

**PDF**
- Input: text-based resume PDFs extracted directly with `pypdf`; scanned/image PDFs via `pdf2image` → OpenCV deskew → `pytesseract` OCR.
- Output: the generated report can be exported as a PDF (`fpdf2`) via the sidebar download button.

**Web app**
- Streamlit for the UI, file upload, and chat.

## Example Usage

**Scoring a resume against a job description (web app):**
1. Upload a resume (`.pdf`) and a job description (`.txt`, or paste the text directly) in the sidebar.
2. Click **Calculate Match Score** to see the embedding-similarity score.
3. Ask the chat follow-up questions, or click **Generate Report** for the full multi-section breakdown (downloadable as PDF afterward).

See `DEMO.md` for exact reproducible resume/JD pairs and example chat questions/answers.

**Scoring a local dataset in bulk:**
```bash
cd src
python resume_scorer.py
```
Reads every JD in `jd_data/` and every resume in `resume_data_synthetic/` (the default `RESUME_PATH` in `constants.py` - point it at `../resume_data/*/*` instead if you have the real, gitignored dataset locally), embeds them, and prints each resume's best-matching JD with a percentage score.

**Regenerating the synthetic resume set:**
```bash
pip install -r requirements-dev.txt
python scripts/generate_synthetic_resumes.py
```
