import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Annotated

from fastapi import FastAPI, Depends, Header, HTTPException
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from pydantic import BaseModel
from dotenv import load_dotenv
from dbmodels import Property, Pricing_and_floor_plans

load_dotenv()

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# -------------------------
# Database setup (Async)
# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it to your PostgreSQL database URL.")

engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=False, future=True)

async_session_maker = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# -------------------------
# Auth dependency
# -------------------------
class Authorisation:
    async def __call__(self, x_token: Annotated[str, Header()]) -> str:

        token = os.getenv("API_TOKEN")
        if x_token != token:
            raise HTTPException(status_code=403, detail="Invalid Token")
        return x_token


# -------------------------
# Response Models
# -------------------------
class PropertyRead(BaseModel):
    id: int
    title: str
    city: str
    year_built: Optional[int]
    timestamp: datetime

    class Config:
        from_attributes = True


class FloorPlanRead(BaseModel):
    id: int
    property_id: int
    bedrooms: int
    base_rent: float

    class Config:
        from_attributes = True


# -------------------------
# Lifespan
# -------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Application Startup: Creating database tables if they don't exist")
    await create_db_and_tables()
    yield
    logging.info("Application Shutdown: Cleaning up process")


# -------------------------
# App Init
# -------------------------
app = FastAPI(
    title="Real Estate Data API",
    description="API for accessing scraped real estate property and floor plan data.",
    version="2.0.0",
    lifespan=lifespan
)


# -------------------------
# Routes
# -------------------------
@app.get("/", tags=["Health"])
async def welcome():
    return {"Message": "Welcome to the Real estate API"}


@app.get("/all-property-listings", response_model=List[PropertyRead], tags=["Properties"])
async def get_listings(
    session: AsyncSession = Depends(get_session),
    is_authorized: str = Depends(Authorisation())
):
    result = await session.exec(select(Property))
    return result.all()


@app.get("/properties/{property_id}/floor-plans", response_model=List[FloorPlanRead], tags=["Floor Plans"])
async def get_floor_plans(
    property_id: int,
    session: AsyncSession = Depends(get_session),
    is_authorized: str = Depends(Authorisation())
):
    property_exists = await session.exec(select(Property).where(Property.id == property_id))
    if not property_exists.first():
        raise HTTPException(status_code=404, detail="Property with that ID is not available")

    result = await session.exec(
        select(Pricing_and_floor_plans).where(Pricing_and_floor_plans.property_id == property_id)
    )
    return result.all()


@app.get("/properties/search", response_model=List[PropertyRead], tags=["Properties"])
async def search_properties(
    session: AsyncSession = Depends(get_session),
    is_authorized: str = Depends(Authorisation()),
    city: Optional[str] = None,
    min_bedrooms: Optional[int] = None,
    max_base_rent: Optional[float] = None,
    year_built: Optional[int] = None,
):
    statement = select(Property).join(Pricing_and_floor_plans, isouter=True)

    if city:
        statement = statement.where(Property.city.ilike(f"%{city}%"))
    if min_bedrooms is not None:
        statement = statement.where(Pricing_and_floor_plans.bedrooms >= min_bedrooms)
    if max_base_rent is not None:
        statement = statement.where(Pricing_and_floor_plans.base_rent <= max_base_rent)
    if year_built is not None:
        statement = statement.where(Property.year_built == year_built)

    statement = statement.group_by(Property.id)

    result = await session.exec(statement)
    return result.all()


@app.get("/top/{x}/most-affordable-properties", response_model=List[FloorPlanRead], tags=["Analytics"])
async def get_top_x_most_affordable_properties(
    x: int,
    session: AsyncSession = Depends(get_session),
    is_authorized: str = Depends(Authorisation())
):
    result = await session.exec(
        select(Pricing_and_floor_plans).order_by(Pricing_and_floor_plans.base_rent.asc()).limit(x)
    )
    return result.all()


@app.get("/top/{x}/most-expensive-properties", response_model=List[FloorPlanRead], tags=["Analytics"])
async def get_top_x_most_expensive_properties(
    x: int,
    session: AsyncSession = Depends(get_session),
    is_authorized: str = Depends(Authorisation())
):
    result = await session.exec(
        select(Pricing_and_floor_plans).order_by(Pricing_and_floor_plans.base_rent.desc()).limit(x)
    )
    return result.all()


@app.get("/this-weeks-listings", response_model=List[PropertyRead], tags=["Properties"])
async def get_this_weeks_listings(
    session: AsyncSession = Depends(get_session),
    is_authorized: str = Depends(Authorisation())
):
    one_week_ago = datetime.now() - timedelta(days=7)
    result = await session.exec(select(Property).where(Property.timestamp >= one_week_ago))
    return result.all()
