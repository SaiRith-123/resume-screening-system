"""Lightweight, deterministic NLP features used by resume screening."""
from __future__ import annotations

import re

from app.services.skill_matcher.taxonomy import ALIAS_TO_CANONICAL


def tfidf_cosine_similarity(left: str, right: str) -> float:
    """Return lexical TF-IDF cosine similarity for two text documents."""
    if not (left or "").strip() or not (right or "").strip():
        return 0.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform(
            [left, right]
        )
        return float(max(0.0, min(1.0, cosine_similarity(matrix[0:1], matrix[1:2])[0, 0])))
    except (ImportError, ValueError):
        # Very short or unusual text should degrade gracefully when sklearn is unavailable.
        left_tokens = set(re.findall(r"[a-z0-9+#.]+", left.lower()))
        right_tokens = set(re.findall(r"[a-z0-9+#.]+", right.lower()))
        union = left_tokens | right_tokens
        return len(left_tokens & right_tokens) / len(union) if union else 0.0


def extract_skill_entities(text: str) -> list[str]:
    """Extract taxonomy skills with a spaCy EntityRuler when available.

    A regex fallback keeps extraction usable without downloading a spaCy model.
    Resume text is treated as data; only known taxonomy aliases are recognized.
    """
    source = text or ""
    if not source.strip():
        return []
    try:
        import spacy

        nlp = spacy.blank("en")
        ruler = nlp.add_pipe("entity_ruler")
        patterns = [
            {"label": "SKILL", "pattern": alias}
            for alias in sorted(ALIAS_TO_CANONICAL, key=len, reverse=True)
        ]
        ruler.add_patterns(patterns)
        entities = [ent.text for ent in nlp(source).ents if ent.label_ == "SKILL"]
    except (ImportError, ValueError, OSError):
        entities = []
    if not entities:
        entities = [
            alias for alias in ALIAS_TO_CANONICAL
            if re.search(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", source.lower())
        ]
    seen: set[str] = set()
    result: list[str] = []
    for entity in entities:
        canonical = ALIAS_TO_CANONICAL.get(entity.lower())
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result