"""Доменные модули платформы (Phase 1 модульной структуры, см. docs/SYSTEM_AUDIT.md §7.1).

Каждый модуль — ограниченный контекст со своими service/repository (и далее
router/schemas/events): pricing, identity, orders; следующие — dispatch, tracking,
checklists, payments, reviews, finance, subscriptions, notifications, realtime.

Правила:
- модули не импортируют пакеты друг друга целиком, только конкретные файлы
  (например, `app.modules.identity.repository`), чтобы не плодить циклы;
- старые пути `app.services.*` / `app.repositories.*` остаются как шимы
  до переноса всех вызовов и удаляются после.
"""
