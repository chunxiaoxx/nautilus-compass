"""
Embedding Service

Provides text embedding functionality using sentence-transformers.
Uses the all-MiniLM-L6-v2 model for efficient 384-dimensional embeddings.
"""

import asyncio
from typing import List, Union
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the embedding service.

        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self._model = None
        logger.info(f"Initializing EmbeddingService with model: {model_name}")

    def _load_model(self):
        """Lazy load the model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Successfully loaded model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return self._model

    async def embed(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * 384  # Return zero vector for empty text

        try:
            model = self._load_model()
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                model.encode,
                text
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t if t and t.strip() else " " for t in texts]

        try:
            model = self._load_model()
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                model.encode,
                valid_texts
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def embed_sync(self, text: str) -> List[float]:
        """
        Synchronous version of embed for non-async contexts.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            return [0.0] * 384

        try:
            model = self._load_model()
            embedding = model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise


# Global singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
