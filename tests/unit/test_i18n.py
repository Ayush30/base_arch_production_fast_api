from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import NotFoundError
from app.core.messages import ExampleMsg, HealthMsg, SecurityMsg
from app.i18n import _current_lang, get_request_language, set_language, translate
from app.main import create_app

_EN_JSON = json.loads(
    (Path(__file__).parent.parent.parent / "src/app/i18n/locales/en.json").read_text()
)


def _public_constants(cls: type) -> list[str]:
    return [v for k, v in vars(cls).items() if not k.startswith("_")]


def test_translate_uses_english_catalog_by_default() -> None:
    assert translate(HealthMsg.OK) == "ok"


def test_translate_interpolates_params() -> None:
    assert translate(ExampleMsg.NOT_FOUND, item_id="123") == "ExampleItem 123 not found"


def test_translate_falls_back_to_english_for_unknown_language() -> None:
    assert translate(SecurityMsg.TOKEN_INVALID, lang="zz") == "Invalid or expired token"


def test_translate_returns_key_itself_if_not_found_in_any_locale() -> None:
    assert translate("nonexistent.key") == "nonexistent.key"


def test_get_request_language_parses_en_us() -> None:
    assert get_request_language("en-US,en;q=0.9") == "en"


def test_get_request_language_empty_returns_en() -> None:
    assert get_request_language("") == "en"


def test_set_language_context_manager_restores_previous() -> None:
    with set_language("fr"):
        assert _current_lang.get() == "fr"
    assert _current_lang.get() == "en"


def test_app_error_accepts_message_key() -> None:
    exc = NotFoundError(ExampleMsg.NOT_FOUND, item_id="abc")
    assert exc.message == ExampleMsg.NOT_FOUND
    assert exc.kwargs == {"item_id": "abc"}


@pytest.mark.asyncio
async def test_error_response_uses_translated_message() -> None:
    app = create_app()

    @app.get("/test-i18n-error")
    async def test_i18n_error() -> None:
        raise NotFoundError(ExampleMsg.NOT_FOUND, item_id="abc")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/test-i18n-error", headers={"Accept-Language": "en-US"})

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "ExampleItem abc not found"
    assert "message_key" not in response.json()["error"]


def test_all_message_keys_present_in_en_json() -> None:
    for cls in (HealthMsg, SecurityMsg, ExampleMsg):
        for key in _public_constants(cls):
            assert key in _EN_JSON, f"Missing key in en.json: {key}"


def test_all_en_json_values_are_non_empty_strings() -> None:
    for key, value in _EN_JSON.items():
        assert isinstance(value, str) and value, f"Empty or non-string value for key: {key}"
