from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator

_current_lang: ContextVar[str] = ContextVar("current_lang", default="en")
_locale_cache: dict[str, dict[str, str]] = {}
_LOCALES_DIR = Path(__file__).parent / "locales"


def _load_locale(lang: str) -> dict[str, str]:
    """Load and cache a locale JSON file. Returns empty dict if file doesn't exist."""
    if lang not in _locale_cache:
        path = _LOCALES_DIR / f"{lang}.json"
        _locale_cache[lang] = json.loads(path.read_text("utf-8")) if path.exists() else {}
    return _locale_cache[lang]


def translate(key: str, lang: str = "en", **kwargs: Any) -> str:
    """Translate a message key to the given language.

    Falls back to English if the key is missing in the requested language.
    Falls back to the key itself if not found in any locale.
    Supports {placeholder} interpolation via kwargs.
    """
    template = _load_locale(lang).get(key) or _load_locale("en").get(key, key)
    return template.format(**kwargs) if kwargs else template


def t(key: str, **kwargs: Any) -> str:
    """Translate using the current request language set by LanguageMiddleware."""
    return translate(key, _current_lang.get(), **kwargs)


def get_request_language(accept_language: str) -> str:
    """Extract the primary language tag from an Accept-Language header value."""
    if not accept_language:
        return "en"
    primary = accept_language.split(",")[0].split(";")[0].strip()
    return primary.split("-")[0].lower() or "en"


@contextmanager
def set_language(lang: str) -> Generator[None, None, None]:
    """Context manager that sets the active language for the current async context."""
    token = _current_lang.set(lang)
    try:
        yield
    finally:
        _current_lang.reset(token)
