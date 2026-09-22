# Kaggle Resume Dataset

This directory contains the 228 DOCX resumes downloaded from
`palaksood97/resume-dataset` with `kagglehub` on 2026-09-22. The files are
kept separate from the curated fixtures in `sample_data/resumes`.

These resumes can be uploaded through the normal resume-upload workflow for
parser, extraction, matching, and screening evaluation. They are not imported
automatically into a user's account or database.

The download contains resume documents but no reviewed job matches, screening
decisions, or target labels. It therefore cannot validly train a supervised
ranking/classification model by itself. The production model remains the
explainable deterministic parser, matcher, and scorer documented in
`ml_pipeline.md`.

Review the dataset's Kaggle terms and license before redistributing these files
or deploying them. Resume documents may contain personal data; do not expose
them publicly or use them in production without an appropriate lawful basis.

## Build training data and train

From the repository root, run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\train_resume_classifier.py
```

The command extracts the DOCX files and writes a readable JSONL manifest to
`processed/resume_training_manifest.jsonl`. Each line contains the source file,
extracted text, inferred label, label source, and confidence. Unlabeled or
ambiguous records remain in the manifest but are excluded from training.

The trained auxiliary role classifier is saved locally at
`backend/artifacts/resume_role_classifier.joblib`, with held-out metrics in
`processed/training_metrics.json`. The artifact directory is ignored by Git;
rerun the command to reproduce it on another machine.