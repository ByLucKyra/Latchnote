"""Local application configuration."""

from dataclasses import dataclass
from os import environ, getenv
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Paths and optional API credentials read from the environment."""

    notes_dir: Path
    data_dir: Path
    whisper_model: str = "base"
    whisper_language: str | None = None
    whisper_threads: int = 2
    whisper_window_seconds: int = 5
    notes_ai_base_url: str = ""
    notes_ai_api_key: str = ""
    notes_ai_model: str = ""
    notes_format_path: Path | None = None


def load_settings() -> Settings:
    """Load settings without writing or logging credentials."""
    _load_dotenv(Path(".env"))
    return Settings(
        notes_dir=Path(getenv("LATCHNOTE_NOTES_DIR", "notes")),
        data_dir=Path(getenv("LATCHNOTE_DATA_DIR", "data")),
        whisper_model=getenv("LATCHNOTE_WHISPER_MODEL", "base"),
        whisper_language=getenv("LATCHNOTE_WHISPER_LANGUAGE") or None,
        whisper_threads=_positive_int("LATCHNOTE_WHISPER_THREADS", 2, 16),
        whisper_window_seconds=_positive_int("LATCHNOTE_WHISPER_WINDOW_SECONDS", 5, 30),
        notes_ai_base_url=getenv("NOTES_AI_BASE_URL", ""),
        notes_ai_api_key=getenv("NOTES_AI_API_KEY", ""),
        notes_ai_model=getenv("NOTES_AI_MODEL", ""),
        notes_format_path=Path(getenv("LATCHNOTE_NOTES_FORMAT")) if getenv("LATCHNOTE_NOTES_FORMAT") else None,
    )


def _positive_int(name: str, default: int, maximum: int) -> int:
    value = int(getenv(name, str(default)))
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}.")
    return value


def _load_dotenv(path: Path) -> None:
    """Load simple ``KEY=value`` lines without overriding real environment values."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key and not key.startswith("#"):
            environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
