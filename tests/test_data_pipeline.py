import pandas as pd

from backend.ml.data import clean_and_merge, create_demo_accounts, split_accounts


def _row(account_id: str, label: int, completeness: float = 1.0) -> dict:
    return {
        "source_dataset": "fixture",
        "account_id": account_id,
        "label": label,
        "feature_completeness": completeness,
        "account_age_days": 100,
        "followers_count": 10,
        "following_count": 5,
        "tweet_count": 20,
    }


def test_cleaning_removes_conflicts_and_deduplicates_deterministically() -> None:
    first = pd.DataFrame(
        [
            _row("100", 0),
            _row("200", 1, completeness=0.5),
            _row("300", 0),
        ]
    )
    second = pd.DataFrame(
        [
            _row("100", 1),
            _row("200", 1, completeness=0.9),
            _row("bad-id", 0),
        ]
    )

    clean, summary = clean_and_merge([first, second])

    assert clean["account_id"].tolist() == ["200", "300"]
    assert clean.loc[clean["account_id"] == "200", "feature_completeness"].item() == 0.9
    assert summary == {
        "invalid_rows_removed": 1,
        "conflicting_account_ids_removed": 1,
        "duplicate_rows_removed": 1,
        "clean_account_count": 2,
    }


def test_split_and_demo_are_reproducible_and_demo_has_no_label() -> None:
    frame = pd.DataFrame(
        [_row(str(10_000 + index), index % 2) for index in range(200)]
    )
    first = split_accounts(frame)
    second = split_accounts(frame)

    assert {name: len(part) for name, part in first.items()} == {
        "train": 140,
        "validation": 30,
        "test": 30,
    }
    for name in first:
        assert first[name]["account_id"].tolist() == second[name]["account_id"].tolist()
        assert set(first[name]["label"]) == {0, 1}

    demo = create_demo_accounts(first["test"], per_class=5)
    assert len(demo) == 10
    assert "label" not in demo.columns
    assert "quality_flag" not in demo.columns
    assert "feature_completeness" not in demo.columns


def test_scientific_notation_account_ids_are_normalised() -> None:
    clean, summary = clean_and_merge(
        [pd.DataFrame([_row("8.41E+17", 1), _row("123", 0)])]
    )
    assert clean["account_id"].tolist() == ["123", "841000000000000000"]
    assert summary["invalid_rows_removed"] == 0
