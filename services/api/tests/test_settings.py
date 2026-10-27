"""Валидация секретов в настройках и раздельные ключи хешей токенов."""

from __future__ import annotations

import warnings

import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_JWT_SECRET, Settings
from app.core.security import hash_secret, legacy_hash_secret, verify_secret

STRONG = "s" * 64


def test_development_accepts_default_secret():
    assert Settings(environment="development", jwt_secret=DEFAULT_JWT_SECRET).jwt_secret


def test_production_rejects_default_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret=DEFAULT_JWT_SECRET)


def test_production_warns_on_short_jwt_and_missing_token_secret():
    with pytest.warns(UserWarning) as record:
        Settings(environment="production", jwt_secret="short-secret", token_hmac_secret="")
    messages = " ".join(str(w.message) for w in record)
    assert "JWT_SECRET короче" in messages
    assert "TOKEN_HMAC_SECRET" in messages


def test_production_is_silent_with_strong_secrets():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        Settings(environment="production", jwt_secret=STRONG, token_hmac_secret="t" * 64)


def test_hash_secret_uses_token_key_and_keeps_legacy_hash(monkeypatch):
    shared = Settings(jwt_secret="j" * 32)
    split = Settings(jwt_secret="j" * 32, token_hmac_secret="t" * 32)

    monkeypatch.setattr("app.core.security.get_settings", lambda: shared)
    legacy = hash_secret("refresh-token")
    assert legacy_hash_secret("refresh-token") is None  # отдельного ключа нет

    monkeypatch.setattr("app.core.security.get_settings", lambda: split)
    assert hash_secret("refresh-token") != legacy
    # Токены, выданные под старым ключом, по-прежнему можно найти.
    assert legacy_hash_secret("refresh-token") == legacy
    assert verify_secret("refresh-token", hash_secret("refresh-token"))
