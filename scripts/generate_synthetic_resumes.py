"""
Generates a synthetic mirror of resume_data/ using Faker-generated fake people and
templated bullet points. No real personal data is used or read.

Usage:
    pip install faker fpdf2
    python scripts/generate_synthetic_resumes.py

Output goes to resume_data_synthetic/, mirroring resume_data/'s folder names and
resume-N.pdf numbering exactly, so it can be used as a drop-in replacement in tests.
"""
import os
import random

from faker import Faker
from fpdf import FPDF
from fpdf.enums import XPos, YPos

OUTPUT_ROOT = os.path.join(os.path.dirname(__file__), "..", "resume_data_synthetic")

# category -> (resume numbers matching the real resume_data/ layout, role config)
CATEGORIES = {
    "Big Data Analyst": {
        "numbers": [1, 2, 3],
        "titles": ["Big Data Analyst", "Senior Big Data Analyst", "Big Data Analyst II"],
        "skills": ["Hadoop", "Spark", "Hive", "Kafka", "SQL", "Python", "Scala",
                   "Tableau", "Power BI", "AWS EMR", "Airflow", "HBase"],
        "bullets": [
            "Analyzed {n}TB+ of clickstream data using Spark and Hive to identify user engagement trends",
            "Built {n} automated Hadoop pipelines reducing manual reporting effort by {pct}%",
            "Partnered with product teams to deliver {n} dashboards driving a {pct}% lift in retention",
            "Optimized Hive queries, cutting average query runtime by {pct}%",
            "Migrated legacy batch jobs to Spark, processing {n}M records daily",
        ],
    },
    "Business Intelligence Analyst": {
        "numbers": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
        "titles": ["Business Intelligence Analyst", "BI Analyst", "Senior BI Analyst"],
        "skills": ["SQL", "Power BI", "Tableau", "DAX", "Excel", "SSRS", "Snowflake",
                   "Looker", "Python", "Data Modeling", "ETL"],
        "bullets": [
            "Designed {n} executive dashboards in Power BI used by {pct} senior stakeholders weekly",
            "Automated recurring reports, saving the analytics team {n} hours per week",
            "Built a star-schema data model supporting {n} concurrent BI workloads",
            "Identified revenue opportunities worth ${n}K through ad-hoc SQL analysis",
            "Improved report load times by {pct}% through DAX and query optimization",
        ],
    },
    "Data Analyst": {
        "numbers": list(range(14, 29)),
        "titles": ["Data Analyst", "Senior Data Analyst", "Data Analyst II"],
        "skills": ["SQL", "Excel", "Python", "Pandas", "Tableau", "Power BI",
                   "A/B Testing", "Statistics", "R", "Looker"],
        "bullets": [
            "Performed exploratory analysis on {n}+ datasets to support product decisions",
            "Built {n} automated SQL reports, reducing manual work by {pct}%",
            "Ran A/B tests informing a {pct}% improvement in conversion rate",
            "Created interactive Tableau dashboards adopted by {n} teams",
            "Cleaned and validated {n}M+ rows of transactional data for downstream analytics",
        ],
    },
    "Data Architect": {
        "numbers": list(range(29, 40)),
        "titles": ["Data Architect", "Senior Data Architect", "Enterprise Data Architect"],
        "skills": ["Data Modeling", "AWS", "Azure", "Snowflake", "ER/Studio",
                   "Data Governance", "SQL", "Kafka", "Master Data Management", "Redshift"],
        "bullets": [
            "Designed enterprise data warehouse architecture supporting {n}TB of data",
            "Led migration of {n} legacy systems to a cloud-native data platform",
            "Established data governance standards adopted across {n} business units",
            "Reduced storage costs by {pct}% through data lifecycle and partitioning strategy",
            "Defined ER models and DDL standards used by {n} engineering teams",
        ],
    },
    "Data Engineer": {
        "numbers": list(range(40, 54)),
        "titles": ["Data Engineer", "Senior Data Engineer", "Data Engineer II"],
        "skills": ["Python", "SQL", "Airflow", "Spark", "Kafka", "AWS", "dbt",
                   "Snowflake", "Docker", "Kubernetes", "ETL/ELT"],
        "bullets": [
            "Built and maintained {n} ETL pipelines processing {pct}TB of data daily",
            "Reduced pipeline failure rate by {pct}% through improved monitoring and retries",
            "Migrated batch jobs to Airflow, cutting orchestration overhead by {pct}%",
            "Designed a streaming pipeline with Kafka handling {n}K events/sec",
            "Optimized warehouse schema, reducing query costs by {pct}%",
        ],
    },
    "Data Scientist": {
        "numbers": list(range(54, 73)),
        "titles": ["Data Scientist", "Senior Data Scientist", "Data Scientist II"],
        "skills": ["Python", "scikit-learn", "TensorFlow", "SQL", "Statistics",
                   "A/B Testing", "NLP", "Pandas", "XGBoost", "PyTorch"],
        "bullets": [
            "Developed a machine learning model improving prediction accuracy by {pct}%",
            "Built a churn model saving an estimated ${n}K in annual revenue",
            "Led {n} A/B tests to validate model impact before production rollout",
            "Deployed {n} ML models into production serving real-time predictions",
            "Automated feature engineering pipeline, cutting model iteration time by {pct}%",
        ],
    },
    "Machine Learning Engineer": {
        "numbers": list(range(73, 84)),
        "titles": ["Machine Learning Engineer", "Senior ML Engineer", "ML Engineer II"],
        "skills": ["Python", "PyTorch", "TensorFlow", "MLflow", "Docker", "Kubernetes",
                   "AWS SageMaker", "CI/CD", "Feature Stores", "gRPC"],
        "bullets": [
            "Productionized {n} ML models serving {pct}K+ requests per day",
            "Built a feature store reducing feature engineering duplication by {pct}%",
            "Reduced model inference latency by {pct}% through quantization and batching",
            "Implemented CI/CD pipelines for {n} ML services with automated retraining",
            "Collaborated with data science to scale {n} models from prototype to production",
        ],
    },
    "MLOps Engineer": {
        "numbers": [84, 85, 86, 87, 88],
        "titles": ["MLOps Engineer", "Senior MLOps Engineer", "Platform Engineer, ML"],
        "skills": ["Kubernetes", "Docker", "Terraform", "MLflow", "AWS", "CI/CD",
                   "Prometheus", "Airflow", "Python", "Kubeflow"],
        "bullets": [
            "Built ML platform infrastructure supporting {n} production models",
            "Automated model deployment pipelines, cutting release time by {pct}%",
            "Implemented monitoring and alerting reducing model incident response time by {pct}%",
            "Managed Kubernetes clusters running {n} ML training and inference workloads",
            "Standardized CI/CD for ML across {n} teams using Terraform and GitHub Actions",
        ],
    },
}

