"""Совместимость: код переехал в app.modules.pricing.engine (модульная структура, Phase 1).

Импортируйте из нового места; шим будет удалён после переноса всех вызовов.
"""

from app.modules.pricing.engine import *  # noqa: F401,F403
from app.modules.pricing.engine import __all__  # noqa: F401
