"""Shared accepted CREATE-only required-text normalization."""


def trimmed_required_text(value: str, error_message: str) -> str:
    """Trim existing string input and preserve the caller's validation message."""
    result = value.strip()
    if not result:
        raise ValueError(error_message)
    return result
