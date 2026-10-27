"""Страховочные тесты машины статусов заказа (без БД).

Фиксируют текущие допустимые переходы: расширение статусов в Stage 2
(accepted/en_route/arrived/verification) не должно сломать legacy-переходы,
на которые опираются админ-CRM и мобильное приложение v1.
"""

from __future__ import annotations

import pytest

from app.api.v1.mobile import MASTER_ALLOWED_TARGETS
from app.models.orders import (
    ORDER_ASSIGNED,
    ORDER_CANCELLED,
    ORDER_DONE,
    ORDER_IN_PROGRESS,
    ORDER_NEW,
    ORDER_STATUSES,
    ORDER_TRANSITIONS,
    Order,
)
from app.services.orders import OrderError, change_status

# Переходы, которые обязаны оставаться разрешёнными (обратная совместимость).
LEGACY_TRANSITIONS = {
    ORDER_NEW: {ORDER_ASSIGNED, ORDER_CANCELLED},
    ORDER_ASSIGNED: {ORDER_IN_PROGRESS, ORDER_CANCELLED, ORDER_NEW},
    ORDER_IN_PROGRESS: {ORDER_DONE, ORDER_CANCELLED},
    ORDER_DONE: set(),
    ORDER_CANCELLED: set(),
}


def test_every_status_has_transition_entry():
    assert set(ORDER_TRANSITIONS) == set(ORDER_STATUSES)


def test_transitions_target_only_known_statuses():
    for source, targets in ORDER_TRANSITIONS.items():
        assert targets <= set(ORDER_STATUSES), source


@pytest.mark.parametrize("source,targets", LEGACY_TRANSITIONS.items())
def test_legacy_transitions_remain_allowed(source, targets):
    assert targets <= ORDER_TRANSITIONS[source]


def test_terminal_statuses_have_no_exits():
    assert ORDER_TRANSITIONS[ORDER_DONE] == set()
    assert ORDER_TRANSITIONS[ORDER_CANCELLED] == set()


@pytest.mark.parametrize(
    "source,target",
    [
        (ORDER_NEW, ORDER_DONE),
        (ORDER_NEW, ORDER_IN_PROGRESS),
        (ORDER_DONE, ORDER_NEW),
        (ORDER_DONE, ORDER_IN_PROGRESS),
        (ORDER_CANCELLED, ORDER_ASSIGNED),
        (ORDER_IN_PROGRESS, ORDER_ASSIGNED),
        (ORDER_ASSIGNED, ORDER_DONE),
    ],
)
async def test_change_status_rejects_invalid_transition(source, target):
    # Проверка перехода выполняется до обращения к репозиторию — БД не нужна.
    order = Order(status=source)
    with pytest.raises(OrderError):
        await change_status(None, order, target)
    assert order.status == source


def test_master_mobile_targets_are_start_and_finish_only():
    # Клинер из мобайла может только начать и завершить уборку; отмена — за менеджером.
    assert MASTER_ALLOWED_TARGETS == {ORDER_IN_PROGRESS, ORDER_DONE}
    reachable = set().union(*ORDER_TRANSITIONS.values())
    assert MASTER_ALLOWED_TARGETS <= reachable
