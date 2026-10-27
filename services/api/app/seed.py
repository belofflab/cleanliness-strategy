"""Заполнение БД начальными данными (idempotent).

Города: Тюмень и Уфа. Услуги: поддерживающая, генеральная, после ремонта,
офисная (тариф за м²). Доп.услуги — с единицами количества (створки/часы/шт).
Плюс мастера, слоты, филиалы, промокод, отзывы и демо-кейсы «До/После».

Запуск:
    python -m app.seed            (внутри контейнера: make seed)
Повторный запуск не дублирует данные — проверяем по slug/code/title.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.db import AsyncSessionLocal
from app.models.catalog import AddonService, Branch, City, Master, MasterSchedule, Service
from app.models.marketing import Promotion
from app.models.media import BeforeAfterPair, Media
from app.models.reviews import Review, ReviewSource


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        cities_seed = [
            {
                "slug": "tyumen",
                "name": "Тюмень",
                "name_prepositional": "в Тюмени",
                "timezone": "Asia/Yekaterinburg",
                "phone": "+7 (912) 395-20-43",
                "email": "ow@blanq.tech",
                "price_multiplier": Decimal("1.00"),
                "services": [
                    dict(
                        type="maintenance",
                        name="Поддерживающая уборка",
                        base_price="1500",
                        price_per_room="450",
                        price_per_bathroom="350",
                        minutes_base=60,
                        minutes_per_room=30,
                        minutes_per_bathroom=25,
                    ),
                    dict(
                        type="general",
                        name="Генеральная уборка",
                        base_price="3500",
                        price_per_room="900",
                        price_per_bathroom="700",
                        minutes_base=120,
                        minutes_per_room=60,
                        minutes_per_bathroom=45,
                    ),
                    dict(
                        type="post_renovation",
                        name="Уборка после ремонта",
                        base_price="5000",
                        price_per_room="1300",
                        price_per_bathroom="1000",
                        minutes_base=180,
                        minutes_per_room=90,
                        minutes_per_bathroom=60,
                    ),
                    dict(
                        type="office",
                        name="Офисная уборка",
                        base_price="2500",
                        price_per_room="0",
                        price_per_bathroom="350",
                        price_per_sqm="45",
                        minutes_base=90,
                        minutes_per_room=0,
                        minutes_per_bathroom=25,
                    ),
                ],
                "addons": [
                    dict(code="windows", name="Мытьё окон", price="350", minutes=20, unit="створка", max_qty=30),
                    dict(code="oven", name="Чистка духовки", price="500", minutes=25, unit="шт", max_qty=2),
                    dict(code="fridge", name="Мойка холодильника", price="400", minutes=20, unit="шт", max_qty=3),
                    dict(code="microwave", name="Чистка микроволновки", price="250", minutes=15, unit="шт", max_qty=2),
                    dict(code="kitchen_cabinets", name="Кухонные шкафы внутри", price="300", minutes=12, unit="секция", max_qty=12),
                    dict(code="balcony", name="Уборка балкона/лоджии", price="900", minutes=45, unit="шт", max_qty=3),
                    dict(code="ironing", name="Глажка белья", price="600", minutes=60, unit="час", max_qty=8),
                    dict(code="walls_washing", name="Мытьё стен", price="90", minutes=3, unit="м²", max_qty=300),
                    dict(code="construction_dust", name="Удаление строительной пыли", price="70", minutes=2, unit="м²", max_qty=500),
                    dict(code="upholstery", name="Химчистка мебели", price="1500", minutes=45, unit="предмет", max_qty=10),
                ],
                "masters": [
                    dict(full_name="Гульнара Х.", rating=Decimal("4.95")),
                    dict(full_name="Алина С.", rating=Decimal("4.90")),
                ],
                "branches": [
                    dict(
                        name="Точка Чистоты — Центр",
                        address="Тюмень, ул. Мельникайте, 30к1",
                        phone="+7 (912) 395-20-43",
                        email="ow@blanq.tech",
                        working_hours="Ежедневно 08:00–22:00",
                    ),
                    dict(
                        name="Точка Чистоты — Восточный",
                        address="Тюмень, ул. Мельникайте, 127А",
                        phone="+7 (912) 395-20-43",
                        email="ow@blanq.tech",
                        working_hours="Ежедневно 09:00–21:00",
                    ),
                ],
            },
            {
                "slug": "ufa",
                "name": "Уфа",
                "name_prepositional": "в Уфе",
                "timezone": "Asia/Yekaterinburg",
                "phone": "+7 (993) 138-60-53",
                "email": "ow@blanq.tech",
                "price_multiplier": Decimal("1.00"),
                "services": [
                    dict(
                        type="maintenance",
                        name="Поддерживающая уборка",
                        base_price="1650",
                        price_per_room="490",
                        price_per_bathroom="370",
                        minutes_base=60,
                        minutes_per_room=30,
                        minutes_per_bathroom=25,
                    ),
                    dict(
                        type="general",
                        name="Генеральная уборка",
                        base_price="3750",
                        price_per_room="980",
                        price_per_bathroom="760",
                        minutes_base=120,
                        minutes_per_room=60,
                        minutes_per_bathroom=45,
                    ),
                    dict(
                        type="post_renovation",
                        name="Уборка после ремонта",
                        base_price="5350",
                        price_per_room="1380",
                        price_per_bathroom="1080",
                        minutes_base=180,
                        minutes_per_room=90,
                        minutes_per_bathroom=60,
                    ),
                    dict(
                        type="office",
                        name="Офисная уборка",
                        base_price="2650",
                        price_per_room="0",
                        price_per_bathroom="370",
                        price_per_sqm="48",
                        minutes_base=90,
                        minutes_per_room=0,
                        minutes_per_bathroom=25,
                    ),
                ],
                "addons": [
                    dict(code="windows", name="Мытьё окон", price="380", minutes=20, unit="створка", max_qty=30),
                    dict(code="oven", name="Чистка духовки", price="550", minutes=25, unit="шт", max_qty=2),
                    dict(code="fridge", name="Мойка холодильника", price="420", minutes=20, unit="шт", max_qty=3),
                    dict(code="microwave", name="Чистка микроволновки", price="270", minutes=15, unit="шт", max_qty=2),
                    dict(code="kitchen_cabinets", name="Кухонные шкафы внутри", price="320", minutes=12, unit="секция", max_qty=12),
                    dict(code="balcony", name="Уборка балкона/лоджии", price="950", minutes=45, unit="шт", max_qty=3),
                    dict(code="ironing", name="Глажка белья", price="650", minutes=60, unit="час", max_qty=8),
                    dict(code="walls_washing", name="Мытьё стен", price="100", minutes=3, unit="м²", max_qty=300),
                    dict(code="construction_dust", name="Удаление строительной пыли", price="75", minutes=2, unit="м²", max_qty=500),
                    dict(code="upholstery", name="Химчистка мебели", price="1600", minutes=45, unit="предмет", max_qty=10),
                ],
                "masters": [
                    dict(full_name="Лейсан Г.", rating=Decimal("4.94")),
                    dict(full_name="Рамиля Н.", rating=Decimal("4.92")),
                ],
                "branches": [
                    dict(
                        name="Точка Чистоты — Проспект Октября",
                        address="Уфа, пр. Октября, 56",
                        phone="+7 (993) 138-60-53",
                        email="ow@blanq.tech",
                        working_hours="Ежедневно 08:00–22:00",
                    ),
                    dict(
                        name="Точка Чистоты — Сипайлово",
                        address="Уфа, ул. Гагарина, 47",
                        phone="+7 (993) 138-60-53",
                        email="ow@blanq.tech",
                        working_hours="Ежедневно 09:00–21:00",
                    ),
                ],
            },
        ]

        for city_seed in cities_seed:
            city = (
                await db.execute(select(City).where(City.slug == city_seed["slug"]))
            ).scalar_one_or_none()
            if city is None:
                city = City(
                    name=city_seed["name"],
                    slug=city_seed["slug"],
                    name_prepositional=city_seed["name_prepositional"],
                    timezone=city_seed["timezone"],
                    phone=city_seed["phone"],
                    email=city_seed["email"],
                    price_multiplier=city_seed["price_multiplier"],
                    is_active=True,
                )
                db.add(city)
                await db.flush()
            else:
                city.name = city_seed["name"]
                city.name_prepositional = city_seed["name_prepositional"]
                city.timezone = city_seed["timezone"]
                city.phone = city_seed["phone"]
                city.email = city_seed["email"]
                city.price_multiplier = city_seed["price_multiplier"]
                city.is_active = True

            for service_seed in city_seed["services"]:
                service = (
                    await db.execute(
                        select(Service).where(
                            Service.city_id == city.id,
                            Service.type == service_seed["type"],
                        )
                    )
                ).scalar_one_or_none()
                if service is None:
                    db.add(
                        Service(
                            city_id=city.id,
                            type=service_seed["type"],
                            name=service_seed["name"],
                            base_price=Decimal(service_seed["base_price"]),
                            price_per_room=Decimal(service_seed["price_per_room"]),
                            price_per_bathroom=Decimal(service_seed["price_per_bathroom"]),
                            price_per_sqm=Decimal(service_seed.get("price_per_sqm", "0")),
                            minutes_base=service_seed["minutes_base"],
                            minutes_per_room=service_seed["minutes_per_room"],
                            minutes_per_bathroom=service_seed["minutes_per_bathroom"],
                            is_active=True,
                        )
                    )
                else:
                    service.name = service_seed["name"]
                    service.base_price = Decimal(service_seed["base_price"])
                    service.price_per_room = Decimal(service_seed["price_per_room"])
                    service.price_per_bathroom = Decimal(service_seed["price_per_bathroom"])
                    service.price_per_sqm = Decimal(service_seed.get("price_per_sqm", "0"))
                    service.minutes_base = service_seed["minutes_base"]
                    service.minutes_per_room = service_seed["minutes_per_room"]
                    service.minutes_per_bathroom = service_seed["minutes_per_bathroom"]
                    service.is_active = True

            for addon_seed in city_seed["addons"]:
                addon = (
                    await db.execute(
                        select(AddonService).where(
                            AddonService.city_id == city.id,
                            AddonService.code == addon_seed["code"],
                        )
                    )
                ).scalar_one_or_none()
                if addon is None:
                    db.add(
                        AddonService(
                            city_id=city.id,
                            code=addon_seed["code"],
                            name=addon_seed["name"],
                            price=Decimal(addon_seed["price"]),
                            minutes=addon_seed["minutes"],
                            unit=addon_seed.get("unit"),
                            max_qty=addon_seed.get("max_qty", 10),
                            is_active=True,
                        )
                    )
                else:
                    addon.name = addon_seed["name"]
                    addon.price = Decimal(addon_seed["price"])
                    addon.minutes = addon_seed["minutes"]
                    addon.unit = addon_seed.get("unit")
                    addon.max_qty = addon_seed.get("max_qty", 10)
                    addon.is_active = True

            for master_seed in city_seed["masters"]:
                master = (
                    await db.execute(
                        select(Master).where(
                            Master.city_id == city.id,
                            Master.full_name == master_seed["full_name"],
                        )
                    )
                ).scalar_one_or_none()
                if master is None:
                    db.add(Master(city_id=city.id, is_active=True, **master_seed))
                else:
                    master.rating = master_seed["rating"]
                    master.is_active = True

            await db.flush()

            city_masters = (
                await db.execute(select(Master).where(Master.city_id == city.id))
            ).scalars().all()
            for master in city_masters:
                has_slots = (
                    await db.execute(
                        select(MasterSchedule).where(MasterSchedule.master_id == master.id)
                    )
                ).first()
                if has_slots:
                    continue
                for day_offset in range(1, 6):
                    work_day = date.today() + timedelta(days=day_offset)
                    for start, end in (
                        (time(10, 0), time(13, 0)),
                        (time(14, 0), time(18, 0)),
                    ):
                        db.add(
                            MasterSchedule(
                                master_id=master.id,
                                work_date=work_day,
                                start_time=start,
                                end_time=end,
                                is_booked=False,
                            )
                        )

            for branch_seed in city_seed["branches"]:
                branch = (
                    await db.execute(
                        select(Branch).where(
                            Branch.city_id == city.id,
                            Branch.name == branch_seed["name"],
                        )
                    )
                ).scalar_one_or_none()
                if branch is None:
                    db.add(Branch(city_id=city.id, is_active=True, **branch_seed))
                else:
                    branch.address = branch_seed["address"]
                    branch.phone = branch_seed["phone"]
                    branch.email = branch_seed["email"]
                    branch.working_hours = branch_seed["working_hours"]
                    branch.is_active = True

            source_ids = {
                "tyumen": "tyumen-demo",
                "ufa": "ufa-demo",
            }
            for provider in ("yandex", "2gis"):
                source = (
                    await db.execute(
                        select(ReviewSource).where(
                            ReviewSource.city_id == city.id,
                            ReviewSource.provider == provider,
                        )
                    )
                ).scalar_one_or_none()
                if source is None:
                    db.add(
                        ReviewSource(
                            city_id=city.id,
                            provider=provider,
                            external_place_id=source_ids[city.slug],
                            is_active=True,
                        )
                    )
                else:
                    source.external_place_id = source_ids[city.slug]
                    source.is_active = True

            has_reviews = (
                await db.execute(
                    select(Review).where(Review.city_id == city.id).limit(1)
                )
            ).first()
            if not has_reviews:
                db.add(
                    Review(
                        city_id=city.id,
                        provider="manual",
                        external_id=None,
                        author_name="Алина",
                        rating=Decimal("5.0"),
                        text=f"Заказала генеральную уборку {city.name_prepositional} — всё чётко по времени и очень аккуратно.",
                        service_type="Генеральная уборка",
                        published_at=datetime.now(timezone.utc),
                        is_published=True,
                    )
                )
            else:
                # Прозрачные отзывы (ТЗ п.6): дозаполняем вид уборки и дату
                # у ранее засеянных отзывов, чтобы карточки не были пустыми.
                bare_reviews = (
                    await db.execute(
                        select(Review).where(
                            Review.city_id == city.id,
                            Review.provider == "manual",
                            Review.service_type.is_(None),
                        )
                    )
                ).scalars().all()
                for bare in bare_reviews:
                    bare.service_type = "Генеральная уборка"
                    if bare.published_at is None:
                        bare.published_at = bare.created_at

        promo = (
            await db.execute(select(Promotion).where(Promotion.code == "CLEAN10"))
        ).scalar_one_or_none()
        if promo is None:
            db.add(
                Promotion(
                    city_id=None,
                    code="CLEAN10",
                    discount_type="percent",
                    value=Decimal("10"),
                    is_active=True,
                )
            )

        # --- Кейсы «До/После» (ТЗ п.4/9): 4 кейса на город с карточкой заказа. ---
        # Фотографии РЕАЛЬНЫЕ (передал заказчик, опубликованы с согласия клиентов):
        # apps/web/public/cases/*.webp. Кейсы матчятся по (город, sort_order), чтобы
        # обновление заголовков/фото не плодило дубликатов.
        cases_seed: dict[str, list[dict]] = {
            "tyumen": [
                dict(
                    title="Генеральная уборка двухкомнатной квартиры",
                    room_type="Кухня в двухкомнатной квартире",
                    area_sqm=64,
                    cleaning_type="Генеральная уборка",
                    cleaners_count=2,
                    duration_hours=Decimal("5.0"),
                    cost_text="8 900 ₽",
                    district="Центральный округ",
                    task_text="Кухня после арендаторов: рабочие поверхности, техника, раковина и фасады.",
                    review_text="Принимала по чек-листу — всё идеально, особенно кухня.",
                    before_url="/cases/kitchen-blue-before.webp",
                    after_url="/cases/kitchen-blue-after.webp",
                ),
                dict(
                    title="Генеральная уборка гостиной",
                    room_type="Гостиная в трёхкомнатной квартире",
                    area_sqm=18,
                    cleaning_type="Генеральная уборка",
                    cleaners_count=2,
                    duration_hours=Decimal("4.0"),
                    cost_text="6 400 ₽",
                    district="Заречный микрорайон",
                    task_text="Пыль на мебели и технике, ковры, текстиль и труднодоступные зоны.",
                    review_text="Комнату не узнать — чисто и свежо, как после ремонта.",
                    before_url="/cases/living-room-before.webp",
                    after_url="/cases/living-room-after.webp",
                ),
                dict(
                    title="Генеральная уборка кухни и плиты",
                    room_type="Кухня",
                    area_sqm=9,
                    cleaning_type="Генеральная уборка",
                    cleaners_count=1,
                    duration_hours=Decimal("3.0"),
                    cost_text="4 500 ₽",
                    district="Дом Обороны",
                    task_text="Застарелый жир на варочной панели и духовке, налёт на фасадах и фартуке.",
                    review_text="Плита выглядит как новая, спасибо за терпение!",
                    before_url="/cases/kitchen-stove-before.webp",
                    after_url="/cases/kitchen-stove-after.webp",
                ),
                dict(
                    title="Поддерживающая уборка гостиной",
                    room_type="Гостиная",
                    area_sqm=16,
                    cleaning_type="Поддерживающая уборка",
                    cleaners_count=1,
                    duration_hours=Decimal("2.0"),
                    cost_text="2 900 ₽",
                    district="Центральный округ",
                    task_text="Уборка после детских игр: пол, мягкая мебель, пыль и вынос мусора.",
                    review_text="Стабильно приезжают вовремя, результат одинаково хороший.",
                    before_url="/cases/living-floor-before.webp",
                    after_url="/cases/living-floor-after.webp",
                ),
            ],
            "ufa": [
                dict(
                    title="Уборка сильно запущенной комнаты",
                    room_type="Комната в квартире",
                    area_sqm=17,
                    cleaning_type="Генеральная уборка",
                    cleaners_count=3,
                    duration_hours=Decimal("8.0"),
                    cost_text="от 15 000 ₽",
                    district="Черниковка",
                    task_text="Комната в запущенном состоянии: вынос мусора, дезинфекция, мытьё всех поверхностей.",
                    review_text="Не верили, что комнату можно спасти — команда справилась за день.",
                    before_url="/cases/room-deep-before.webp",
                    after_url="/cases/room-deep-after.webp",
                ),
                dict(
                    title="Генеральная уборка ванной комнаты",
                    room_type="Ванная комната",
                    area_sqm=6,
                    cleaning_type="Генеральная уборка",
                    cleaners_count=1,
                    duration_hours=Decimal("2.5"),
                    cost_text="3 500 ₽",
                    district="Сипайлово",
                    task_text="Известковый налёт на сантехнике и плитке, уборка после долгого отсутствия хозяев.",
                    review_text="Ванная сияет — даже швы плитки снова белые.",
                    before_url="/cases/bathroom-before.webp",
                    after_url="/cases/bathroom-after.webp",
                ),
                dict(
                    title="Поддерживающая уборка кухни",
                    room_type="Кухня",
                    area_sqm=10,
                    cleaning_type="Поддерживающая уборка",
                    cleaners_count=1,
                    duration_hours=Decimal("1.5"),
                    cost_text="2 400 ₽",
                    district="Проспект Октября",
                    task_text="Порядок на кухне: посуда, рабочие поверхности, раковина и плита.",
                    review_text="Удобно, что можно оставить ключи — доверяем полностью.",
                    before_url="/cases/kitchen-dishes-before.webp",
                    after_url="/cases/kitchen-dishes-after.webp",
                ),
                dict(
                    title="Генеральная уборка кухни",
                    room_type="Кухня",
                    area_sqm=8,
                    cleaning_type="Генеральная уборка",
                    cleaners_count=2,
                    duration_hours=Decimal("4.0"),
                    cost_text="5 900 ₽",
                    district="Зелёная Роща",
                    task_text="Газовая плита и посуда, жир на фасадах и фартуке, генеральная чистка поверхностей.",
                    review_text="Кухней снова приятно пользоваться, всё блестит.",
                    before_url="/cases/kitchen-gas-before.webp",
                    after_url="/cases/kitchen-gas-after.webp",
                ),
            ],
        }

        for city_slug, city_cases in cases_seed.items():
            city = (
                await db.execute(select(City).where(City.slug == city_slug))
            ).scalar_one_or_none()
            if city is None:
                continue

            # Сид владеет только парами с media.bucket == 'seed': загруженные
            # менеджером через админку (S3) не трогаем. Существующие сид-пары
            # сопоставляются с кейсами по порядку — детерминированно, без дублей.
            city_pairs = (
                await db.execute(
                    select(BeforeAfterPair)
                    .where(BeforeAfterPair.city_id == city.id)
                    .order_by(BeforeAfterPair.sort_order, BeforeAfterPair.created_at)
                )
            ).scalars().all()
            seed_pairs: list[BeforeAfterPair] = []
            for pair in city_pairs:
                before_media = await db.get(Media, pair.before_media_id)
                if before_media is not None and before_media.bucket == "seed":
                    seed_pairs.append(pair)

            # Лишние сид-пары (старые версии сидов) — скрываем, чтобы не было дублей.
            for extra_pair in seed_pairs[len(city_cases):]:
                extra_pair.is_active = False

            for sort_order, case in enumerate(city_cases):
                existing_pair = seed_pairs[sort_order] if sort_order < len(seed_pairs) else None

                if existing_pair is None:
                    before = Media(
                        owner_type="before_after",
                        bucket="seed",
                        key=f"{city_slug}/case-{sort_order}-before",
                        url=case["before_url"],
                        content_type="image/webp",
                    )
                    after = Media(
                        owner_type="before_after",
                        bucket="seed",
                        key=f"{city_slug}/case-{sort_order}-after",
                        url=case["after_url"],
                        content_type="image/webp",
                    )
                    db.add_all([before, after])
                    await db.flush()
                    existing_pair = BeforeAfterPair(
                        city_id=city.id,
                        title=case["title"],
                        before_media_id=before.id,
                        after_media_id=after.id,
                        is_active=True,
                    )
                    db.add(existing_pair)
                else:
                    # Реальные фото пришли на смену плейсхолдерам —
                    # обновляем URL существующих медиа-записей пары.
                    before_media = await db.get(Media, existing_pair.before_media_id)
                    after_media = await db.get(Media, existing_pair.after_media_id)
                    if before_media is not None:
                        before_media.url = case["before_url"]
                        before_media.content_type = "image/webp"
                    if after_media is not None:
                        after_media.url = case["after_url"]
                        after_media.content_type = "image/webp"

                existing_pair.title = case["title"]
                existing_pair.room_type = case["room_type"]
                existing_pair.area_sqm = case["area_sqm"]
                existing_pair.cleaning_type = case["cleaning_type"]
                existing_pair.cleaners_count = case["cleaners_count"]
                existing_pair.duration_hours = case["duration_hours"]
                existing_pair.cost_text = case["cost_text"]
                existing_pair.district = case["district"]
                existing_pair.task_text = case["task_text"]
                existing_pair.review_text = case["review_text"]
                existing_pair.sort_order = sort_order
                existing_pair.is_active = True

        await db.commit()
        print(
            "Сиды применены: tyumen/ufa, услуги (вкл. офисную), доп.услуги с количеством, "
            "мастера, слоты, филиалы, промокод, отзывы, кейсы «До/После»"
        )


if __name__ == "__main__":
    asyncio.run(seed())

