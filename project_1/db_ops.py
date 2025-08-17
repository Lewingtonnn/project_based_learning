import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import os
import asyncio
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, create_engine, select
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

'''---import your SQLModel models here for the tables---'''
from dbmodels import Property, Pricing_and_floor_plans

# Configure logging for database operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

'''--- Database Configuration ---'''
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it to your PostgreSQL database URL.")

# Use an async engine for async operations
engine = create_async_engine(DATABASE_URL, echo=False)

async_session_maker = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncSession:
    """
    Dependency for getting an async database session.
    """
    async with async_session_maker() as session:
        yield session


# --- Database Initialization ---
async def create_db_and_tables():
    """
    Asynchronously creates all tables defined in SQLModel.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# --- Helper Function for Parsing Scraped Numeric Values ---
def parse_numeric_value(text: Any) -> Optional[float]:
    """
    Attempts to extract a numeric (float or int) value from a string.
    Note: This is not an async function, as it is CPU-bound, not I/O-bound.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        try:
            return float(text)
        except (ValueError, TypeError):
            return None

    # Clean the string
    clean_text = text.replace('Sq Ft', '').replace('Bed', '').replace('Bath', '').replace('+', '').strip()
    clean_text = clean_text.replace('$', '').replace(',', '').replace('–', '-').strip()

    try:
        if '-' in clean_text:
            parts = clean_text.split('-')
            if parts[0].strip().isdigit():
                return float(parts[0].strip())
        return float(clean_text)
    except ValueError:
        return None


# --- Data Saving Function ---
async def save_scraped_data_to_db(scraped_data: List[Dict[str, Any]]):
    """
    Asynchronously saves a list of scraped property data to the database,
    handling upsert logic.
    """
    logging.info(f"Starting to save {len(scraped_data)} properties to the database...")

    async for session in get_session():
        for prop_data in scraped_data:
            property_link = prop_data.get('property_link')
            if not property_link:
                logging.warning(f"Skipping property due to missing property_link: {prop_data.get('title', 'N/A')}")
                continue

            # **CRITICAL CHANGE**: Convert the datetime to timezone-naive.
            # We're getting the current time in UTC and then stripping the timezone info.
            now_utc_naive = datetime.utcnow()

            try:
                existing_property = (await session.exec(
                    select(Property).where(Property.property_link == property_link))).first()

                lease_options_str = json.dumps(prop_data['lease_options']) if isinstance(prop_data.get('lease_options'),
                                                                                         list) else None
                parsed_property_reviews = parse_numeric_value(prop_data.get('property_reviews'))
                parsed_year_built = parse_numeric_value(prop_data.get('year_built'))

                if existing_property:
                    logging.info(f"Updating existing property: {prop_data.get('title', 'N/A')}")
                    existing_property.title = prop_data.get('title')
                    existing_property.address = prop_data.get('address')
                    existing_property.street = prop_data.get('street')
                    existing_property.city = prop_data.get('city')
                    existing_property.state = prop_data.get('state')
                    existing_property.zip_code = prop_data.get('zip_code')
                    existing_property.property_reviews = parsed_property_reviews
                    existing_property.listing_verification = prop_data.get('listing_verification')
                    existing_property.lease_options = lease_options_str
                    existing_property.year_built = parsed_year_built
                    existing_property.validation_status = prop_data.get('validation_status', 'pending')
                    existing_property.property_type = prop_data.get('property_type', 'apartment')

                    # Update the timestamp with the new naive datetime
                    existing_property.timestamp = now_utc_naive

                    session.add(existing_property)

                    await session.exec(Pricing_and_floor_plans).filter_by(property_id=existing_property.id).delete()
                    await session.flush()
                else:
                    logging.info(f"Inserting new property: {prop_data.get('title', 'N/A')}")
                    new_property = Property(
                        property_link=property_link,
                        title=prop_data.get('title'),
                        address=prop_data.get('address'),
                        street=prop_data.get('street'),
                        city=prop_data.get('city'),
                        state=prop_data.get('state'),
                        zip_code=prop_data.get('zip_code'),
                        property_reviews=parsed_property_reviews,
                        listing_verification=prop_data.get('listing_verification'),
                        lease_options=lease_options_str,
                        year_built=parsed_year_built,
                        validation_status=prop_data.get('validation_status', 'pending'),
                        property_type=prop_data.get('property_type', 'apartment'),

                        # Use the new naive datetime for the new property
                        timestamp=now_utc_naive
                    )
                    session.add(new_property)
                    await session.flush()
                    existing_property = new_property

                for fp_data in prop_data.get('pricing_and_floor_plans', []):
                    parsed_bedrooms = parse_numeric_value(fp_data.get('bedrooms'))
                    parsed_bathrooms = parse_numeric_value(fp_data.get('bathrooms'))
                    parsed_sqft = parse_numeric_value(fp_data.get('sqft'))
                    parsed_base_rent = parse_numeric_value(fp_data.get('base_rent'))

                    new_floor_plan = Pricing_and_floor_plans(
                        property=existing_property,
                        apartment_name=fp_data.get('apartment_name'),
                        rent_price_range=fp_data.get('rent_price_range'),
                        bedrooms=parsed_bedrooms,
                        bathrooms=parsed_bathrooms,
                        sqft=parsed_sqft,
                        unit=fp_data.get('unit'),
                        base_rent=parsed_base_rent,
                        availability=fp_data.get('availability'),
                        details_link=fp_data.get('details_link'),

                        # Use the new naive datetime for the floor plan
                        timestamp=now_utc_naive
                    )
                    session.add(new_floor_plan)

                await session.commit()
                logging.info(f"Successfully processed and committed property: {property_link}")

            except IntegrityError as ie:
                await session.rollback()
                logging.error(f"Integrity Error for {property_link}: {ie}")
            except Exception as e:
                await session.rollback()
                logging.error(f"Error saving property {property_link} to database: {e}", exc_info=True)


