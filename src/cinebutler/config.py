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
    base_url: str = "https://api.themoviedb.org/3"


class CineButlerConfig(BaseModel):
    """Full CineButler configuration."""

    placement_rules: PlacementRules = Field(default_factory=PlacementRules)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    tmdb: TMDBConfig = Field(default_factory=TMDBConfig)
    file_op_mode: str = "cp"  # cp | mv


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

    import os

    # Override TMDB api_key from env if config is empty
    env_tmdb = os.getenv("TMDB_API_KEY", "")
    if env_tmdb and not config.tmdb.api_key:
        config.tmdb.api_key = env_tmdb

    # Override TMDB base_url from env
    env_tmdb_base = os.getenv("TMDB_BASE_URL", "").strip().rstrip("/")
    if env_tmdb_base:
        config.tmdb.base_url = env_tmdb_base

    # FILE_OP_MODE: cp (default) or mv
    env_file_op = os.getenv("FILE_OP_MODE", "").strip().lower()
    if env_file_op in ("cp", "mv"):
        config.file_op_mode = env_file_op

    return config
