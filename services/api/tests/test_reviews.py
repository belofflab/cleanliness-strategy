"""Тесты агрегатора отзывов (чистая логика, без БД/сети)."""

from app.services.reviews_sync import (
    PROVIDER_2GIS,
    PROVIDER_YANDEX,
    ReviewItem,
    dedup_items,
    fetch_provider,
)


def test_fetch_provider_returns_items():
    items = fetch_provider(PROVIDER_YANDEX, "tyumen-demo")
    assert items and items[0].provider == PROVIDER_YANDEX
    assert items[0].external_id.startswith("tyumen-demo")


def test_fetch_unknown_provider_empty():
    assert fetch_provider("unknown", "x") == []


def test_dedup_by_provider_and_external_id():
    a = ReviewItem(provider="yandex", external_id="1", author_name="A", rating=5, text="t")
    a_dup = ReviewItem(provider="yandex", external_id="1", author_name="A2", rating=4, text="t2")
    b = ReviewItem(provider="2gis", external_id="1", author_name="B", rating=5, text="t")
    result = dedup_items([a, a_dup, b])
    assert len(result) == 2
    assert {(r.provider, r.external_id) for r in result} == {("yandex", "1"), ("2gis", "1")}


def test_different_providers_same_external_id_kept():
    items = fetch_provider(PROVIDER_2GIS, "place") + fetch_provider(PROVIDER_YANDEX, "place")
    assert len(dedup_items(items)) == 2

