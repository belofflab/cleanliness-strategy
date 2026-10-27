"""Нормализация телефонов (общая для CRM, аутентификации и коллтрекинга)."""

import re


def normalize_phone(phone: str) -> str:
    """Приводит телефон к виду +7XXXXXXXXXX (оставляем + и цифры)."""
    digits = re.sub(r"[^\d+]", "", phone)
    digits = digits.lstrip("+")
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return "+" + digits if digits else ""
