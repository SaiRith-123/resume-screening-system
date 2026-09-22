# Synthetic Resume Dataset

This directory contains 150 fictional, machine-generated resume records for
testing the supervised training pipeline. It contains 10 role labels with 15
examples per role and no real people's personal data.

## Files

- `synthetic_resumes.jsonl`: one readable JSON record per fictional person.
- `training_metrics.json`: held-out evaluation metrics.

The trained artifact is generated outside this directory at
`backend/artifacts/synthetic_resume_role_classifier.joblib`.

## Reproduce

```powershell
backend\.venv\Scripts\python.exe backend\scripts\generate_synthetic_resume_dataset.py
backend\.venv\Scripts\python.exe backend\scripts\train_resume_classifier.py `
  --input-jsonl sample_data\synthetic_resume_dataset\synthetic_resumes.jsonl `
  --artifact backend\artifacts\synthetic_resume_role_classifier.joblib `
  --output-dir sample_data\synthetic_resume_dataset
```

This dataset is for development and pipeline tests only. Its templated text
does not represent real resume diversity or hiring performance.