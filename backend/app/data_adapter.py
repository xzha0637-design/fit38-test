from pathlib import Path
from typing import Any

import pandas as pd


class DatasetAdapter:
    """Local replacement for Module A while live X API access is out of scope."""

    def __init__(self, demo_data_path: Path) -> None:
        self.demo_data_path = Path(demo_data_path)
        self.ready = False
        self.error: str | None = None
        self._accounts: pd.DataFrame | None = None
        self.load()

    def load(self) -> None:
        try:
            if not self.demo_data_path.is_file():
                raise FileNotFoundError(f"Demo data not found: {self.demo_data_path}")
            frame = pd.read_csv(
                self.demo_data_path,
                dtype={"account_id": "string"},
            )
            if "account_id" not in frame.columns:
                raise ValueError("Demo data does not contain account_id.")
            if "label" in frame.columns:
                raise ValueError("Demo data must not expose the training label.")
            frame["account_id"] = frame["account_id"].astype("string").str.strip()
            if frame["account_id"].duplicated().any():
                raise ValueError("Demo data contains duplicate account IDs.")
            self._accounts = frame.set_index("account_id", drop=False)
            self.ready = True
            self.error = None
        except Exception as exc:
            self._accounts = None
            self.ready = False
            self.error = str(exc)

    @property
    def account_count(self) -> int:
        return 0 if self._accounts is None else int(len(self._accounts))

    def get_account(self, account_id: str) -> dict[str, Any] | None:
        if not self.ready or self._accounts is None:
            return None
        if account_id not in self._accounts.index:
            return None
        row = self._accounts.loc[account_id]
        return row.to_dict()

    def list_accounts(self, limit: int) -> list[dict[str, str | None]]:
        if not self.ready or self._accounts is None:
            return []
        output: list[dict[str, str | None]] = []
        for record in self._accounts.head(limit).to_dict(orient="records"):
            output.append(
                {
                    "account_id": str(record["account_id"]),
                    "source_dataset": self._optional_text(record.get("source_dataset")),
                    "username": self._optional_text(record.get("username")),
                }
            )
        return output

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        if value is None or pd.isna(value):
            return None
        text = str(value).strip()
        return text or None