DEGREES = ["B.S. in Computer Science", "B.S. in Statistics", "M.S. in Data Science",
           "M.S. in Computer Science", "B.S. in Mathematics", "M.S. in Analytics"]


def render_bullet(template, rng):
    return template.format(n=rng.randint(2, 40), pct=rng.randint(10, 65))


def build_resume_text(fake, rng, role_config):
    title = rng.choice(role_config["titles"])
    skills = rng.sample(role_config["skills"], k=min(6, len(role_config["skills"])))
    bullets_job1 = rng.sample(role_config["bullets"], k=3)
    bullets_job2 = rng.sample(role_config["bullets"], k=2)

    name = fake.name()
    city, state = fake.city(), fake.state_abbr()
    email = fake.safe_email()
    phone = fake.phone_number()

    company1, company2 = fake.company(), fake.company()
    years_total = rng.randint(3, 12)
    end_year = rng.randint(2022, 2025)
    mid_year = end_year - rng.randint(1, 3)
    start_year = mid_year - rng.randint(1, 4)

    degree = rng.choice(DEGREES)
    university = fake.city() + " University"

    lines = [
        f"{name}",
        f"{title} | {city}, {state} | {email} | {phone}",
        "",
        f"Summary",
        f"{title} with {years_total}+ years of experience across {', '.join(skills[:3])}, "
        f"delivering measurable business impact through data-driven solutions.",
        "",
        "Employment History",
        f"{title}",
        f"{company1}, {city}, {state} | {mid_year} - Present",
    ]
    lines += [f"- {render_bullet(b, rng)}" for b in bullets_job1]
    lines += [
        "",
        rng.choice(role_config["titles"]),
        f"{company2}, {fake.city()}, {fake.state_abbr()} | {start_year} - {mid_year}",
    ]
    lines += [f"- {render_bullet(b, rng)}" for b in bullets_job2]
    lines += [
        "",
        "Education",
        f"{degree}, {university}, {start_year - rng.randint(1, 3)}",
        "",
        "Skills",
        ", ".join(skills),
    ]
    return "\n".join(lines)


def write_pdf(text, path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    for line in text.split("\n"):
        if line:
            pdf.multi_cell(0, 6, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            pdf.ln(6)
    pdf.output(path)


def main():
    fake = Faker()
    for category, config in CATEGORIES.items():
        out_dir = os.path.join(OUTPUT_ROOT, category)
        os.makedirs(out_dir, exist_ok=True)
        for number in config["numbers"]:
            Faker.seed(number)
            rng = random.Random(number)
            resume_text = build_resume_text(fake, rng, config)
            out_path = os.path.join(out_dir, f"resume-{number}.pdf")
            write_pdf(resume_text, out_path)
            print(f"Generated {out_path}")


if __name__ == "__main__":
    main()
