"""Embedding search over agent cards.

Each card is embedded as several vectors: one for "name: summary" and one per artifact. An agent's
score for a query is its best-matching vector, so one strong artifact match (an email address, a
reference number) isn't diluted by the rest of the card.

Vectors are cached by text in a .npz next to roster.json. A search embeds only texts that aren't
cached yet (new cards, changed summaries or artifacts) in the same request as the query, so the
index always matches the current roster and never needs a separate sync step.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

from ...config import data_dir, get_settings
from ...logging_config import logger
from ...openrouter_client import request_embeddings
from .roster import AgentCard

_EMBED_BATCH_SIZE = 256


def card_texts(card: AgentCard) -> List[str]:
    """The texts embedded for a card: "name: summary" first, then each artifact."""
    head = f"{card.name}: {card.summary}" if card.summary else card.name
    return [head, *card.artifacts]


def _normalize(vectors: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.where(norms == 0, 1.0, norms)


class EmbeddingStore:
    """Cache of text -> unit vector, held in memory and persisted as a .npz."""

    def __init__(self, path: Path):
        self._path = path
        self._loaded = False
        self._rows: Dict[str, int] = {}
        self._matrix = np.zeros((0, 0), dtype=np.float32)

    @staticmethod
    def _key(text: str) -> str:
        # The model and dimensions are part of the key, so changing either re-embeds everything
        settings = get_settings()
        raw = f"{settings.embedding_model}|{settings.embedding_dimensions}|{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not self._path.exists():
            return
        try:
            with np.load(self._path) as data:
                keys, matrix = [str(k) for k in data["keys"]], data["vectors"].astype(np.float32)
            self._rows = {key: row for row, key in enumerate(keys)}
            self._matrix = matrix
        except Exception as exc:
            logger.warning(f"Failed to load agent embeddings, rebuilding: {exc}")

    def missing(self, texts: Sequence[str]) -> List[str]:
        self._load()
        return [text for text in dict.fromkeys(texts) if self._key(text) not in self._rows]

    def add(self, texts: Sequence[str], vectors: np.ndarray) -> None:
        new = [(self._key(t), v) for t, v in zip(texts, vectors) if self._key(t) not in self._rows]
        if not new:
            return
        stacked = np.stack([v for _, v in new]).astype(np.float32)
        start = len(self._rows)
        self._matrix = stacked if start == 0 else np.vstack([self._matrix, stacked])
        for offset, (key, _) in enumerate(new):
            self._rows[key] = start + offset

    def rows(self, texts: Sequence[str]) -> np.ndarray:
        return self._matrix[[self._rows[self._key(t)] for t in texts]]

    def clear(self) -> None:
        """Drop every cached vector, in memory and on disk."""
        self._rows = {}
        self._matrix = np.zeros((0, 0), dtype=np.float32)
        self._loaded = True
        try:
            self._path.unlink(missing_ok=True)
            logger.info("Cleared agent embeddings")
        except Exception as exc:
            logger.warning(f"Failed to clear agent embeddings: {exc}")

    def save(self, keep: Sequence[str]) -> None:
        """Persist only the vectors for `keep` (the current roster's texts), dropping stale ones."""
        keep_keys = [k for k in dict.fromkeys(self._key(t) for t in keep) if k in self._rows]
        matrix = self._matrix[[self._rows[k] for k in keep_keys]] if keep_keys else self._matrix[:0]
        self._rows = {key: row for row, key in enumerate(keep_keys)}
        self._matrix = matrix

        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self._path.parent, prefix=".agent-embeddings-", suffix=".npz")
        try:
            with os.fdopen(fd, "wb") as f:
                np.savez(f, keys=np.array(keep_keys), vectors=matrix)
            os.replace(tmp_path, self._path)
        except Exception as exc:
            Path(tmp_path).unlink(missing_ok=True)
            logger.warning(f"Failed to save agent embeddings: {exc}")


async def _embed(texts: List[str]) -> np.ndarray:
    settings = get_settings()
    vectors: List[List[float]] = []
    for start in range(0, len(texts), _EMBED_BATCH_SIZE):
        vectors.extend(
            await request_embeddings(
                model=settings.embedding_model,
                inputs=texts[start : start + _EMBED_BATCH_SIZE],
                dimensions=settings.embedding_dimensions,
                api_key=settings.openrouter_api_key,
            )
        )
    return _normalize(np.asarray(vectors, dtype=np.float32))


async def search_agent_cards(query: str, cards: Sequence[AgentCard], top_k: int) -> List[AgentCard]:
    """Return the `top_k` cards most similar to `query`, best match first."""
    store = get_embedding_store()
    texts_per_card = [card_texts(card) for card in cards]
    all_texts = [text for texts in texts_per_card for text in texts]

    # The query rides along with any uncached card texts, so a search is one embedding request
    missing = store.missing(all_texts)
    embedded = await _embed([query, *missing])
    query_vector = embedded[0]
    if missing:
        store.add(missing, embedded[1:])
        store.save(keep=all_texts)
        logger.info(f"Embedded {len(missing)} new agent card texts")

    owners = np.array([index for index, texts in enumerate(texts_per_card) for _ in texts])
    similarities = store.rows(all_texts) @ query_vector
    scores = np.full(len(cards), -np.inf, dtype=np.float32)
    np.maximum.at(scores, owners, similarities)

    best = np.argsort(-scores)[:top_k]
    return [cards[index] for index in best]


_STORE = EmbeddingStore(data_dir() / "execution_agents" / "agent_embeddings.npz")


def get_embedding_store() -> EmbeddingStore:
    """Get the singleton embedding store."""
    return _STORE
