"""Scoring weights (spec §10)."""
from __future__ import annotations

DEFAULT_WEIGHTS: dict[str, float] = {
    "skill": 0.35,
    "experience": 0.20,
    "semantic": 0.15,
    "education": 0.10,
    "project": 0.10,
    "certification": 0.05,
    "preferred": 0.05,
}

COMPONENT_KEYS = list(DEFAULT_WEIGHTS.keys())


def normalize_weights(weights: dict[str, float] | None) -> dict[str, float]:
    """Return a weights dict that sums to 1.0, filling missing keys."""
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        for k, v in weights.items():
            if k in w and v is not None:
                w[k] = max(0.0, float(v))
    total = sum(w.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: round(v / total, 6) for k, v in w.items()}
