from __future__ import annotations

import ast
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer


DEFAULT_DATA_PATH = Path("datasets/preprocessed_jobs.csv")
ARTIFACT_DIR = Path("data/models/skill_gap_ranker")
MODEL_PATH = ARTIFACT_DIR / "skill_gap_ranker.joblib"
METADATA_PATH = ARTIFACT_DIR / "skill_gap_ranker_metadata.json"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _normalize_whitespace(value: str) -> str:
    return " ".join(str(value).split())


def _parse_skill_list(value: Any) -> list[str]:
    raw_text = _safe_text(value)
    if not raw_text:
        return []

    try:
        parsed = ast.literal_eval(raw_text)
        if isinstance(parsed, list):
            return [re.sub(r"\s+", " ", str(item)).strip() for item in parsed if str(item).strip()]  # noqa: PERF401
    except Exception:
        pass

    if raw_text.startswith("[") and raw_text.endswith("]"):
        raw_text = raw_text[1:-1]

    return [part.strip().strip("'\"") for part in raw_text.split(",") if part.strip().strip("'\"")]


def _build_job_text(row: pd.Series) -> str:
    category = _safe_text(row.get("category"))
    job_title = _safe_text(row.get("job_title"))
    job_description = _safe_text(row.get("job_description"))
    skills = _parse_skill_list(row.get("job_skill_set"))
    return " ".join(part for part in [category, job_title, job_description, ", ".join(skills)] if part)


def load_training_data(csv_path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    required_columns = {"category", "job_title", "job_description", "job_skill_set"}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns in training data: {sorted(missing_columns)}")

    frame = frame.copy()
    frame["job_text"] = frame.apply(_build_job_text, axis=1)
    frame["skill_list"] = frame["job_skill_set"].apply(_parse_skill_list)
    return frame


def _get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        return SentenceTransformer(EMBEDDING_MODEL_NAME)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _cached_embedding_model():
    return _get_embedding_model()


def train_and_save_model(csv_path: str | Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    frame = load_training_data(csv_path)
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1, max_features=20000)
    job_matrix = vectorizer.fit_transform(frame["job_text"].astype(str))

    skill_counts: dict[str, int] = {}
    job_skill_map: dict[str, list[str]] = {}
    for _, row in frame.iterrows():
        job_title = _safe_text(row.get("job_title"))
        skills = row["skill_list"]
        job_skill_map.setdefault(job_title, [])
        for skill in skills:
            normalized_skill = _normalize_whitespace(skill)
            if normalized_skill not in job_skill_map[job_title]:
                job_skill_map[job_title].append(normalized_skill)
            skill_counts[normalized_skill] = skill_counts.get(normalized_skill, 0) + 1

    payload = {
        "vectorizer": vectorizer,
        "job_matrix": job_matrix,
        "frame": frame[["category", "job_title", "job_description", "skill_list", "job_text"]],
        "skill_counts": skill_counts,
        "job_skill_map": job_skill_map,
        "embedding_model_name": EMBEDDING_MODEL_NAME,
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, MODEL_PATH)

    metadata = {
        "training_rows": int(len(frame)),
        "job_titles": int(frame["job_title"].nunique()),
        "skill_vocabulary_size": int(len(skill_counts)),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "data_path": str(Path(csv_path)),
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def _normalize_skill_name(skill: str) -> str:
    return _normalize_whitespace(skill).lower()


def _similarity_scores(job_matrix, query_vector):
    similarity = job_matrix @ query_vector.T
    if hasattr(similarity, "toarray"):
        return np.asarray(similarity.toarray()).ravel()
    return np.asarray(similarity).ravel()


def rank_missing_skills(
    selected_role: str,
    extracted_skills: list[str],
    candidate_skills: list[str] | None = None,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    model = load_model()
    if model is None:
        return []

    frame: pd.DataFrame = model["frame"]
    vectorizer: TfidfVectorizer = model["vectorizer"]
    job_matrix = model["job_matrix"]
    job_skill_map: dict[str, list[str]] = model["job_skill_map"]

    normalized_resume_skills = {_normalize_skill_name(skill) for skill in extracted_skills if _normalize_skill_name(skill)}
    query_text = _normalize_whitespace(selected_role)
    query_vector = vectorizer.transform([query_text])
    job_scores = _similarity_scores(job_matrix, query_vector)

    top_job_indices = np.argsort(job_scores)[::-1][:5]
    top_jobs = frame.iloc[top_job_indices]

    exact_role_skills: list[str] = []
    exact_role_rows = frame[
        frame["job_title"].astype(str).str.lower().eq(selected_role.strip().lower())
    ]
    if not exact_role_rows.empty:
        exact_role_skills = sorted({skill for skills in exact_role_rows["skill_list"] for skill in skills})
    else:
        exact_role_skills = sorted(job_skill_map.get(selected_role, []))

    if candidate_skills is not None and candidate_skills:
        skills_to_rank = candidate_skills
    elif exact_role_skills:
        skills_to_rank = exact_role_skills
    else:
        skills_to_rank = sorted({skill for skills in top_jobs["skill_list"] for skill in skills})

    if not skills_to_rank:
        return []

    embedding_model = _cached_embedding_model()
    role_embedding = None
    if embedding_model is not None:
        try:
            role_embedding = embedding_model.encode([query_text], normalize_embeddings=True)[0]
        except Exception:
            role_embedding = None

    top_job_skill_lists = [list(skills) for skills in top_jobs["skill_list"].tolist()]

    ranked_items: list[dict[str, Any]] = []
    for skill in skills_to_rank:
        normalized_skill = _normalize_skill_name(skill)
        if normalized_skill in normalized_resume_skills:
            continue

        # Rule score: how frequently the skill appears among the most similar jobs.
        frequency = sum(1 for skills in top_job_skill_lists if any(_normalize_skill_name(item) == normalized_skill for item in skills))
        rule_score = frequency / max(1, len(top_job_skill_lists))

        # Retrieval score: use the best similar job that contains this skill.
        supporting_job_scores = [float(job_scores[index]) for index, skills in zip(top_job_indices, top_job_skill_lists) if any(_normalize_skill_name(item) == normalized_skill for item in skills)]
        retrieval_score = max(supporting_job_scores) if supporting_job_scores else 0.0

        # Semantic score: skill text vs role text.
        semantic_score = 0.0
        if role_embedding is not None:
            try:
                skill_embedding = embedding_model.encode([skill], normalize_embeddings=True)[0]
                semantic_score = float(np.dot(role_embedding, skill_embedding))
                semantic_score = max(0.0, min(1.0, semantic_score))
            except Exception:
                semantic_score = 0.0

        exact_bonus = 1.0 if any(_normalize_skill_name(item) == normalized_skill for item in exact_role_skills) else 0.0
        final_score = (0.40 * rule_score) + (0.30 * retrieval_score) + (0.20 * semantic_score) + (0.10 * exact_bonus)

        ranked_items.append(
            {
                "skill": skill,
                "score": round(final_score * 100, 2),
                "model_probability": round(retrieval_score * 100, 2),
                "rule_score": round(rule_score * 100, 2),
                "retrieval_score": round(retrieval_score * 100, 2),
                "semantic_similarity": round(semantic_score * 100, 2),
                "exact_bonus": exact_bonus,
            }
        )

    ranked_items.sort(key=lambda item: item["score"], reverse=True)
    return ranked_items[:top_n]
