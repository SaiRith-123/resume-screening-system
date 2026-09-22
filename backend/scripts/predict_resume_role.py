"""Predict a role label from plain resume text using a trained artifact."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import joblib


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("text_file", type=Path)
    parser.add_argument("--artifact", type=Path, required=True)
    args = parser.parse_args()
    model = joblib.load(args.artifact)
    text = args.text_file.read_text(encoding="utf-8")
    prediction = model.predict([text])[0]
    probabilities = model.predict_proba([text])[0]
    classes = model.classes_
    ranked = sorted(zip(classes, probabilities), key=lambda item: item[1], reverse=True)
    print(f"predicted_role={prediction}")
    print("ranked_roles=" + ", ".join(f"{label}:{score:.3f}" for label, score in ranked))


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()