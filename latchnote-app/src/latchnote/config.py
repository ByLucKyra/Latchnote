"""Local application configuration."""

from dataclasses import dataclass
from os import environ
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


def load_settings(config_path: Path = Path(".env")) -> Settings:
    """Reload one explicit dotenv file, with process environment taking precedence."""
    values = _read_dotenv(config_path)
    values.update(environ)
    return Settings(
        notes_dir=Path(values.get("LATCHNOTE_NOTES_DIR", "notes")),
        data_dir=Path(values.get("LATCHNOTE_DATA_DIR", "data")),
        whisper_model=values.get("LATCHNOTE_WHISPER_MODEL", "base"),
        whisper_language=values.get("LATCHNOTE_WHISPER_LANGUAGE") or None,
        whisper_threads=_positive_int(values, "LATCHNOTE_WHISPER_THREADS", 2, 16),
        whisper_window_seconds=_positive_int(values, "LATCHNOTE_WHISPER_WINDOW_SECONDS", 5, 30),
        notes_ai_base_url=values.get("NOTES_AI_BASE_URL", ""),
        notes_ai_api_key=values.get("NOTES_AI_API_KEY", ""),
        notes_ai_model=values.get("NOTES_AI_MODEL", ""),
        notes_format_path=Path(values["LATCHNOTE_NOTES_FORMAT"]) if values.get("LATCHNOTE_NOTES_FORMAT") else None,
    )


def _positive_int(values: dict[str, str], name: str, default: int, maximum: int) -> int:
    value = int(values.get(name, str(default)))
    if not 1 <= value <= maximum:
        raise ValueError(f"{name} must be between 1 and {maximum}.")
    return value


def _read_dotenv(path: Path) -> dict[str, str]:
    """Read simple ``KEY=value`` lines without mutating process environment."""
    values = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key and not key.startswith("#"):
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values
