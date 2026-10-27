"""Каталог: города, услуги, доп.услуги, мастера и их расписание.

Мультирегиональность: услуги, доп.услуги и мастера привязаны к city_id,
поэтому выбор города на фронте автоматически определяет доступность и цены.
"""

import uuid
from datetime import date, time

from sqlalchemy import (
    Boolean,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class City(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Город/регион присутствия сервиса."""

    __tablename__ = "cities"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    name_prepositional: Mapped[str] = mapped_column(String(160), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Yekaterinburg")
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # Региональный коэффициент цены: Тюмень = 1.00, дороже/дешевле — корректируем.
    price_multiplier: Mapped[float] = mapped_column(
        Numeric(4, 2), default=1.00, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    services: Mapped[list["Service"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    addons: Mapped[list["AddonService"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    masters: Mapped[list["Master"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    branches: Mapped[list["Branch"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )


class Service(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Основная услуга уборки (поддерживающая/генеральная/после ремонта)."""

    __tablename__ = "services"
    __table_args__ = (
        # В одном городе один тип услуги встречается один раз.
        UniqueConstraint("city_id", "type", name="uq_service_city_type"),
    )

    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # maintenance | general | post_renovation | office
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)

    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    price_per_room: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    price_per_bathroom: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    # Цена за м² (офисная уборка и другие тарифы «от площади»); 0 = не используется.
    price_per_sqm: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    minutes_base: Mapped[int] = mapped_column(Integer, default=0)
    minutes_per_room: Mapped[int] = mapped_column(Integer, default=0)
    minutes_per_bathroom: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    city: Mapped["City"] = relationship(back_populates="services")


class AddonService(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Дополнительная услуга (мытьё окон, духовка, холодильник, глажка)."""

    __tablename__ = "addon_services"
    __table_args__ = (
        UniqueConstraint("city_id", "code", name="uq_addon_city_code"),
    )

    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # windows | oven | fridge | microwave | kitchen_cabinets | balcony |
    # ironing | walls_washing | construction_dust | upholstery
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, default=0)
    # Единица измерения для количества («створка», «час», «шт»); NULL = без количества.
    unit: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Максимальное количество в квизе (защита от абсурдных значений).
    max_qty: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    city: Mapped["City"] = relationship(back_populates="addons")


class Master(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Мастер (клинер), привязанный к городу."""

    __tablename__ = "masters"

    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 2), default=5.00)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Телефон клинера: по нему мастер входит по OTP и связывается с учёткой.
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    # Учётная запись клинера (для мобильного приложения мастера).
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True
    )

    city: Mapped["City"] = relationship(back_populates="masters")
    schedules: Mapped[list["MasterSchedule"]] = relationship(
        back_populates="master", cascade="all, delete-orphan"
    )


class MasterSchedule(UUIDPrimaryKeyMixin, Base):
    """Слот доступности мастера для букинга (Блок 3)."""

    __tablename__ = "master_schedules"

    master_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("masters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    master: Mapped["Master"] = relationship(back_populates="schedules")


class Branch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Филиал в городе: контактный телефон, адрес и режим работы."""

    __tablename__ = "branches"

    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    working_hours: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    city: Mapped["City"] = relationship(back_populates="branches")

