from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DEFAULT_DATA_PATH = Path("datasets/preprocessed_resumes.csv")
ARTIFACT_DIR = Path("data/models/ats_score_model")
MODEL_PATH = ARTIFACT_DIR / "ats_score_model.joblib"
METADATA_PATH = ARTIFACT_DIR / "ats_score_model_metadata.json"

EDUCATION_RANKS = {
    "high school": 0,
    "associate": 1,
    "diploma": 1,
    "b.sc": 2,
    "bsc": 2,
    "b.tech": 3,
    "btech": 3,
    "mba": 4,
    "m.sc": 4,
    "msc": 4,
    "m.tech": 5,
    "mtech": 5,
    "phd": 6,
}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _parse_certification_count(value: Any) -> int:
    text = _safe_text(value)
    if not text:
        return 0
    if text.lower() in {"none", "n/a", "na", "-"}:
        return 0
    return max(1, len([part for part in re.split(r"[,;/|]", text) if part.strip()]))


def _parse_education_rank(value: Any) -> int:
    text = _safe_text(value).lower()
    for key, rank in EDUCATION_RANKS.items():
        if key in text:
            return rank
    return 2


def _parse_skill_count(value: Any) -> int:
    text = _safe_text(value)
    if not text:
        return 0
    return len([part for part in re.split(r"[,;/|]", text) if part.strip()])


def _build_features_from_row(row: pd.Series | dict[str, Any]) -> dict[str, Any]:
    skills_text = _safe_text(row.get("Skills"))
    education = _safe_text(row.get("Education"))
    certifications = _safe_text(row.get("Certifications"))

    skill_count = _parse_skill_count(skills_text)
    cert_count = _parse_certification_count(certifications)

    return {
        "experience_years": float(row.get("Experience (Years)", 0) or 0),
        "projects_count": float(row.get("Projects Count", 0) or 0),
        "skill_count": float(skill_count),
        "skill_char_count": float(len(skills_text)),
        "cert_count": float(cert_count),
        "has_certification": "yes" if cert_count else "no",
        "education_rank": float(_parse_education_rank(education)),
    }


def load_training_data(csv_path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    required_columns = {"Skills", "Experience (Years)", "Education", "Certifications", "Projects Count", "AI Score (0-100)"}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns in training data: {sorted(missing_columns)}")

    feature_rows = frame.apply(_build_features_from_row, axis=1, result_type="expand")
    feature_frame = pd.concat([frame.copy(), feature_rows], axis=1)
    return feature_frame


def build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                ["has_certification"],
            ),
            (
                "numeric",
                "passthrough",
                ["experience_years", "projects_count", "skill_count", "skill_char_count", "cert_count", "education_rank"],
            ),
        ]
    )

    model = GradientBoostingRegressor(
        random_state=42,
        n_estimators=250,
        learning_rate=0.05,
        max_depth=3,
    )

    return Pipeline([("features", preprocessor), ("model", model)])


def train_and_save_model(csv_path: str | Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    frame = load_training_data(csv_path)
    feature_columns = [
        "has_certification",
        "experience_years",
        "projects_count",
        "skill_count",
        "skill_char_count",
        "cert_count",
        "education_rank",
    ]

    X = frame[feature_columns]
    y = frame["AI Score (0-100)"].astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = root_mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    metadata = {
        "training_rows": int(len(frame)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "target": "AI Score (0-100)",
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
        "data_path": str(Path(csv_path)),
        "feature_columns": feature_columns,
    }

    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def extract_text_features(text: str, uploaded_file=None) -> dict[str, Any]:
    normalized_text = text or ""
    word_count = len(re.findall(r"\b\w+\b", normalized_text))
    line_count = len([line for line in normalized_text.splitlines() if line.strip()])
    bullet_count = len(re.findall(r"(?:^|\n)\s*[-•*]\s+", normalized_text))
    quant_count = len(re.findall(r"\d+%|\b\d{2,}\b", normalized_text))
    experience_matches = re.findall(r"(\d{1,2})\+?\s+years?", normalized_text, flags=re.IGNORECASE)
    experience_years = float(max([int(match) for match in experience_matches], default=0))

    education_text = normalized_text.lower()
    education_rank = 2
    for key, rank in EDUCATION_RANKS.items():
        if key in education_text:
            education_rank = rank
            break

    certification_count = len(re.findall(r"\b(certified|certification|certificate|aws certified|shrm|pmp|cissp|google ml|deep learning specialization)\b", normalized_text, flags=re.IGNORECASE))
    if uploaded_file is not None and hasattr(uploaded_file, "name"):
        file_name = str(uploaded_file.name).lower()
        has_pdf = 1.0 if file_name.endswith(".pdf") else 0.0
    else:
        has_pdf = 0.0

    return {
        "experience_years": experience_years,
        "projects_count": float(len(re.findall(r"\bproject\b", normalized_text, flags=re.IGNORECASE))),
        "skill_count": float(len(set(re.findall(r"\b[a-z][a-z0-9+.#-]{1,}\b", normalized_text.lower())))),
        "skill_char_count": float(len(normalized_text)),
        "cert_count": float(certification_count),
        "has_certification": "yes" if certification_count else "no",
        "education_rank": float(education_rank),
        "word_count": float(word_count),
        "line_count": float(line_count),
        "bullet_count": float(bullet_count),
        "quant_count": float(quant_count),
        "has_pdf": has_pdf,
    }


def predict_score(text: str, uploaded_file=None) -> tuple[float, dict[str, Any]]:
    model = load_model()
    if model is None:
        return 0.0, {"available": False, "reason": "ATS score model not trained yet."}

    features = extract_text_features(text, uploaded_file)
    model_input = pd.DataFrame([
        {
            "has_certification": features["has_certification"],
            "experience_years": features["experience_years"],
            "projects_count": features["projects_count"],
            "skill_count": features["skill_count"],
            "skill_char_count": features["skill_char_count"],
            "cert_count": features["cert_count"],
            "education_rank": features["education_rank"],
        }
    ])

    score = float(model.predict(model_input)[0])
    bounded_score = max(0.0, min(100.0, score))
    return bounded_score, {"available": True, "features": features}
