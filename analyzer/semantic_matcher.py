from functools import lru_cache


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_embedding_model():
    """Load the embedding model once and reuse it across requests."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        return SentenceTransformer(MODEL_NAME)
    except Exception:
        return None


def compute_semantic_match_score(resume_text: str, jd_text: str) -> tuple[float, bool, str | None]:
    """
    Returns:
        semantic_pct: 0..100 semantic similarity score
        available: whether semantic model was available
        error_message: optional error detail if unavailable
    """
    model = _load_embedding_model()
    resume_input = (resume_text or "").strip()[:8000]
    jd_input = (jd_text or "").strip()[:8000]

    if not resume_input or not jd_input:
        return 0.0, True, None

    if model is not None:
        try:
            embeddings = model.encode([resume_input, jd_input], normalize_embeddings=True)
            resume_vec, jd_vec = embeddings[0], embeddings[1]

            cosine_similarity = float((resume_vec @ jd_vec).item())
            cosine_similarity = max(-1.0, min(1.0, cosine_similarity))

            semantic_pct = ((cosine_similarity + 1.0) / 2.0) * 100.0
            return semantic_pct, True, None
        except Exception as exc:
            return 0.0, False, f"Semantic scoring failed: {exc}"

    try:
        from preprocessor.spacy_nlp import load_spacy_nlp_model

        nlp = load_spacy_nlp_model()
        resume_doc = nlp(resume_input[:4000])
        jd_doc = nlp(jd_input[:4000])

        similarity = float(resume_doc.similarity(jd_doc))
        similarity = max(0.0, min(1.0, similarity))
        semantic_pct = similarity * 100.0

        return semantic_pct, True, (
            "Using spaCy semantic fallback. Install sentence-transformers for stronger semantic matching."
        )
    except Exception as exc:
        return 0.0, False, f"Semantic model unavailable: {exc}"