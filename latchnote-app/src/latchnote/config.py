"""Local application configuration."""

from dataclasses import dataclass
from os import getenv
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Paths and optional API credentials read from the environment."""

    notes_dir: Path
    data_dir: Path
    deepgram_api_key: str | None
    anthropic_api_key: str | None


def load_settings() -> Settings:
    """Load settings without writing or logging credentials."""
    return Settings(
        notes_dir=Path(getenv("LATCHNOTE_NOTES_DIR", "notes")),
        data_dir=Path(getenv("LATCHNOTE_DATA_DIR", "data")),
        deepgram_api_key=getenv("DEEPGRAM_API_KEY") or None,
        anthropic_api_key=getenv("ANTHROPIC_API_KEY") or None,
    )
