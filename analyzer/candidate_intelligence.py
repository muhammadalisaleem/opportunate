from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


RESUME_DATA_PATH = Path("datasets/preprocessed_resumes.csv")
JOBS_DATA_PATH = Path("datasets/preprocessed_jobs.csv")

ARTIFACT_DIR = Path("data/models/candidate_intelligence")
MODEL_PATH = ARTIFACT_DIR / "candidate_intelligence.joblib"
METADATA_PATH = ARTIFACT_DIR / "candidate_intelligence_metadata.json"


def _normalize_skills_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.strip().lower()


def _extract_experience_years(resume_text: str) -> float:
    matches = re.findall(r"(\d{1,2})\+?\s+years?", resume_text or "", flags=re.IGNORECASE)
    return float(max([int(item) for item in matches], default=0))


def _extract_projects_count(resume_text: str) -> float:
    return float(len(re.findall(r"\bproject\b", resume_text or "", flags=re.IGNORECASE)))


def _pick_job_text_column(jobs: pd.DataFrame) -> str:
    candidates = [
        "Skills",
        "skills",
        "Required Skills",
        "required_skills",
        "job_description",
        "description",
        "job_skill_set",
    ]
    for column_name in candidates:
        if column_name in jobs.columns:
            return column_name
    raise ValueError(f"No suitable text column found in jobs dataset. Columns: {jobs.columns.tolist()}")


