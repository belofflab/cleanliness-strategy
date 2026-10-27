"""ORM-модели платформы.

Импорт всех моделей здесь нужен, чтобы Alembic видел их в Base.metadata
(autogenerate) и чтобы они регистрировались при импорте пакета.
"""

from app.models.auth import OtpCode, RefreshToken, User
from app.models.calls import CallEvent
from app.models.catalog import AddonService, Branch, City, Master, MasterSchedule, Service
from app.models.finance import FinanceEntry
from app.models.integrations import PushToken
from app.models.marketing import Promotion
from app.models.media import BeforeAfterPair, Media
from app.models.notifications import Notification
from app.models.orders import Lead, Order
from app.models.reviews import Review, ReviewSource

__all__ = [
    "City",
    "Service",
    "AddonService",
    "Branch",
    "Master",
    "MasterSchedule",
    "Lead",
    "Order",
    "FinanceEntry",
    "Notification",
    "Promotion",
    "Media",
    "BeforeAfterPair",
    "Review",
    "ReviewSource",
    "PushToken",
    "CallEvent",
    "User",
    "OtpCode",
    "RefreshToken",
]

