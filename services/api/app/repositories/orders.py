"""Совместимость: код переехал в app.modules.orders.repository (модульная структура, Phase 1).

Импортируйте из нового места; шим будет удалён после переноса всех вызовов.
"""

from app.modules.orders.repository import *  # noqa: F401,F403
from app.modules.orders.repository import __all__  # noqa: F401
