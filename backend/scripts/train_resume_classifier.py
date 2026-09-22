"""Build training data from the imported resumes and train a role classifier.

The Kaggle corpus has no annotation file. Labels are therefore weak labels
inferred from role phrases in filenames and extracted resume text. Every
record stores its label source and confidence so the dataset can be reviewed
before using the classifier for decisions.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.resume_parser.extractor import extract


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "sample_data" / "kaggle_resume_dataset" / "Resumes"
DEFAULT_OUTPUT = PROJECT_ROOT / "sample_data" / "kaggle_resume_dataset" / "processed"
DEFAULT_ARTIFACT = PROJECT_ROOT / "backend" / "artifacts" / "resume_role_classifier.joblib"

ROLE_PATTERNS: dict[str, tuple[str, ...]] = {
    "business_analyst": ("business analyst", "business analysis", "business analyst"),
    "project_manager": ("project manager", "project management", "pmp"),
    "program_manager": ("program manager", "program management"),
    "scrum_master": ("scrum master", "scrum", "agile coach"),
    "java_developer": ("java developer", "java engineer", "spring boot", "j2ee"),
    "full_stack_developer": ("full stack", "full-stack", "fullstack"),
    "hadoop_developer": ("hadoop", "big data", "hive", "spark developer"),
    "devops_engineer": ("devops", "dev ops", "site reliability", "sre"),
    "healthcare": ("healthcare", "health care", "clinical", "medical"),
}


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower().replace("_", " ")).strip()


def infer_label(filename: str, text: str) -> tuple[str | None, str, float]:
    """Return (label, source, confidence), or an unlabeled result."""
    filename_text = _normalize(Path(filename).stem)
    resume_text = _normalize(text)
    scores: Counter[str] = Counter()
    filename_hits: Counter[str] = Counter()
    text_hits: Counter[str] = Counter()

    for label, phrases in ROLE_PATTERNS.items():
        for phrase in phrases:
            normalized_phrase = _normalize(phrase)
            if normalized_phrase in filename_text:
                filename_hits[label] += 1
                scores[label] += 4
            if normalized_phrase in resume_text:
                text_hits[label] += 1
                scores[label] += 1

    if not scores:
        return None, "unlabeled", 0.0
    ranked = scores.most_common()
    best_label, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    if best_score < 2 or best_score == second_score:
        return None, "ambiguous", 0.0

    if filename_hits[best_label]:
        source = "filename+text" if text_hits[best_label] else "filename"
        confidence = min(1.0, 0.75 + 0.05 * min(filename_hits[best_label] + text_hits[best_label], 5))
    else:
        source = "text"
        confidence = min(0.7, 0.45 + 0.05 * min(text_hits[best_label], 5))
    return best_label, source, round(confidence, 2)


def build_manifest(input_dir: Path, output_path: Path) -> tuple[list[dict], Counter[str]]:
    records: list[dict] = []
    skipped: Counter[str] = Counter()
    for path in sorted(input_dir.glob("*.docx")):
        result = extract(str(path), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        if not result.ok:
            skipped[result.error or "extraction_failed"] += 1
            continue
        label, label_source, confidence = infer_label(path.name, result.text)
        record = {
            "source_file": path.name,
            "label": label,
            "label_source": label_source,
            "label_confidence": confidence,
            "text": result.text,
            "extraction_method": result.method,
        }
        records.append(record)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return records, skipped


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def train(records: list[dict], artifact_path: Path, metrics_path: Path) -> dict:
    labeled = [record for record in records if record["label"]]
    label_counts = Counter(record["label"] for record in labeled)
    eligible_labels = {label for label, count in label_counts.items() if count >= 2}
    labeled = [record for record in labeled if record["label"] in eligible_labels]
    if len(labeled) < 10 or len(eligible_labels) < 2:
        raise RuntimeError("Not enough weakly labeled resumes to train a classifier")

    texts = [record["text"] for record in labeled]
    labels = [record["label"] for record in labeled]
    test_size = max(len(eligible_labels), round(len(labeled) * 0.2))
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts, labels, test_size=test_size, random_state=42, stratify=labels
    )
    model = Pipeline([
        ("tfidf", TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2), min_df=2, max_features=60000)),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])
    model.fit(train_texts, train_labels)
    predictions = model.predict(test_texts)
    report = classification_report(test_labels, predictions, output_dict=True, zero_division=0)
    metrics = {
        "training_records": len(train_texts),
        "test_records": len(test_texts),
        "eligible_labels": sorted(eligible_labels),
        "label_counts": dict(sorted(label_counts.items())),
        "classification_report": report,
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, artifact_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--input-jsonl", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    args = parser.parse_args()

    manifest_path = args.output_dir / "resume_training_manifest.jsonl"
    metrics_path = args.output_dir / "training_metrics.json"
    if args.input_jsonl:
        records = load_jsonl(args.input_jsonl)
        skipped = Counter()
        manifest_path = args.input_jsonl
    else:
        records, skipped = build_manifest(args.input_dir, manifest_path)
    metrics = train(records, args.artifact, metrics_path)
    labeled = sum(record["label"] is not None for record in records)
    print(f"Manifest: {manifest_path}")
    print(f"Records: {len(records)}; labeled: {labeled}; skipped: {dict(skipped)}")
    print(f"Artifact: {args.artifact}")
    print(f"Metrics: {metrics_path}")
    print(f"Macro F1: {metrics['classification_report']['macro avg']['f1-score']:.3f}")


if __name__ == "__main__":
    main()