from typing import Optional
from datetime import datetime, timezone

from sqlmodel import SQLModel, Relationship, Field

class Property(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    property_link: str = Field(max_length=500)
    address: str = Field(max_length=500)
    listing_verification: str = Field(max_length=100)
    property_reviews: float = Field(default=0)
    year_built: int = Field(default=None)
    street: str = Field(max_length=200, default=None)
    city: str = Field(max_length=100, default=None)
    state: str = Field(max_length=100, default=None)
    zip_code: str = Field(default=None)
    validation_status: str = Field(max_length=50, default="pending")
    property_type: str = Field(max_length=100, default="apartment")
    lease_option: Optional[str] = Field(max_length=1000, default=None)
    timestamp: datetime = Field(default_factory=lambda :datetime.now(timezone.utc), nullable=False)

    pricing_and_floor_plans: list["Pricing_and_floor_plans"] = Relationship(back_populates="property")


class Pricing_and_floor_plans(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="property.id", nullable=False)
    apartment_name: str = Field(max_length=200)
    rent_price_range: str = Field(max_length=100)
    bedrooms: Optional[int] = Field(default=None, nullable=True)
    bathrooms: Optional[float] = Field(default=None, nullable=True)
    sqft: Optional[int] = Field(default=None, nullable=True)
    unit: Optional[str] = Field(max_length=50, default=None, nullable=True)
    base_rent: Optional[float] = Field(default=None, nullable=True)
    availability: str = Field(max_length=50, default=None)
    details_link: str = Field(max_length=500, default=None)

    property: Optional[Property] = Relationship(back_populates="pricing_and_floor_plans")