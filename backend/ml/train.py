import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import shap
import sklearn
import xgboost
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from backend.app.config import PROJECT_ROOT
from backend.app.version import MODEL_VERSION, THRESHOLD_VERSION
from backend.ml.data import (
    SOURCE_FILENAMES,
    clean_and_merge,
    create_demo_accounts,
    load_source_data,
    split_accounts,
    write_generated_data,
)
from backend.ml.features import FEATURE_NAMES, build_feature_matrix, is_sufficient
from backend.ml.pipeline import (
    classification_metrics,
    make_preprocessor,
    select_risk_thresholds,
)


def _prepared_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, int]:
    features, completeness = build_feature_matrix(frame)
    usable = completeness.map(is_sufficient).to_numpy()
    removed = int((~usable).sum())
    labels = frame["label"].astype(int).to_numpy()[usable]
    return features.loc[usable].reset_index(drop=True), labels, removed


def train_pipeline(
    dataset_dir: Path,
    artifact_dir: Path,
    generated_dir: Path,
    demo_per_class: int = 50,
    random_state: int = 42,
) -> dict[str, Any]:
    frames = load_source_data(dataset_dir)
    clean, cleaning_summary = clean_and_merge(frames)
    splits = split_accounts(clean, random_state=random_state)
    demo = create_demo_accounts(
        splits["test"],
        per_class=demo_per_class,
        random_state=random_state,
    )
    write_generated_data(splits, demo, generated_dir)

    x_train, y_train, train_removed = _prepared_split(splits["train"])
    x_validation, y_validation, validation_removed = _prepared_split(
        splits["validation"]
    )
    x_test, y_test, test_removed = _prepared_split(splits["test"])

    preprocessor = make_preprocessor()
    transformed_train = preprocessor.fit_transform(x_train)
    transformed_validation = preprocessor.transform(x_validation)
    transformed_test = preprocessor.transform(x_test)

    baseline = LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=random_state,
    )
    baseline.fit(transformed_train, y_train)
    baseline_probability = baseline.predict_proba(transformed_test)[:, 1]

    negative_count = max(int((y_train == 0).sum()), 1)
    positive_count = max(int((y_train == 1).sum()), 1)
    model = XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=negative_count / positive_count,
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        random_state=random_state,
        n_jobs=4,
    )
    model.fit(transformed_train, y_train)
    validation_probability = model.predict_proba(transformed_validation)[:, 1]
    thresholds = select_risk_thresholds(y_validation, validation_probability)
    test_probability = model.predict_proba(transformed_test)[:, 1]

    artifact_dir.mkdir(parents=True, exist_ok=True)
    model.save_model(artifact_dir / "xgboost_model.json")
    joblib.dump(preprocessor, artifact_dir / "preprocessor.joblib")
    joblib.dump(baseline, artifact_dir / "logistic_baseline.joblib")

    transformed_feature_names = preprocessor.get_feature_names_out().tolist()
    created_at = datetime.now(timezone.utc).isoformat()
    model_id = MODEL_VERSION
    metadata: dict[str, Any] = {
        "model_id": model_id,
        "model_version": MODEL_VERSION,
        "threshold_version": THRESHOLD_VERSION,
        "created_at": created_at,
        "random_state": random_state,
        "source_files": list(SOURCE_FILENAMES),
        "feature_names": FEATURE_NAMES,
        "transformed_feature_names": transformed_feature_names,
        "thresholds": thresholds,
        "confidence_margin": 0.08,
        "cleaning": cleaning_summary,
        "split_counts": {name: int(len(frame)) for name, frame in splits.items()},
        "below_completeness_threshold_removed": {
            "train": train_removed,
            "validation": validation_removed,
            "test": test_removed,
        },
        "metrics": {
            "logistic_regression_test": classification_metrics(
                y_test, baseline_probability
            ),
            "xgboost_test": classification_metrics(
                y_test,
                test_probability,
                threshold=thresholds["medium"],
            ),
        },
        "library_versions": {
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
            "shap": shap.__version__,
        },
    }
    (artifact_dir / "model_metadata.json").write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare local data and train the FIT5238 backend models."
    )
    parser.add_argument("--dataset-dir", type=Path, default=PROJECT_ROOT / "dataset")
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=PROJECT_ROOT / "models" / MODEL_VERSION,
    )
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=PROJECT_ROOT / "backend" / "data" / "generated",
    )
    parser.add_argument("--demo-per-class", type=int, default=50)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metadata = train_pipeline(
        dataset_dir=args.dataset_dir,
        artifact_dir=args.artifact_dir,
        generated_dir=args.generated_dir,
        demo_per_class=args.demo_per_class,
    )
    summary = {
        "model_id": metadata["model_id"],
        "clean_account_count": metadata["cleaning"]["clean_account_count"],
        "thresholds": metadata["thresholds"],
        "metrics": metadata["metrics"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
