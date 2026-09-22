"""Unit tests: real embedding path and explicit degraded hash backend."""
import numpy as np

from app.services.embedding_service.embedder import Embedder


def test_embedder_shape_and_determinism():
    emb = Embedder(dim=64)
    v1 = emb.encode(["python fastapi backend"])
    v2 = emb.encode(["python fastapi backend"])
    assert v1.shape == (1, 64)
    assert np.allclose(v1, v2)


def test_similarity_is_bounded():
    emb = Embedder(dim=64)
    vecs = emb.encode(["machine learning python", "completely different marketing content"])
    sim = emb.similarity(vecs[0], vecs[1])
    assert -1.0 <= sim <= 1.0


def test_identical_text_similarity_is_high():
    emb = Embedder(dim=128)
    vecs = emb.encode(["pytorch deep learning models", "pytorch deep learning models"])
    assert emb.similarity(vecs[0], vecs[1]) > 0.99


def test_hash_encoder_normalized():
    emb = Embedder(dim=32)
    v = emb.encode([""])  # empty text should not crash
    assert v.shape == (1, 32)


def test_default_embedder_uses_real_model():
    emb = Embedder(cache_dir=".pytest_cache/embeddings")
    vectors = emb.encode(["machine learning with Python"])
    assert emb.backend == "transformers"
    assert emb.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert vectors.shape == (1, 384)
    assert not np.allclose(vectors, Embedder(dim=384).encode(["machine learning with Python"]))


def test_real_embeddings_are_cached_on_disk(tmp_path):
    text = "cache this real embedding"
    first = Embedder(cache_dir=str(tmp_path)).encode([text])
    cached_files = list(tmp_path.glob("*.npy"))
    second = Embedder(cache_dir=str(tmp_path)).encode([text])
    assert cached_files
    assert np.allclose(first, second)
