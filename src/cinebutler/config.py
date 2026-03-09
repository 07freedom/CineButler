"""Configuration loading: YAML + .env for CineButler."""

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


# --- Pydantic models for config ---


class PlacementRule(BaseModel):
    """Placement rule for a media type."""

    targets: list[str] = Field(default_factory=list)
    action: str = "move"  # move | skip


class PlacementRules(BaseModel):
    """All placement rules."""

    movie: PlacementRule = Field(default_factory=lambda: PlacementRule(targets=[]))
    tv: PlacementRule = Field(default_factory=lambda: PlacementRule(targets=[]))
    adult: PlacementRule = Field(default_factory=lambda: PlacementRule(action="skip"))


class NotificationConfig(BaseModel):
    """Notification settings."""

    feishu_target: str = ""
    node_bin: str = "/home/tth/.nvm/versions/node/v22.17.0/bin"


class TMDBConfig(BaseModel):
    """TMDB API settings."""

    api_key: str = ""
    language: str = "zh-CN"


class CineButlerConfig(BaseModel):
    """Full CineButler configuration."""

    placement_rules: PlacementRules = Field(default_factory=PlacementRules)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    tmdb: TMDBConfig = Field(default_factory=TMDBConfig)


def load_config(config_path: Path | None = None) -> CineButlerConfig:
    """Load config from YAML, override with .env."""
    _load_env()

    root = _project_root()
    path = config_path or root / "config.yaml"
    raw: dict = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    config = CineButlerConfig.model_validate(raw)

    # Override TMDB api_key from env if config is empty
    import os
    env_tmdb = os.getenv("TMDB_API_KEY", "")
    if env_tmdb and not config.tmdb.api_key:
        config.tmdb.api_key = env_tmdb

    return config
