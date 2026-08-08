from collections.abc import Mapping
from typing import Any

import pandas as pd

from backend.app.schemas import (
    AccountPreview,
    PublicActivity,
    PublicNetwork,
    PublicProfile,
)


MISSING_LABELS = {
    "username": "Username",
    "description": "Profile description",
    "location": "Location",
    "account_age_days": "Account age",
    "tweet_count": "Post count",
    "posts_per_day": "Posts per day",
    "followers_count": "Follower count",
    "following_count": "Following count",
}


def _text(value: Any) -> str | None:
    """Normalise one optional public text value without inventing content."""

    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() in {"unknown", "none", "n/a", "na"}:
        return None
    return text


def _number(value: Any) -> float | None:
    """Return one finite non-negative public number or ``None``."""

    if value is None or pd.isna(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def build_public_preview(record: Mapping[str, Any]) -> AccountPreview:
    """Return only the approved public fields used by the assessment."""

    account_age = _number(record.get("account_age_days"))
    post_count = _number(record.get("tweet_count"))
    posts_per_day = None
    if account_age and post_count is not None:
        posts_per_day = round(post_count / account_age, 2)

    values = {
        "username": _text(record.get("username")),
        "description": _text(record.get("description")),
        "location": _text(record.get("location")),
        "account_age_days": int(account_age) if account_age is not None else None,
        "tweet_count": int(post_count) if post_count is not None else None,
        "posts_per_day": posts_per_day,
        "followers_count": (
            int(value) if (value := _number(record.get("followers_count"))) is not None else None
        ),
        "following_count": (
            int(value) if (value := _number(record.get("following_count"))) is not None else None
        ),
    }
    missing = [MISSING_LABELS[key] for key, value in values.items() if value is None]
    username = values["username"]
    return AccountPreview(
        account_id=str(record["account_id"]),
        display_identifier=f"@{username}" if username else str(record["account_id"]),
        profile=PublicProfile(
            username=username,
            description=values["description"],
            location=values["location"],
        ),
        activity=PublicActivity(
            account_age_days=values["account_age_days"],
            post_count=values["tweet_count"],
            posts_per_day=values["posts_per_day"],
        ),
        network=PublicNetwork(
            followers_count=values["followers_count"],
            following_count=values["following_count"],
        ),
        missing_fields=missing,
    )
