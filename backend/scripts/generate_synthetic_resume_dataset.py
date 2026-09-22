"""Generate 150 fictional labeled resumes for pipeline development."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "sample_data" / "synthetic_resume_dataset" / "synthetic_resumes.jsonl"

FIRST_NAMES = [
    "Aarav", "Maya", "Noah", "Sofia", "Liam", "Zara", "Ethan", "Nia", "Lucas", "Aisha",
    "Milo", "Elena", "Kai", "Iris", "Owen",
]
LAST_NAMES = [
    "Sharma", "Patel", "Morgan", "Chen", "Williams", "Iyer", "Brown", "Garcia", "Singh", "Wilson",
]
EMPLOYERS = [
    "Northstar Labs", "Cedarline Systems", "Brightfield Digital", "Orbit Peak Solutions",
    "Maple Ridge Technologies", "Harborstone Analytics", "Bluehaven Services", "Summit Grove",
    "Redwood Works", "Silverleaf Health",
]
SCHOOLS = [
    "Riverview Institute of Technology", "Lakeside University", "Westbridge College",
    "Pinecrest University", "Easton School of Engineering",
]
CITIES = ["Austin, TX", "Denver, CO", "Atlanta, GA", "Raleigh, NC", "Portland, OR"]

ROLE_PROFILES = {
    "business_analyst": ("Business Analyst", ["requirements gathering", "SQL", "Power BI", "process mapping"]),
    "project_manager": ("Project Manager", ["project planning", "risk management", "PMP", "stakeholder management"]),
    "program_manager": ("Program Manager", ["portfolio management", "strategic planning", "OKRs", "executive reporting"]),
    "scrum_master": ("Scrum Master", ["Scrum", "Agile coaching", "Jira", "sprint planning"]),
    "java_developer": ("Java Developer", ["Java", "Spring Boot", "REST APIs", "PostgreSQL"]),
    "full_stack_developer": ("Full Stack Developer", ["React", "TypeScript", "Node.js", "PostgreSQL"]),
    "hadoop_developer": ("Hadoop Developer", ["Hadoop", "Spark", "Hive", "Python"]),
    "devops_engineer": ("DevOps Engineer", ["AWS", "Docker", "Kubernetes", "Terraform"]),
    "healthcare": ("Healthcare Data Analyst", ["healthcare analytics", "HIPAA", "SQL", "clinical reporting"]),
    "data_scientist": ("Data Scientist", ["Python", "scikit-learn", "pandas", "machine learning"]),
}


def build_records() -> list[dict]:
    records: list[dict] = []
    role_items = list(ROLE_PROFILES.items())
    for role_index, (label, (title, skills)) in enumerate(role_items):
        for person_index in range(15):
            first = FIRST_NAMES[person_index]
            last = LAST_NAMES[role_index]
            name = f"{first} {last}"
            years = 2 + (person_index % 7)
            start_year = 2025 - years
            end_year = start_year + years - 1
            employer = EMPLOYERS[(role_index + person_index) % len(EMPLOYERS)]
            school = SCHOOLS[(role_index * 2 + person_index) % len(SCHOOLS)]
            city = CITIES[(role_index + person_index) % len(CITIES)]
            project_name = [
                "Operations Insight Portal", "Workflow Modernization", "Customer Metrics Hub",
                "Platform Reliability Program", "Forecasting and Reporting Suite",
            ][person_index % 5]
            achievement = [
                "reduced reporting time by 28%",
                "improved release consistency across three teams",
                "automated a weekly process used by 40 colleagues",
                "cut recurring defects by 18%",
                "increased dashboard adoption by 35%",
            ][person_index % 5]
            records.append({
                "person_id": f"synthetic-{role_index + 1:02d}-{person_index + 1:02d}",
                "name": name,
                "email": f"synthetic.{role_index + 1:02d}.{person_index + 1:02d}@example.invalid",
                "label": label,
                "label_source": "synthetic_template",
                "label_confidence": 1.0,
                "text": (
                    f"{name}\n{title}\n"
                    f"{city} | synthetic.{role_index + 1:02d}.{person_index + 1:02d}@example.invalid\n"
                    f"Profile: {years} years of experience delivering {title.lower()} work across cross-functional teams.\n"
                    f"Experience\n{employer}, {title} | {start_year}-01 to {end_year}-12\n"
                    f"Delivered {project_name.lower()} initiatives and {achievement}.\n"
                    f"Skills\n{', '.join(skills)}, documentation, collaboration, testing\n"
                    f"Projects\n{project_name}: applied {skills[0]}, {skills[1]}, and {skills[2]} to improve delivery quality.\n"
                    f"Education\nBachelor of Science, {school} | {start_year - 4}-{start_year - 1}"
                ),
            })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    records = build_records()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    print(f"Generated {len(records)} fictional labeled resumes at {args.output}")


if __name__ == "__main__":
    main()