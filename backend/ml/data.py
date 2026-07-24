from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

import pandas as pd
from sklearn.model_selection import train_test_split


SOURCE_FILENAMES = (
    "twitter_human_bots_cleaned.csv",
    "twitter_bot_training_data2_cleaned.csv",
)
RANDOM_STATE = 42


def _normalise_account_id(value: object) -> str | None:
    """Preserve digit IDs and recover integral scientific notation from source CSVs."""

    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not parsed.is_finite() or parsed < 0 or parsed != parsed.to_integral_value():
        return None
    normalised = str(int(parsed))
    if len(normalised) > 19:
        return None
    return normalised


def load_source_data(dataset_dir: Path) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for filename in SOURCE_FILENAMES:
        path = dataset_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required dataset is missing: {path}")
        frames.append(pd.read_csv(path, dtype={"account_id": "string"}))
    return frames


def clean_and_merge(frames: Iterable[pd.DataFrame]) -> tuple[pd.DataFrame, dict[str, int]]:
    """Remove invalid IDs, label conflicts, and deterministic duplicate records."""

    prepared = []
    for source_order, original in enumerate(frames):
        frame = original.copy()
        required = {"account_id", "label", "source_dataset"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
        frame["account_id"] = frame["account_id"].map(_normalise_account_id).astype("string")
        frame["label"] = pd.to_numeric(frame["label"], errors="coerce")
        frame["_source_order"] = source_order
        frame["_row_order"] = range(len(frame))
        prepared.append(frame)

    merged = pd.concat(prepared, ignore_index=True, sort=False)
    valid_id = merged["account_id"].str.fullmatch(r"[0-9]{1,19}", na=False)
    valid_label = merged["label"].isin([0, 1])
    invalid_rows = int((~(valid_id & valid_label)).sum())
    merged = merged.loc[valid_id & valid_label].copy()
    merged["label"] = merged["label"].astype(int)

    label_counts = merged.groupby("account_id", sort=False)["label"].nunique()
    conflicting_ids = label_counts[label_counts > 1].index
    conflict_count = len(conflicting_ids)
    merged = merged.loc[~merged["account_id"].isin(conflicting_ids)].copy()

    completeness = pd.to_numeric(
        merged.get("feature_completeness", pd.Series(index=merged.index, dtype=float)),
        errors="coerce",
    ).fillna(-1.0)
    merged["_completeness_rank"] = completeness
    before_deduplication = len(merged)
    merged = merged.sort_values(
        ["account_id", "_completeness_rank", "_source_order", "_row_order"],
        ascending=[True, False, True, True],
        kind="mergesort",
    ).drop_duplicates(subset=["account_id"], keep="first")
    duplicate_rows_removed = before_deduplication - len(merged)
    merged = merged.drop(
        columns=["_source_order", "_row_order", "_completeness_rank"]
    ).reset_index(drop=True)

    summary = {
        "invalid_rows_removed": invalid_rows,
        "conflicting_account_ids_removed": int(conflict_count),
        "duplicate_rows_removed": int(duplicate_rows_removed),
        "clean_account_count": int(len(merged)),
    }
    return merged, summary


def split_accounts(
    frame: pd.DataFrame,
    random_state: int = RANDOM_STATE,
) -> dict[str, pd.DataFrame]:
    train, remaining = train_test_split(
        frame,
        test_size=0.30,
        random_state=random_state,
        stratify=frame["label"],
    )
    validation, test = train_test_split(
        remaining,
        test_size=0.50,
        random_state=random_state,
        stratify=remaining["label"],
    )
    return {
        "train": train.sort_values("account_id").reset_index(drop=True),
        "validation": validation.sort_values("account_id").reset_index(drop=True),
        "test": test.sort_values("account_id").reset_index(drop=True),
    }


def create_demo_accounts(
    test_frame: pd.DataFrame,
    per_class: int = 50,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    samples = []
    for label in (0, 1):
        candidates = test_frame.loc[test_frame["label"] == label]
        count = min(per_class, len(candidates))
        samples.append(candidates.sample(n=count, random_state=random_state + label))
    demo = pd.concat(samples, ignore_index=True).sample(
        frac=1.0, random_state=random_state
    )
    private_columns = {"label", "quality_flag", "feature_completeness"}
    demo = demo.drop(columns=[c for c in private_columns if c in demo.columns])
    if "label" in demo.columns:
        raise AssertionError("Demo data must never contain the training label.")
    return demo.sort_values("account_id").reset_index(drop=True)


def write_generated_data(
    splits: dict[str, pd.DataFrame],
    demo: pd.DataFrame,
    generated_dir: Path,
) -> None:
    generated_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in splits.items():
        frame.to_csv(generated_dir / f"{name}.csv", index=False)
    demo.to_csv(generated_dir / "demo_accounts.csv", index=False)
