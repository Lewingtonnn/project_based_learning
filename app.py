from fastapi import FastAPI, Depends
from sqlmodel import Session, select, func


from database import get_session,create_db_and_tables
from models import Sources, Listings
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app= FastAPI(lifespan=lifespan)


@app.get("/debug/first")
def debug_first(session: Session = Depends(get_session)):
    first = session.exec(select(Listings)).first()
    return first if first else {"error": "No listings found"}

@app.get("/")
def read_root():
    return {"message": "Welcome to the Real Estate API!"}


@app.get("/all_listings")
def read_all_listing_details(session: Session = Depends(get_session)):
    statement = select(Listings)
    listings = session.exec(statement).all()
    return listings

@app.get("/listings/by-price/{price}")
def read_listings_by_price(price: float, session: Session = Depends(get_session)):
    statement = select(Listings).where(Listings.price <= price)
    listings = session.exec(statement).all()
    return listings

@app.get("/lisings/by-sources/{source_id}")
def read_listings_by_source(source_id: int, session: Session = Depends(get_session)):
    statement = select(Listings).where(Listings.source_id == source_id)
    listings = session.exec(statement).all()
    return listings

@app.get("/listings/by-range/{price_min}/{price_max}")
def get_listings_by_price_range(price_min: float, price_max: float, session: Session = Depends(get_session)):
    statement = select(Listings).where(Listings.price.between(price_min, price_max))
    listings = session.exec(statement).all()
    return listings

@app.get("/listings/{source_id_1}/{source_id_2}")
def get_listings_by_multiple_sources(source_id_1: int, source_id_2: int, session: Session = Depends(get_session)):
    statement = select(Listings).where(Listings.source_id.in_([source_id_1, source_id_2]))
    listings = session.exec(statement).all()
    return listings

@app.get("/top/{n}/expensive-listings")
def get_top_n_listings(n: int, session: Session = Depends(get_session)):
    statement = select(Listings).order_by(Listings.price.desc()).limit(n)
    listings = session.exec(statement).all()
    return listings

@app.get("/top/{n}/cheapest-listings")
def get_top_n_cheapest_listings(n: int, session: Session = Depends(get_session)):
    statement = select(Listings).order_by(Listings.price.asc()).limit(n)
    listings = session.exec(statement).all()
    return listings

@app.get("/listings-source-names")
def get_listings_with_source_names(session: Session = Depends(get_session)):
    statement = select(Listings.title, Sources.name).join(Sources)
    results = session.exec(statement).all()
    return [{"listing": listing.title, "source": source_name} for listing, source_name in results]

@app.get("/this-weeks-listings")
def get_this_weeks_listings(session: Session = Depends(get_session)):
    from datetime import datetime, timedelta
    one_week_ago = datetime.now() - timedelta(days=7)
    statement = select(Listings).where(Listings.created_at >= one_week_ago)
    listings = session.exec(statement).all()
    return listings