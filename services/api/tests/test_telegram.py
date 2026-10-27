"""Тесты Telegram fast-response (Этап 3.3): mock-режим и формат сообщения."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.telegram import _format_lead, send_message


async def test_send_message_mock_when_disabled():
    """Без токена/чата отправка не падает и честно возвращает False (mock)."""
    assert await send_message("проверка") is False


def test_format_lead_has_contact_and_city():
    lead = SimpleNamespace(
        name="Иван",
        phone="+79170000000",
        source="calculator",
        context="Генеральная: 2 комн.",
        city=SimpleNamespace(name="Тюмень"),
    )
    text = _format_lead(lead)
    assert "Иван" in text
    assert 'tel:+79170000000' in text
    assert "Тюмень" in text
    assert "calculator" in text
    assert "1–2 минут" in text


def test_format_lead_escapes_html():
    """Пользовательский ввод не должен ломать HTML-разметку сообщения."""
    lead = SimpleNamespace(
        name="<b>hack</b>",
        phone="+70000000000",
        source="hero",
        context="<script>alert(1)</script>",
        city=None,
    )
    text = _format_lead(lead)
    assert "<b>hack</b>" not in text
    assert "&lt;b&gt;hack&lt;/b&gt;" in text
    assert "<script>" not in text
