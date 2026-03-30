"""Nexus embedding service — Google text-embedding-004, always Gemini regardless of AI_PROVIDER."""

import json
import logging
import os

logger = logging.getLogger(__name__)

_EMBEDDING_MODEL = "models/text-embedding-004"


def generate_embedding(text: str) -> list[float]:
    """Generate a 768-dim embedding using Google text-embedding-004.

    Always uses GOOGLE_API_KEY regardless of AI_PROVIDER env var.
    """
    import google.generativeai as genai  # lazy import

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set — cannot generate embeddings")

    genai.configure(api_key=api_key)
    result = genai.embed_content(model=_EMBEDDING_MODEL, content=text)
    return result["embedding"]


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors using numpy."""
    import numpy as np

    a = np.array(vec_a, dtype=float)
    b = np.array(vec_b, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def semantic_search(
    query: str,
    candidates: list[dict],
    embedding_field: str = "embedding",
    top_k: int = 5,
) -> list[dict]:
    """Search candidates by cosine similarity to query embedding.

    Args:
        query: Natural language question.
        candidates: List of dicts each containing an embedding_field (JSON list[float]).
        embedding_field: Key in each dict that holds the embedding (JSON string or list).
        top_k: Number of top results to return.

    Returns:
        Top-k candidates sorted by descending similarity, each with added "_score".
    """
    if not candidates:
        return []

    query_vec = generate_embedding(query)

    scored = []
    for c in candidates:
        raw = c.get(embedding_field)
        if raw is None:
            continue
        try:
            vec = raw if isinstance(raw, list) else json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            continue
        score = cosine_similarity(query_vec, vec)
        scored.append({**c, "_score": score})

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# DB helpers — update embedding columns
# ---------------------------------------------------------------------------


def embed_intel(intel_id: int) -> bool:
    """Generate and persist embedding for nx_intel.embedding.

    Returns True on success, False on failure.
    """
    from database.connection import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT title, raw_input FROM nx_intel WHERE id = %s", (intel_id,)
            )
            row = cur.fetchone()
    if not row:
        return False

    title, raw_input = row
    text = f"{title or ''}\n{raw_input or ''}".strip()
    if not text:
        return False

    try:
        vec = generate_embedding(text)
    except Exception as e:
        logger.warning("embed_intel #%d failed: %s", intel_id, e)
        return False

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE nx_intel SET embedding = %s WHERE id = %s",
                (json.dumps(vec), intel_id),
            )
    return True


def embed_knowledge_chunk(chunk_id: int) -> bool:
    """Generate and persist embedding for nx_knowledge.embedding.

    Returns True on success, False on failure.
    """
    from database.connection import get_connection

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT content, summary FROM nx_knowledge WHERE id = %s", (chunk_id,)
            )
            row = cur.fetchone()
    if not row:
        return False

    content, summary = row
    text = f"{summary or ''}\n{content or ''}".strip()
    if not text:
        return False

    try:
        vec = generate_embedding(text)
    except Exception as e:
        logger.warning("embed_knowledge_chunk #%d failed: %s", chunk_id, e)
        return False

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE nx_knowledge SET embedding = %s WHERE id = %s",
                (json.dumps(vec), chunk_id),
            )
    return True
