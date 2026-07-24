from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BOT_RISK_",
        extra="ignore",
    )

    artifact_dir: Path = PROJECT_ROOT / "models" / "xgb-offline-v1"
    demo_data_path: Path = (
        PROJECT_ROOT / "data" / "fixtures" / "demo_accounts.csv"
    )
    database_path: Path = PROJECT_ROOT / "backend" / "runtime" / "feedback.sqlite3"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    log_level: str = "INFO"
    authorised_roles: str = "analyst,admin"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def authorised_role_set(self) -> set[str]:
        return {
            role.strip().lower()
            for role in self.authorised_roles.split(",")
            if role.strip()
        }
