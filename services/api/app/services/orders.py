"""Совместимость: код переехал в app.modules.orders.service (модульная структура, Phase 1).

Импортируйте из нового места; шим будет удалён после переноса всех вызовов.
"""

from app.modules.orders.service import *  # noqa: F401,F403
from app.modules.orders.service import __all__  # noqa: F401
