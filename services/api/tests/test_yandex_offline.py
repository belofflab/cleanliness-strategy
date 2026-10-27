"""Тесты офлайн-конверсий Яндекс.Метрики (чистая сборка CSV + mock-режим)."""

import asyncio

from app.services.yandex_offline import build_conversion_csv, upload_conversion


def test_csv_prefers_client_id():
    result = build_conversion_csv(
        target="CleaningDone",
        ym_uid="123456789",
        yclid="y-1",
        price=8900.0,
        timestamp=1754500000,
    )
    assert result is not None
    client_id_type, csv_text = result
    assert client_id_type == "CLIENT_ID"
    assert csv_text.splitlines()[0] == "ClientId,Target,DateTime,Price,Currency"
    assert csv_text.splitlines()[1] == "123456789,CleaningDone,1754500000,8900.00,RUB"


def test_csv_falls_back_to_yclid():
    result = build_conversion_csv(
        target="CleaningDone",
        ym_uid=None,
        yclid="y-42",
        price=None,
        timestamp=1754500000,
    )
    assert result is not None
    client_id_type, csv_text = result
    assert client_id_type == "YCLID"
    assert csv_text.splitlines()[0] == "Yclid,Target,DateTime,Price,Currency"
    assert csv_text.splitlines()[1] == "y-42,CleaningDone,1754500000,,"


def test_csv_none_without_identifiers():
    assert (
        build_conversion_csv(target="CleaningDone", ym_uid=None, yclid=None, price=10)
        is None
    )


def test_upload_mock_mode_without_token(monkeypatch):
    from app.core import config

    monkeypatch.setattr(
        "app.services.yandex_offline.get_settings", lambda: config.Settings()
    )
    result = asyncio.run(
        upload_conversion(target="CleaningDone", ym_uid="1", yclid=None, price=100.0)
    )
    # Без токена ничего не отправляется наружу — mock с готовым CSV.
    assert result["status"] == "mocked"
    assert "CleaningDone" in result["csv"]


def test_upload_skips_without_identifiers(monkeypatch):
    from app.core import config

    monkeypatch.setattr(
        "app.services.yandex_offline.get_settings", lambda: config.Settings()
    )
    result = asyncio.run(
        upload_conversion(target="CleaningDone", ym_uid=None, yclid=None, price=None)
    )
    assert result["status"] == "skipped"
