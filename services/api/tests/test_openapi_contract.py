"""Контракт API: снимок маршрутов и operationId + требования к схемам.

Снимок `tests/openapi_contract.json` фиксирует все публичные маршруты, на которые
опираются лендинг, админ-CRM и mobile v1. Удаление или переименование маршрута
ломает тест — это защита обратной совместимости. Новые маршруты добавляются
осознанно: обновите снимок командой

    UPDATE_OPENAPI_SNAPSHOT=1 pytest tests/test_openapi_contract.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.main import app

SNAPSHOT = Path(__file__).parent / "openapi_contract.json"


def _current_contract() -> dict[str, str]:
    spec = app.openapi()
    contract: dict[str, str] = {}
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            contract[f"{method.upper()} {path}"] = operation.get("operationId", "")
    return dict(sorted(contract.items()))


def test_contract_matches_snapshot():
    current = _current_contract()
    if os.environ.get("UPDATE_OPENAPI_SNAPSHOT"):
        SNAPSHOT.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))

    removed = sorted(set(expected) - set(current))
    assert not removed, f"Удалены/переименованы маршруты (ломает клиентов): {removed}"

    renamed = {k: (expected[k], current[k]) for k in expected if k in current and expected[k] != current[k]}
    assert not renamed, f"Изменены operationId (ломает сгенерированные клиенты): {renamed}"

    added = sorted(set(current) - set(expected))
    assert not added, f"Новые маршруты — обновите снимок (UPDATE_OPENAPI_SNAPSHOT=1): {added}"


def test_operation_ids_are_present_and_unique():
    spec = app.openapi()
    ids = [
        operation["operationId"]
        for methods in spec["paths"].values()
        for operation in methods.values()
    ]
    assert all(ids), "у каждого маршрута должен быть operationId"
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicates, f"Дублирующиеся operationId: {duplicates}"


def test_success_responses_have_schemas():
    """У каждого маршрута (кроме 204) успешный ответ описан схемой (response_model)."""
    spec = app.openapi()
    missing = []
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            responses = operation.get("responses", {})
            success = next((code for code in ("200", "201") if code in responses), None)
            if success is None:
                assert "204" in responses, f"{method.upper()} {path}: нет успешного ответа"
                continue
            schema = responses[success].get("content", {}).get("application/json", {}).get("schema")
            if not schema:
                missing.append(f"{method.upper()} {path}")
    assert not missing, f"Маршруты без схемы успешного ответа: {missing}"