def train_and_save_models(
    resume_csv_path: str | Path = RESUME_DATA_PATH,
    jobs_csv_path: str | Path = JOBS_DATA_PATH,
) -> dict[str, Any]:
    resumes = pd.read_csv(resume_csv_path)
    jobs = pd.read_csv(jobs_csv_path)

    required_resume_columns = {
        "Skills",
        "Experience (Years)",
        "Projects Count",
        "Recruiter Decision",
        "Salary Expectation ($)",
    }
    missing = required_resume_columns.difference(resumes.columns)
    if missing:
        raise ValueError(f"Missing resume dataset columns: {sorted(missing)}")

    resumes = resumes.copy()
    resumes["Skills"] = resumes["Skills"].fillna("").map(_normalize_skills_text)

    label_encoder = LabelEncoder()
    resumes["Decision_encoded"] = label_encoder.fit_transform(resumes["Recruiter Decision"])

    tfidf = TfidfVectorizer(max_features=400, stop_words="english")
    skills_tfidf = tfidf.fit_transform(resumes["Skills"])
    skills_df = pd.DataFrame(
        skills_tfidf.toarray(),
        columns=[f"skill_{index}" for index in range(skills_tfidf.shape[1])],
    )

    numeric_features = ["Experience (Years)", "Projects Count"]
    X_class = pd.concat([resumes[numeric_features].reset_index(drop=True), skills_df.reset_index(drop=True)], axis=1)
    X_reg = pd.concat(
        [
            resumes[numeric_features + ["AI Score (0-100)"]].reset_index(drop=True),
            skills_df.reset_index(drop=True),
        ],
        axis=1,
    )

    y_class = resumes["Decision_encoded"]
    y_reg = resumes["Salary Expectation ($)"]

    X_train_class, _, y_train_class, _ = train_test_split(
        X_class,
        y_class,
        test_size=0.2,
        random_state=42,
        stratify=y_class,
    )
    X_train_reg, _, y_train_reg, _ = train_test_split(
        X_reg,
        y_reg,
        test_size=0.2,
        random_state=42,
    )

    classifier = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    classifier.fit(X_train_class, y_train_class)

    regressor = RandomForestRegressor(n_estimators=200, random_state=42)
    regressor.fit(X_train_reg, y_train_reg)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_class)

    best_k = 4
    best_silhouette = -1.0
    for candidate_k in range(2, 11):
        kmeans = KMeans(n_clusters=candidate_k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, cluster_labels)
        if score > best_silhouette:
            best_silhouette = float(score)
            best_k = int(candidate_k)

    clustering_model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    clustering_model.fit(X_scaled)

    job_text_column = _pick_job_text_column(jobs)
    jobs = jobs.copy()
    jobs[job_text_column] = jobs[job_text_column].fillna("").astype(str).str.lower()
    jobs_tfidf = tfidf.transform(jobs[job_text_column])

    bundle = {
        "tfidf": tfidf,
        "classifier": classifier,
        "regressor": regressor,
        "scaler": scaler,
        "kmeans": clustering_model,
        "label_encoder": label_encoder,
        "classification_columns": X_class.columns.tolist(),
        "regression_columns": X_reg.columns.tolist(),
        "jobs": jobs,
        "jobs_tfidf": jobs_tfidf,
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH)

    metadata = {
        "resume_rows": int(len(resumes)),
        "job_rows": int(len(jobs)),
        "classification_features": int(X_class.shape[1]),
        "regression_features": int(X_reg.shape[1]),
        "clusters": int(best_k),
        "silhouette_score": float(best_silhouette),
        "job_text_column": job_text_column,
        "resume_data_path": str(Path(resume_csv_path)),
        "jobs_data_path": str(Path(jobs_csv_path)),
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


@lru_cache(maxsize=1)
def load_models() -> dict[str, Any] | None:
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def _build_feature_row(skills: list[str], resume_text: str, include_ai_score: bool = False) -> dict[str, float]:
    normalized_skills = [skill.strip().lower() for skill in skills if str(skill).strip()]
    skills_text = ", ".join(normalized_skills)

    feature_row = {
        "Experience (Years)": _extract_experience_years(resume_text),
        "Projects Count": _extract_projects_count(resume_text),
    }
    if include_ai_score:
        # Lightweight proxy for notebook parity; keeps the regressor input schema intact.
        feature_row["AI Score (0-100)"] = min(100.0, 40.0 + (len(set(normalized_skills)) * 4.0))

    feature_row["skills_text"] = skills_text
    return feature_row


def predict_candidate_insights(resume_text: str, skills: list[str], top_n: int = 5) -> dict[str, Any]:
    models = load_models()
    if models is None:
        return {"available": False, "reason": "Candidate intelligence models are not trained yet."}

    feature_row = _build_feature_row(skills, resume_text, include_ai_score=True)
    tfidf_vector = models["tfidf"].transform([feature_row["skills_text"]]).toarray()[0]
    skill_feature_values = {f"skill_{index}": float(value) for index, value in enumerate(tfidf_vector)}

    class_input_dict = {
        "Experience (Years)": feature_row["Experience (Years)"],
        "Projects Count": feature_row["Projects Count"],
        **skill_feature_values,
    }
    regression_input_dict = {
        "Experience (Years)": feature_row["Experience (Years)"],
        "Projects Count": feature_row["Projects Count"],
        "AI Score (0-100)": feature_row["AI Score (0-100)"],
        **skill_feature_values,
    }

    class_df = pd.DataFrame([class_input_dict]).reindex(columns=models["classification_columns"], fill_value=0.0)
    reg_df = pd.DataFrame([regression_input_dict]).reindex(columns=models["regression_columns"], fill_value=0.0)

    probabilities = models["classifier"].predict_proba(class_df)[0]
    class_index = int(np.argmax(probabilities))
    predicted_decision = str(models["label_encoder"].inverse_transform([class_index])[0])
    decision_confidence = float(np.max(probabilities) * 100.0)

    predicted_salary = float(models["regressor"].predict(reg_df)[0])

    scaled_vector = models["scaler"].transform(class_df)
    cluster_id = int(models["kmeans"].predict(scaled_vector)[0])

    resume_sparse = models["tfidf"].transform([feature_row["skills_text"]])
    similarity_scores = (models["jobs_tfidf"] @ resume_sparse.T).toarray().ravel()
    ranked_indices = np.argsort(similarity_scores)[::-1][: max(1, top_n)]

    jobs_df: pd.DataFrame = models["jobs"]
    recommendations: list[dict[str, Any]] = []
    for index in ranked_indices:
        row = jobs_df.iloc[int(index)]
        recommendations.append(
            {
                "job_id": row.get("job_id"),
                "job_title": row.get("job_title"),
                "category": row.get("category"),
                "match_score": round(float(similarity_scores[int(index)] * 100.0), 2),
            }
        )

    return {
        "available": True,
        "decision": predicted_decision,
        "decision_confidence": round(decision_confidence, 2),
        "salary_prediction": round(predicted_salary, 2),
        "cluster": cluster_id,
        "experience_years": feature_row["Experience (Years)"],
        "projects_count": feature_row["Projects Count"],
        "recommendations": recommendations,
    }