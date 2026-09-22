from app.services.nlp_features import extract_skill_entities, tfidf_cosine_similarity


def test_tfidf_similarity_distinguishes_related_documents():
    related = tfidf_cosine_similarity(
        "Python FastAPI backend services", "Backend APIs built with Python and FastAPI"
    )
    unrelated = tfidf_cosine_similarity("Python FastAPI backend services", "Organic gardening tips")
    assert related > unrelated
    assert 0.0 <= related <= 1.0


def test_skill_entities_normalize_known_aliases():
    entities = extract_skill_entities("Built REST APIs with Python and ReactJS")
    assert "Python" in entities
    assert "React" in entities