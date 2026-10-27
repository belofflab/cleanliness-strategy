"""DTO для city-aware контента лендинга."""

from pydantic import BaseModel


class ContentCityOut(BaseModel):
    slug: str
    name: str
    name_prepositional: str
    timezone: str
    phone: str
    email: str


class ContentServiceOut(BaseModel):
    type: str
    name: str
    base_price: float
    price_per_room: float
    price_per_bathroom: float
    price_per_sqm: float = 0
    minutes_base: int
    minutes_per_room: int
    minutes_per_bathroom: int


class ContentAddonOut(BaseModel):
    code: str
    name: str
    price: float
    minutes: int
    unit: str | None = None
    max_qty: int = 10


class ContentBranchOut(BaseModel):
    name: str
    address: str
    phone: str
    email: str | None
    working_hours: str | None


class ContentSeoOut(BaseModel):
    title: str
    description: str
    canonical: str
    hreflang: dict[str, str]


class ContentResponse(BaseModel):
    city: ContentCityOut
    services: list[ContentServiceOut]
    addons: list[ContentAddonOut]
    branches: list[ContentBranchOut]
    seo: ContentSeoOut
