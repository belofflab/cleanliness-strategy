"""Совместимость: код переехал в app.modules.identity.service (модульная структура, Phase 1).

Импортируйте из нового места; шим будет удалён после переноса всех вызовов.
"""

from app.modules.identity.service import *  # noqa: F401,F403
from app.modules.identity.service import __all__  # noqa: F401
