"""Тесты чистой логики калькулятора (без БД)."""

from decimal import Decimal

from app.services.pricing import (
    AddonInput,
    PromoInput,
    ServiceInput,
    compute_quote,
    human_minutes,
)

SERVICE = ServiceInput(
    name="Генеральная уборка",
    base_price=Decimal("3500"),
    price_per_room=Decimal("900"),
    price_per_bathroom=Decimal("700"),
    minutes_base=120,
    minutes_per_room=60,
    minutes_per_bathroom=45,
)


def test_base_quote_without_addons():
    # 3500 + 2*900 + 1*700 = 6000, множитель 1.0
    res = compute_quote(
        service=SERVICE, addons=[], rooms=2, bathrooms=1,
        price_multiplier=Decimal("1.00"),
    )
    assert res.subtotal == Decimal("6000.00")
    assert res.total == Decimal("6000.00")
    # время: 120 + 2*60 + 1*45 = 285 мин
    assert res.est_minutes == 285


def test_quote_with_addons_and_region_multiplier():
    addons = [AddonInput(code="windows", name="Окна", price=Decimal("350"), minutes=30)]
    # base 6000 + 350 = 6350, множитель 1.20 = 7620
    res = compute_quote(
        service=SERVICE, addons=addons, rooms=2, bathrooms=1,
        price_multiplier=Decimal("1.20"),
    )
    assert res.subtotal == Decimal("7620.00")
    assert res.est_minutes == 285 + 30


def test_quote_with_percent_promo():
    promo = PromoInput(code="CLEAN10", discount_type="percent", value=Decimal("10"))
    res = compute_quote(
        service=SERVICE, addons=[], rooms=2, bathrooms=1,
        price_multiplier=Decimal("1.00"), promo=promo,
    )
    # 6000 - 10% = 5400
    assert res.discount == Decimal("600.00")
    assert res.total == Decimal("5400.00")


def test_fixed_promo_capped_at_subtotal():
    promo = PromoInput(code="BIG", discount_type="fixed", value=Decimal("999999"))
    res = compute_quote(
        service=SERVICE, addons=[], rooms=0, bathrooms=0,
        price_multiplier=Decimal("1.00"), promo=promo,
    )
    # скидка не больше суммы
    assert res.total == Decimal("0.00")


def test_human_minutes():
    assert human_minutes(285) == "4 ч 45 мин"
    assert human_minutes(60) == "1 ч"
    assert human_minutes(0) == "—"


# ---------- Квиз (ТЗ п.8): состояние, количество допов, площадь ----------

def test_condition_coefficient_increases_price_and_time():
    # base 6000, «давно не убирали» +15% → 6900
    res = compute_quote(
        service=SERVICE, addons=[], rooms=2, bathrooms=1,
        price_multiplier=Decimal("1.00"), condition="neglected",
    )
    assert res.subtotal == Decimal("6900.00")
    assert res.total == Decimal("6900.00")
    # 285 мин * 1.15 = 327.75 → int() = 327
    assert res.est_minutes == 327
    assert res.needs_assessment is False


def test_heavy_condition_plus_30_percent():
    res = compute_quote(
        service=SERVICE, addons=[], rooms=0, bathrooms=0,
        price_multiplier=Decimal("1.00"), condition="heavy",
    )
    # 3500 * 1.3 = 4550
    assert res.total == Decimal("4550.00")


def test_needs_assessment_flag_without_surcharge():
    res = compute_quote(
        service=SERVICE, addons=[], rooms=2, bathrooms=1,
        price_multiplier=Decimal("1.00"), condition="needs_assessment",
    )
    # Цена базовая (без наценки), но расчёт помечен предварительным.
    assert res.total == Decimal("6000.00")
    assert res.needs_assessment is True


def test_addon_quantity_multiplies_price_and_minutes():
    addons = [
        AddonInput(
            code="windows", name="Мытьё окон", price=Decimal("350"),
            minutes=20, qty=6, unit="створка",
        )
    ]
    res = compute_quote(
        service=SERVICE, addons=addons, rooms=0, bathrooms=0,
        price_multiplier=Decimal("1.00"),
    )
    # 3500 + 6*350 = 5600; время 120 + 6*20 = 240
    assert res.total == Decimal("5600.00")
    assert res.est_minutes == 240
    # Строка детализации содержит количество и единицу.
    labels = [i.label for i in res.items]
    assert any("× 6 створка" in label for label in labels)


def test_area_based_office_pricing():
    office = ServiceInput(
        name="Офисная уборка",
        base_price=Decimal("2500"),
        price_per_room=Decimal("0"),
        price_per_bathroom=Decimal("350"),
        minutes_base=90,
        minutes_per_room=0,
        minutes_per_bathroom=25,
        price_per_sqm=Decimal("45"),
    )
    res = compute_quote(
        service=office, addons=[], rooms=0, bathrooms=2,
        price_multiplier=Decimal("1.00"), area_sqm=120,
    )
    # 2500 + 2*350 + 120*45 = 8600; время 90 + 2*25 + 120*0.5 = 200
    assert res.total == Decimal("8600.00")
    assert res.est_minutes == 200


def test_area_ignored_for_flat_rate_services():
    # У жилых тарифов price_per_sqm=0 — площадь не влияет на цену.
    res = compute_quote(
        service=SERVICE, addons=[], rooms=2, bathrooms=1,
        price_multiplier=Decimal("1.00"), area_sqm=200,
    )
    assert res.total == Decimal("6000.00")

