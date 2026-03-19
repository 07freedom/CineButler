"""Configuration loading: YAML + .env for CineButler."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _project_root() -> Path:
    """Resolve project root (where config.yaml lives)."""
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parent.parent.parent,
    ]
    for p in candidates:
        if (p / "config.yaml").exists():
            return p
    return Path.cwd()


def _load_env() -> None:
    """Load .env from project root."""
    root = _project_root()
    load_dotenv(root / ".env", override=False)


# --- Pydantic models ---


class TargetsConfig(BaseModel):
    """Target directories by media type."""

    movie: list[str] = Field(default_factory=list)
    tv: list[str] = Field(default_factory=list)


class ActionsConfig(BaseModel):
    """File operation action per media type: mv | cp | skip."""

    movie: str = "mv"
    tv: str = "mv"
    adult: str = "skip"
    unknown: str = "skip"
    on_duplicate: str = "skip"  # skip | overwrite


class NotificationConfig(BaseModel):
    """Notification settings via OpenClaw."""

    channel: str = "feishu"  # feishu | telegram | slack | ...
    target: str = ""          # channel-specific target ID
    node_bin: str = "/home/tth/.nvm/versions/node/v22.17.0/bin"


class TMDBConfig(BaseModel):
    """TMDB API settings."""

    api_key: str = ""
    language: str = "zh-CN"
    base_url: str = "https://api.themoviedb.org/3"


class CineButlerConfig(BaseModel):
    """Full CineButler configuration."""

    targets: TargetsConfig = Field(default_factory=TargetsConfig)
    actions: ActionsConfig = Field(default_factory=ActionsConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    tmdb: TMDBConfig = Field(default_factory=TMDBConfig)
    file_naming: str = "infuse"  # infuse | raw
    naming_rules: list[str] = Field(default_factory=list)


def load_config(config_path: Path | None = None) -> CineButlerConfig:
    """Load config from YAML, then apply .env overrides."""
    _load_env()

    root = _project_root()
    path = config_path or root / "config.yaml"
    raw: dict = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    config = CineButlerConfig.model_validate(raw)

    # Override TMDB api_key from env if config is empty
    env_tmdb = os.getenv("TMDB_API_KEY", "")
    if env_tmdb and not config.tmdb.api_key:
        config.tmdb.api_key = env_tmdb

    # Override TMDB base_url from env
    env_tmdb_base = os.getenv("TMDB_BASE_URL", "").strip().rstrip("/")
    if env_tmdb_base:
        config.tmdb.base_url = env_tmdb_base

    return config
