"""Semantic embedding service (spec §8C). sentence-transformers all-MiniLM-L6-v2."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class Embedder:
    """Encode text with a real model by default, with explicit hash degradation."""

    _models: dict[str, object] = {}

    def __init__(self, model_name: str | None = None, dim: int | None = None,
                 backend: str | None = None, cache_dir: str | None = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.dim = dim or settings.EMBEDDING_DIM
        self.backend = backend or ("hash" if dim is not None else settings.EMBEDDING_BACKEND)
        if self.backend not in {"transformers", "hash"}:
            raise ValueError("EMBEDDING_BACKEND must be 'transformers' or 'hash'")
        if self.backend == "hash" and dim is None:
            logger.warning("Using degraded hash embeddings; set EMBEDDING_BACKEND=transformers")
        self.cache_dir = Path(cache_dir or settings.EMBEDDING_CACHE_DIR)

    def _load(self):
        if self.backend == "hash":
            return None
        if self.model_name not in Embedder._models:
            try:
                from sentence_transformers import SentenceTransformer
                Embedder._models[self.model_name] = SentenceTransformer(self.model_name)
            except Exception as exc:  # pragma: no cover
                raise RuntimeError(
                    f"Real embedding model '{self.model_name}' could not be loaded; "
                    "set EMBEDDING_BACKEND=hash only for explicit degraded operation"
                ) from exc
        return Embedder._models[self.model_name]

    # -- public API ---------------------------------------------------------
    def encode(self, texts: list[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)
        vectors: list[np.ndarray | None] = [self._read_cache(text) for text in texts]
        missing = [i for i, vector in enumerate(vectors) if vector is None]
        if missing:
            model = self._load()
            if model is None:
                computed = [self._hash_encode(texts[i]) for i in missing]
            else:
                computed = np.asarray(
                    model.encode([texts[i] for i in missing], normalize_embeddings=True,
                                 show_progress_bar=False),
                    dtype=np.float32,
                )
            for index, vector in zip(missing, computed):
                vectors[index] = np.asarray(vector, dtype=np.float32)
                self._write_cache(texts[index], vectors[index])
        return np.vstack([vector for vector in vectors if vector is not None])

    def _cache_path(self, text: str) -> Path:
        key = hashlib.sha256(f"{self.backend}\0{self.model_name}\0{text}".encode()).hexdigest()
        return self.cache_dir / f"{key}.npy"

    def _read_cache(self, text: str) -> np.ndarray | None:
        path = self._cache_path(text)
        try:
            vector = np.load(path, allow_pickle=False)
            return np.asarray(vector, dtype=np.float32)
        except (FileNotFoundError, OSError, ValueError):
            return None

    def _write_cache(self, text: str, vector: np.ndarray) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._cache_path(text)
        temporary = path.with_suffix(".tmp.npy")
        np.save(temporary, vector)
        temporary.replace(path)

    @staticmethod
    def similarity(a: np.ndarray, b: np.ndarray) -> float:
        a = np.asarray(a, dtype=np.float32).ravel()
        b = np.asarray(b, dtype=np.float32).ravel()
        denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-9
        return float(np.dot(a, b) / denom)

    def hashing_dim(self) -> int:
        return self.dim

    # -- deterministic fallback --------------------------------------------
    def _hash_encode(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = (text or "").lower().split()
        if not tokens:
            return vec
        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 3) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = math.sqrt(float(np.dot(vec, vec))) or 1.0
        return vec / norm


_default_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    """Process-wide singleton embedder (avoids reloading the model per request)."""
    global _default_embedder
    if _default_embedder is None:
        _default_embedder = Embedder()
    return _default_embedder
