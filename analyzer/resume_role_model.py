from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


DEFAULT_DATA_PATH = Path("datasets/preprocessed_resumes.csv")
ARTIFACT_DIR = Path("data/models/resume_role_model")
MODEL_PATH = ARTIFACT_DIR / "resume_role_model.joblib"
METADATA_PATH = ARTIFACT_DIR / "resume_role_model_metadata.json"


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def build_profile_text(row: pd.Series | dict[str, Any]) -> str:
    """Create the text representation used for training and inference."""
    skills = _safe_text(row.get("Skills"))
    education = _safe_text(row.get("Education"))
    certifications = _safe_text(row.get("Certifications"))

    parts = [
        f"skills {skills}",
        f"education {education}",
        f"certifications {certifications}",
    ]

    return " | ".join(part for part in parts if part.strip())


def load_training_data(csv_path: str | Path = DEFAULT_DATA_PATH) -> pd.DataFrame:
    frame = pd.read_csv(csv_path)
    required_columns = {"Skills", "Education", "Certifications", "Job Role"}
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns in training data: {sorted(missing_columns)}")

    frame = frame.copy()
    frame["profile_text"] = frame.apply(build_profile_text, axis=1)
    return frame


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=12000,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                ),
            ),
        ]
    )


def train_and_save_model(csv_path: str | Path = DEFAULT_DATA_PATH) -> dict[str, Any]:
    frame = load_training_data(csv_path)
    features = frame["profile_text"].astype(str)
    labels = frame["Job Role"].astype(str)

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    report_text = classification_report(y_test, predictions, output_dict=False)
    metadata = {
        "training_rows": int(len(frame)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "labels": sorted(labels.unique().tolist()),
        "accuracy": float(accuracy),
        "data_path": str(Path(csv_path)),
        "report": report_text,
    }

    METADATA_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


@lru_cache(maxsize=1)
def load_model() -> Pipeline | None:
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)


def predict_role(profile_text: str) -> tuple[str, float, list[tuple[str, float]]]:
    model = load_model()
    if model is None:
        return "", 0.0, []

    probabilities = model.predict_proba([profile_text])[0]
    classes = list(model.classes_)
    ranked = sorted(
        zip(classes, probabilities),
        key=lambda item: item[1],
        reverse=True,
    )
    top_role, top_probability = ranked[0]
    top_candidates = [(label, float(prob)) for label, prob in ranked[:3]]
    return str(top_role), float(top_probability), top_candidates