# Main execution block remains the same
async def main():
    try:
        await create_db_and_tables()
        dummy_scraped_data = [
            {
                'title': 'Test Property 1',
                'property_link': 'http://example.com/prop1',
                'address': '123 Test St, Chicago, IL 60601',
                'street': '123 Test St', 'city': 'Chicago', 'state': 'IL', 'zip_code': '60601',
                'property_reviews': '4.5',
                'listing_verification': 'Verified',
                'lease_options': ['12 months', '6 months'],
                'year_built': '2010',
                'validation_status': 'Success',
                'property_type': 'apartment',
                'pricing_and_floor_plans': [
                    {
                        'apartment_name': 'Studio-A',
                        'rent_price_range': '$1500 - $1800',
                        'bedrooms': '0',
                        'bathrooms': '1',
                        'sqft': '400 Sq Ft',
                        'unit': 'S01',
                        'base_rent': '1500.0',
                        'availability': 'Available Now',
                        'details_link': 'key123'
                    },
                    {
                        'apartment_name': '1B-C',
                        'rent_price_range': '$2000 - $2200',
                        'bedrooms': '1',
                        'bathrooms': '1.5',
                        'sqft': '650 Sq Ft',
                        'unit': '1B03',
                        'base_rent': '2000.0',
                        'availability': 'Oct 1',
                        'details_link': 'key456'
                    }
                ]
            },
            {
                'title': 'Test Property 2',
                'property_link': 'http://example.com/prop2',
                'address': '456 Demo Ave, Chicago, IL 60602',
                'street': '456 Demo Ave', 'city': 'Chicago', 'state': 'IL', 'zip_code': '60602',
                'property_reviews': '3.9',
                'listing_verification': 'Not Verified',
                'lease_options': ['12 months'],
                'year_built': '1995',
                'validation_status': 'Success',
                'property_type': 'apartment',
                'pricing_and_floor_plans': [
                    {
                        'apartment_name': 'Studio-B',
                        'rent_price_range': '$1400',
                        'bedrooms': '0',
                        'bathrooms': '1',
                        'sqft': '380 Sq Ft',
                        'unit': 'S02',
                        'base_rent': '1400.0',
                        'availability': 'Sep 15',
                        'details_link': 'key789'
                    }
                ]
            }
        ]

        await save_scraped_data_to_db(dummy_scraped_data)

        logging.info("Database operations script finished.")
    except ValueError as ve:
        logging.error(f"Configuration Error: {ve}")
    except Exception as e:
        logging.error(f"An unexpected error occurred in main: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())