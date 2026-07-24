from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


NUMERIC_FEATURES = [
    "account_age_days",
    "followers_count",
    "following_count",
    "follower_following_ratio",
    "tweet_count",
    "posting_frequency",
    "description_length",
    "username_length",
    "profile_completeness",
]
BOOLEAN_FEATURES = ["verified", "uses_default_profile_image", "has_description"]
FEATURE_NAMES = NUMERIC_FEATURES + BOOLEAN_FEATURES
MINIMUM_COMPLETENESS = 0.5


@dataclass(frozen=True)
class FeatureResult:
    frame: pd.DataFrame
    completeness: float
    usable_feature_count: int


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _number(value: Any, *, positive: bool = False) -> float:
    if _is_missing(value):
        return np.nan
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return np.nan
    if not np.isfinite(parsed) or parsed < 0 or (positive and parsed <= 0):
        return np.nan
    return parsed


def _boolean(value: Any) -> float:
    if _is_missing(value):
        return np.nan
    if isinstance(value, (bool, np.bool_)):
        return float(value)
    if isinstance(value, (int, float)) and value in (0, 1):
        return float(value)
    normalised = str(value).strip().lower()
    if normalised in {"true", "t", "yes", "y", "1"}:
        return 1.0
    if normalised in {"false", "f", "no", "n", "0"}:
        return 0.0
    return np.nan


def _text_length(record: Mapping[str, Any], text_key: str, length_key: str) -> float:
    supplied = _number(record.get(length_key))
    if not np.isnan(supplied):
        return supplied
    value = record.get(text_key)
    if _is_missing(value):
        return np.nan
    return float(len(str(value).strip()))


def _present(value: Any, *, unknown_is_missing: bool = False) -> float:
    if _is_missing(value):
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    if unknown_is_missing and text.lower() in {"unknown", "none", "n/a", "na"}:
        return 0.0
    return 1.0


def _profile_completeness(record: Mapping[str, Any], default_image: float) -> float:
    indicators = [
        _present(record.get("username")),
        _present(record.get("description")),
        _present(record.get("location"), unknown_is_missing=True),
    ]
    if not np.isnan(default_image):
        indicators.append(1.0 - default_image)
    if not indicators:
        return np.nan
    return float(np.mean(indicators))


def build_feature_row(record: Mapping[str, Any]) -> FeatureResult:
    """Map one cleaned dataset record into the deployable feature schema."""

    age = _number(record.get("account_age_days"), positive=True)
    followers = _number(record.get("followers_count"))
    following = _number(record.get("following_count"))
    tweets = _number(record.get("tweet_count"))

    ratio = np.nan
    if not np.isnan(followers) and not np.isnan(following):
        ratio = (followers + 1.0) / (following + 1.0)
    else:
        ratio = _number(record.get("followers_following_ratio"))

    frequency = np.nan
    if not np.isnan(tweets) and not np.isnan(age):
        frequency = tweets / age
    else:
        frequency = _number(record.get("tweets_per_day"))

    default_image = _boolean(record.get("default_profile_image"))
    description_length = _text_length(record, "description", "description_length")
    username_length = _text_length(record, "username", "username_length")
    if "description" in record or "description_length" in record:
        has_description = (
            1.0 if not np.isnan(description_length) and description_length > 0 else 0.0
        )
    else:
        has_description = np.nan

    values = {
        "account_age_days": age,
        "followers_count": followers,
        "following_count": following,
        "follower_following_ratio": ratio,
        "tweet_count": tweets,
        "posting_frequency": frequency,
        "description_length": description_length,
        "username_length": username_length,
        "profile_completeness": _profile_completeness(record, default_image),
        "verified": _boolean(record.get("verified")),
        "uses_default_profile_image": default_image,
        "has_description": has_description,
    }
    frame = pd.DataFrame([values], columns=FEATURE_NAMES, dtype=float)
    usable = int(frame.notna().sum(axis=1).iloc[0])
    return FeatureResult(
        frame=frame,
        completeness=usable / len(FEATURE_NAMES),
        usable_feature_count=usable,
    )


def build_feature_matrix(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    results = [build_feature_row(row) for row in frame.to_dict(orient="records")]
    matrix = pd.concat([result.frame for result in results], ignore_index=True)
    completeness = pd.Series(
        [result.completeness for result in results],
        index=frame.index,
        name="runtime_feature_completeness",
        dtype=float,
    )
    return matrix, completeness


def is_sufficient(completeness: float) -> bool:
    return completeness >= MINIMUM_COMPLETENESS
