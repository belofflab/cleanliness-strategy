"""Тесты криптопримитивов аутентификации (без БД и сети)."""

import asyncio

import jwt
import pytest

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_numeric_code,
    generate_refresh_token,
    hash_password,
    hash_secret,
    verify_password,
    verify_secret,
)
from app.core.config import get_settings
from app.services.sms import send_sms


def test_password_hash_roundtrip():
    h = hash_password("Sup3rSecret!")
    assert h != "Sup3rSecret!"
    assert verify_password("Sup3rSecret!", h)
    assert not verify_password("wrong", h)


def test_secret_hash_is_deterministic_and_verifiable():
    code = "1234"
    hashed = hash_secret(code)
    assert hashed == hash_secret(code)  # детерминирован
    assert verify_secret(code, hashed)
    assert not verify_secret("9999", hashed)


def test_numeric_code_length():
    assert len(generate_numeric_code(4)) == 4
    assert generate_numeric_code(6).isdigit()


def test_refresh_token_is_random():
    assert generate_refresh_token() != generate_refresh_token()


def test_access_token_contains_role_and_type():
    token, expires_in = create_access_token(user_id="abc", role="client")
    assert expires_in > 0
    payload = decode_access_token(token)
    assert payload["sub"] == "abc"
    assert payload["role"] == "client"
    assert payload["type"] == "access"


def test_access_token_signature_validated():
    token, _ = create_access_token(user_id="abc", role="admin")
    # Подмена секрета → невалидная подпись.
    settings = get_settings()
    with pytest.raises(jwt.InvalidTokenError):
        jwt.decode(token, settings.jwt_secret + "x", algorithms=[settings.jwt_algorithm])


def test_sms_mock_mode():
    # Без SMS_RU_API_ID (дефолт настроек) send_sms работает в mock-режиме:
    # возвращает sent=True, mocked=True и ничего не шлёт наружу.
    assert Settings().sms_enabled is False
    result = asyncio.run(send_sms("+79170000000", "Код: 1234"))
    assert result.sent is True
    assert result.mocked is True

