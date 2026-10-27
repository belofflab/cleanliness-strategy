"""Тесты нормализации вебхука Calltracking (чистая логика, без БД и сети)."""

import pytest

from app.services.calltracking import (
    CallWebhookError,
    build_call_context,
    parse_call_payload,
    resolve_city_slug,
)


def test_parse_standard_json_payload():
    call = parse_call_payload(
        {
            "call_id": "abc-123",
            "phone": "8 (917) 123-45-67",
            "called_number": "+7 999 000-00-01",
            "duration": "95",
            "status": "answered",
            "record_url": "https://ct.example/rec/1.mp3",
            "utm_source": "yandexpoisk",
            "utm_campaign": "12345",
            "utm_term": "клининг тюмень",
            "ym_uid": "17222223333444455",
            "yclid": "y-777",
            "site": "cleanliness.pro",
        }
    )
    assert call.external_id == "abc-123"
    assert call.caller_phone == "+79171234567"       # нормализация 8 → +7
    assert call.tracked_phone == "+79990000001"
    assert call.duration_seconds == 95
    assert call.status == "answered"
    assert call.record_url == "https://ct.example/rec/1.mp3"
    assert call.utm == {"source": "yandexpoisk", "campaign": "12345", "term": "клининг тюмень"}
    assert call.ym_uid == "17222223333444455"
    assert call.yclid == "y-777"


def test_parse_synonym_fields_and_nested_utm():
    # Другая версия кабинета: caller/dst/talk_time/link_record + вложенный utm.
    call = parse_call_payload(
        {
            "id": "42",
            "caller": "+79273334455",
            "dst": "+79990000002",
            "talk_time": "12.0",
            "link_record": "https://ct.example/rec/42.wav",
            "utm": {"source": "vkgroup", "medium": "social"},
            "clientid": "555666",
        }
    )
    assert call.external_id == "42"
    assert call.caller_phone == "+79273334455"
    assert call.duration_seconds == 12
    assert call.record_url == "https://ct.example/rec/42.wav"
    assert call.utm["source"] == "vkgroup"
    assert call.utm["medium"] == "social"
    assert call.ym_uid == "555666"


def test_parse_requires_caller_phone():
    with pytest.raises(CallWebhookError):
        parse_call_payload({"duration": "10"})


def test_resolve_city_by_number_map(monkeypatch):
    from app.core import config

    settings = config.Settings(
        calltracking_city_numbers='{"+7 999 000-00-02": "ufa"}'
    )
    monkeypatch.setattr("app.services.calltracking.get_settings", lambda: settings)

    call = parse_call_payload({"phone": "+79170000000", "called": "+79990000002"})
    assert resolve_city_slug(call) == "ufa"


def test_resolve_city_by_domain(monkeypatch):
    from app.core import config

    settings = config.Settings(default_city_slug="ufa", public_base_domain="cleanliness.pro")
    monkeypatch.setattr("app.services.calltracking.get_settings", lambda: settings)

    call = parse_call_payload({"phone": "+79170000000", "site": "tyumen.cleanliness.pro"})
    assert resolve_city_slug(call) == "tyumen"

    call_ufa = parse_call_payload({"phone": "+79170000000", "site": "ufa.cleanliness.pro"})
    assert resolve_city_slug(call_ufa) == "ufa"

    # Apex-домен, служебный поддомен и чужой домен → город по умолчанию.
    for site in ("cleanliness.pro", "www.cleanliness.pro", "example.com", ""):
        call_default = parse_call_payload({"phone": "+79170000000", "site": site})
        assert resolve_city_slug(call_default) == "ufa", site


def test_call_context_contains_essentials():
    call = parse_call_payload(
        {
            "phone": "+79170000000",
            "duration": "125",
            "status": "answered",
            "record": "https://ct.example/r.mp3",
        }
    )
    context = build_call_context(call)
    assert "Входящий звонок" in context
    assert "02:05" in context
    assert "https://ct.example/r.mp3" in context
