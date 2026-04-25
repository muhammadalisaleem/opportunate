from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import FeatureUnion, Pipeline


ARTIFACT_DIR = Path("data/models/job_recommender")
MODEL_PATH = ARTIFACT_DIR / "job_recommender.joblib"
METADATA_PATH = ARTIFACT_DIR / "job_recommender_metadata.json"
SKILL_TO_JOB_PATH = Path("data/dataset/skill_to_job.json")
JOB_TO_SKILL_PATH = Path("data/dataset/job_to_skill.json")
JOB_DEFINITION_PATH = Path("data/dataset/job_definition.json")
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class SentenceTransformerEmbedder:
    """Sentence-transformers wrapper compatible with sklearn pipelines."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self.embedding_dim = 384

    def fit(self, texts: Iterable[str], labels=None):  # noqa: D401, ANN001
        return self

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore

                self._model = SentenceTransformer(self.model_name)
                if hasattr(self._model, "get_embedding_dimension"):
                    self.embedding_dim = int(self._model.get_embedding_dimension())
                else:
                    self.embedding_dim = int(self._model.get_sentence_embedding_dimension())
            except Exception:
                self._model = None
        return self._model

    def transform(self, texts: Iterable[str]):
        text_list = [str(text or "") for text in texts]

        model = self._load_model()
        if model is None:
            return sp.csr_matrix((len(text_list), self.embedding_dim), dtype=np.float32)

        embeddings = model.encode(text_list, normalize_embeddings=True, show_progress_bar=False)
        return sp.csr_matrix(np.asarray(embeddings, dtype=np.float32))

    def __getstate__(self):
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "_model": None,
        }

    def __setstate__(self, state):
        self.model_name = state["model_name"]
        self.embedding_dim = int(state.get("embedding_dim", 384))
        self._model = None


def _load_job_names() -> list[str]:
    if METADATA_PATH.exists():
        try:
            with METADATA_PATH.open("r", encoding="utf-8") as file_handle:
                metadata = json.load(file_handle)
                job_names = metadata.get("job_names", [])
                if isinstance(job_names, list):
                    return [str(item) for item in job_names if str(item).strip()]
        except Exception:
            pass

    job_to_skill = _load_json(JOB_TO_SKILL_PATH)
    return _normalize_job_labels(job_to_skill.keys())


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _job_description_lookup(job_descriptions: dict[str, str], job_name: str) -> str:
    parts = [part.strip() for part in job_name.split("/")]
    descriptions = [job_descriptions.get(part) for part in parts if job_descriptions.get(part)]
    return " ".join(descriptions)


def _normalize_job_labels(job_names: Iterable[str]) -> list[str]:
    unique_jobs = []
    seen = set()
    for job_name in job_names:
        normalized = job_name.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_jobs.append(normalized)
    return unique_jobs


def build_training_samples() -> tuple[list[str], list[list[int]], list[str]]:
    job_to_skill = _load_json(JOB_TO_SKILL_PATH)
    job_descriptions = _load_json(JOB_DEFINITION_PATH)

    jobs = _normalize_job_labels(job_to_skill.keys())
    all_skill_names = sorted({skill for skills in job_to_skill.values() for skill in skills})
    job_index = {job_name: index for index, job_name in enumerate(jobs)}

    texts: list[str] = []
    labels: list[list[int]] = []

    for job_name in jobs:
        skills = job_to_skill.get(job_name, [])
        description = _job_description_lookup(job_descriptions, job_name)
        skill_text = ", ".join(skills)

        variants = [
            f"{job_name}. Skills: {skill_text}",
            f"{job_name}. Skills: {skill_text}. {description}",
            f"{description}. Core skills: {skill_text}",
            f"{job_name}. {description}",
        ]

        for variant in variants:
            texts.append(variant)
            label_row = [0] * len(jobs)
            label_row[job_index[job_name]] = 1
            labels.append(label_row)

    # Add skill-centric weak labels to help the classifier learn smaller resume inputs.
    skill_to_job = _load_json(SKILL_TO_JOB_PATH)
    for skill_name, mapped_jobs in skill_to_job.items():
        normalized_jobs = [job for job in mapped_jobs if job in job_index]
        if not normalized_jobs:
            continue

        texts.append(f"Skill: {skill_name}")
        label_row = [0] * len(jobs)
        for job_name in normalized_jobs:
            label_row[job_index[job_name]] = 1
        labels.append(label_row)

    return texts, labels, jobs


def _build_pipeline() -> Pipeline:
    feature_union = FeatureUnion(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    max_features=8000,
                ),
            ),
            ("embeddings", SentenceTransformerEmbedder()),
        ]
    )

    classifier = OneVsRestClassifier(
        LogisticRegression(
            solver="liblinear",
            max_iter=1000,
            class_weight="balanced",
        )
    )

    return Pipeline([("features", feature_union), ("classifier", classifier)])


def train_and_save_model() -> dict[str, object]:
    texts, labels, job_names = build_training_samples()
    pipeline = _build_pipeline()
    pipeline.fit(texts, labels)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    metadata = {
        "job_count": len(job_names),
        "sample_count": len(texts),
        "job_names": job_names,
        "embedding_model": EMBEDDING_MODEL_NAME,
    }

    with METADATA_PATH.open("w", encoding="utf-8") as file_handle:
        json.dump(metadata, file_handle, indent=2)

    return metadata


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def _rule_based_recommendations(resume_skills: list[str], top_n: int):
    from collections import defaultdict

    skill_to_job = _load_json(SKILL_TO_JOB_PATH)
    job_definitions = _load_json(JOB_DEFINITION_PATH)
    normalized_skill_to_job = {skill.lower(): jobs for skill, jobs in skill_to_job.items()}

    job_scores = defaultdict(lambda: {"count": 0, "skills": []})
    for skill in resume_skills:
        for job_name in normalized_skill_to_job.get(skill.lower(), []):
            job_scores[job_name]["count"] += 1
            job_scores[job_name]["skills"].append(skill)

    sorted_jobs = sorted(job_scores.items(), key=lambda item: item[1]["count"], reverse=True)
    top_jobs = []

    for job_name, info in sorted_jobs[:top_n]:
        matched_skills = sorted(set(info["skills"]))
        parts = [part.strip() for part in job_name.split("/")]
        descriptions = []
        for part in parts:
            desc = job_definitions.get(part)
            if desc:
                descriptions.append(f"<strong>{part}</strong>: {desc}")

        full_description = (
            "".join(
                f"<div style='padding-left: 20px; margin-bottom: 10px;'>{desc}</div>"
                for desc in descriptions
            )
            if descriptions
            else None
        )

        top_jobs.append(
            {
                "title": job_name,
                "match_count": info["count"],
                "matched_skills": matched_skills,
                "description": full_description,
                "confidence": min(100, info["count"] * 20),
                "source": "rule-based",
            }
        )

    return top_jobs


def recommend_top_jobs(resume_skills: list[str], top_n: int = 5, resume_text: str | None = None):
    model = load_model()
    if model is None:
        return _rule_based_recommendations(resume_skills, top_n)

    job_definitions = _load_json(JOB_DEFINITION_PATH)
    job_to_skill = _load_json(JOB_TO_SKILL_PATH)
    all_jobs = _load_job_names()

    if not all_jobs:
        return _rule_based_recommendations(resume_skills, top_n)

    resume_skill_text = ", ".join(sorted({skill.strip() for skill in resume_skills if skill.strip()}))
    resume_text = (resume_text or "").strip()
    combined_text = " ".join(part for part in [resume_text, resume_skill_text] if part)

    if not combined_text:
        return _rule_based_recommendations(resume_skills, top_n)

    probabilities = model.predict_proba([combined_text])

    if isinstance(probabilities, list):
        job_scores = []
        for prob in probabilities:
            prob_array = np.asarray(prob)
            if prob_array.ndim == 2 and prob_array.shape[1] > 1:
                job_scores.append(float(prob_array[0, 1]))
            elif prob_array.ndim == 2:
                job_scores.append(float(prob_array[0, 0]))
            else:
                job_scores.append(float(prob_array.ravel()[0]))
    else:
        prob_array = np.asarray(probabilities)
        if prob_array.ndim == 2:
            job_scores = [float(score) for score in prob_array[0]]
        else:
            job_scores = [float(score) for score in prob_array.ravel()]

    if len(job_scores) != len(all_jobs):
        return _rule_based_recommendations(resume_skills, top_n)

    ranked_indices = sorted(range(len(all_jobs)), key=lambda index: job_scores[index], reverse=True)
    resume_skill_set = {skill.lower() for skill in resume_skills}
    top_jobs = []

    for index in ranked_indices[:top_n]:
        job_name = all_jobs[index]
        job_skills = job_to_skill.get(job_name, []) if isinstance(job_to_skill.get(job_name, []), list) else []

        matched_skills = sorted({skill for skill in job_skills if skill.lower() in resume_skill_set})
        parts = [part.strip() for part in job_name.split("/")]
        descriptions = []
        for part in parts:
            desc = job_definitions.get(part)
            if desc:
                descriptions.append(f"<strong>{part}</strong>: {desc}")

        full_description = (
            "".join(
                f"<div style='padding-left: 20px; margin-bottom: 10px;'>{desc}</div>"
                for desc in descriptions
            )
            if descriptions
            else None
        )

        top_jobs.append(
            {
                "title": job_name,
                "match_count": len(matched_skills),
                "matched_skills": matched_skills,
                "description": full_description,
                "confidence": round(max(0.0, min(100.0, job_scores[index] * 100.0)), 1),
                "source": "ml",
            }
        )

    return top_jobs
