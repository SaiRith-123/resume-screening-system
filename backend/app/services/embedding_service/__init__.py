"""Embedding service package."""
from app.services.embedding_service.embedder import Embedder, get_embedder

__all__ = ["Embedder", "get_embedder"]
