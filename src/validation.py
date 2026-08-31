from urllib.parse import urlparse

from src.constants import BANNED_WORDS


def https_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
    except (AttributeError, ValueError):
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)


def contains_banned_word(*values: str) -> bool:
    normalized = " ".join(value or "" for value in values).lower().replace(" ", "")
    return any(word in normalized for word in BANNED_WORDS)
