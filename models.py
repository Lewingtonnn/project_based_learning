from typing import Optional
from datetime import datetime, UTC, timezone
from sqlmodel import SQLModel, Field, Relationship
import time
from typing import Optional



class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, nullable=False)
    created_at: str = Field(default_factory=lambda :datetime.now(timezone.utc), nullable=False)

    listings: list["Listings"]= Relationship(back_populates="user")


class Sources(SQLModel, table=True):
    id: Optional[int]  = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)
    base_url: str = Field(nullable=False)

    listings: list["Listings"] = Relationship(back_populates="source")

class Listings(SQLModel, table=True):
    id: Optional[int]  = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", nullable=False)
    users_id: int = Field(foreign_key="users.id", nullable= False)
    title: str = Field(nullable=False)
    url: str = Field(nullable=False)
    price: float = Field(nullable=False, index= True)
    location: str = Field(nullable=True, index=True)
    bedrooms: int = Field(nullable=True, index=True)
    created_at: str = Field(default_factory=lambda :datetime.now(timezone.utc), nullable=False)

    source: Optional[Sources] = Relationship(back_populates="listings")
    user: Optional[Users] = Relationship(back_populates="listings")
    pricing_history: list["Pricing_history"] = Relationship(back_populates="listing")

class Pricing_history(SQLModel, table =True):
    id: Optional[int]  = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listings.id", nullable=False)
    price: float = Field(nullable=False)
    timestamp: str = Field(default_factory=lambda :datetime.now(timezone.utc), nullable=False)

    listing: Optional[Listings] = Relationship(back_populates="pricing_history")