"""DTO служебных эндпоинтов: health, метрики, вебхуки."""

from __future__ import annotations

from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str  # ok | error
    database: str  # ok | down
    timestamp: str


class ReadinessOut(BaseModel):
    status: str  # ok | degraded
    database: str
    redis: str


class MetricsOut(BaseModel):
    requests_total: int
    requests_by_status_class: dict[str, int]
    errors_total: int
    avg_duration_ms: float


class CallWebhookResult(BaseModel):
    """Ответ вебхуку Calltracking: событие сохранено / дубликат."""

    status: str  # created | duplicate
    call_event_id: str
    lead_id: str | None = None
    lead_created: bool = False
