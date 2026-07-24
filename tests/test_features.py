import math

import numpy as np

from backend.ml.features import FEATURE_NAMES, build_feature_row, is_sufficient


def test_feature_mapping_handles_zero_following_without_division_error() -> None:
    result = build_feature_row(
        {
            "account_age_days": 10,
            "followers_count": 100,
            "following_count": 0,
            "tweet_count": 50,
            "verified": False,
            "default_profile_image": True,
            "description": "profile text",
            "description_length": 12,
            "username": "demo_user",
            "username_length": 9,
            "location": "Melbourne",
        }
    )

    row = result.frame.iloc[0]
    assert result.frame.columns.tolist() == FEATURE_NAMES
    assert row["follower_following_ratio"] == 101.0
    assert row["posting_frequency"] == 5.0
    assert row["has_description"] == 1.0
    assert result.completeness == 1.0


def test_invalid_values_become_missing_instead_of_infinite() -> None:
    result = build_feature_row(
        {
            "account_age_days": 0,
            "followers_count": -1,
            "following_count": "not-a-number",
            "tweet_count": math.inf,
            "verified": None,
            "default_profile_image": None,
        }
    )
    values = result.frame.to_numpy(dtype=float)
    assert not np.isinf(values).any()
    assert result.completeness < 0.5


def test_completeness_boundary_accepts_exactly_half() -> None:
    assert is_sufficient(0.5)
    assert not is_sufficient(0.499999)
