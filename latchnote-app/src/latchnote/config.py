"""Local application configuration."""

from dataclasses import dataclass
from os import environ, getenv
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Paths and optional API credentials read from the environment."""

    notes_dir: Path
    data_dir: Path
    deepgram_api_key: str | None
    anthropic_api_key: str | None
    anthropic_model: str


def load_settings() -> Settings:
    """Load settings without writing or logging credentials."""
    _load_dotenv(Path(".env"))
    return Settings(
        notes_dir=Path(getenv("LATCHNOTE_NOTES_DIR", "notes")),
        data_dir=Path(getenv("LATCHNOTE_DATA_DIR", "data")),
        deepgram_api_key=getenv("DEEPGRAM_API_KEY") or None,
        anthropic_api_key=getenv("ANTHROPIC_API_KEY") or None,
        anthropic_model=getenv("ANTHROPIC_MODEL", "claude-sonnet-5"),
    )


def _load_dotenv(path: Path) -> None:
    """Load simple ``KEY=value`` lines without overriding real environment values."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key and not key.startswith("#"):
            environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
