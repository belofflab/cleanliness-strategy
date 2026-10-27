"""Сборка всех роутеров API v1 в один router.

В следующих блоках сюда добавятся: pricing, leads, catalog, booking.
"""

from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    booking,
    content,
    health,
    integrations,
    leads,
    mobile,
    pricing,
    reviews,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
# Вебхук динамического коллтрекинга: звонок → лид в собственной CRM.
api_router.include_router(integrations.calltracking_router)

# Защищённое мобильное API (клинер/клиент): заказы, статусы, профиль, пуши.
api_router.include_router(mobile.router)
# Защищённая админ-CRM (manager/admin): заказы, пользователи, клинеры, финансы.
api_router.include_router(admin.router)

# Публичные эндпоинты веб-лендинга (catalog/pricing/leads/booking/reviews/before-after).
# Совместимы с текущим фронтом (NEXT_PUBLIC_API_URL=/api/v1).
api_router.include_router(pricing.router)
api_router.include_router(leads.router)
api_router.include_router(booking.router)
api_router.include_router(reviews.router)
api_router.include_router(content.router)
