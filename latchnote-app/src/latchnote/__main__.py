"""Create a local Latchnote session file."""

import argparse
import logging

from .config import load_settings
from .session import Session, SessionStatus
from .writer import MarkdownWriter


def main() -> None:
    """Create an empty Markdown note for a named session."""
    parser = argparse.ArgumentParser(description="Create a Latchnote session.")
    parser.add_argument("title", help="Title for this study session")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    session = Session(title=args.title, status=SessionStatus.RECORDING)
    writer = MarkdownWriter(load_settings().notes_dir, session)
    logging.info("Created session note: %s", writer.path)


if __name__ == "__main__":
    main()
