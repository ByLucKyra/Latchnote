"""Claude-based, transcript-grounded note structuring."""


class StructuringError(RuntimeError):
    """Raised when a transcript chunk cannot be structured."""


class ClaudeStructurer:
    """Turn one transcript chunk into concise Markdown bullets."""

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def structure(self, transcript: str) -> str:
        """Return only facts grounded in the supplied transcript."""
        if not transcript.strip():
            return ""
        if not self._api_key:
            raise StructuringError("ANTHROPIC_API_KEY is not configured.")

        try:
            from anthropic import APIConnectionError, APIStatusError, Anthropic
        except ImportError as error:
            raise StructuringError("The Anthropic SDK is not installed.") from error

        try:
            response = Anthropic(api_key=self._api_key).messages.create(
                model=self._model,
                max_tokens=500,
                system=(
                    "Convert the transcript into concise Markdown bullet points. "
                    "Preserve technical terms, proper nouns, and code identifiers exactly. "
                    "Remove filler, false starts, and repetition. "
                    "Never add facts, explanations, or context absent from the transcript. "
                    "Keep Indonesian and English as spoken. Return bullets only, with no heading."
                ),
                messages=[{"role": "user", "content": transcript}],
            )
        except (APIConnectionError, APIStatusError, OSError) as error:
            raise StructuringError(f"Claude structuring failed: {error}") from error

        bullets = "\n".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        ).strip()
        if not bullets:
            raise StructuringError("Claude returned no structured notes.")
        return bullets
