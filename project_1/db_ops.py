import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import os
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, create_engine, Session, select
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker



'''---import your SQLModel models here for the tables---'''
from dbmodels import Property, \
    Pricing_and_floor_plans

# Configure logging for database operations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

'''--- Database Configuration ---'''
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set. Please set it to your PostgreSQL database URL.")

engine = create_engine(DATABASE_URL, echo=False)

async_session_maker = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# --- Database Initialization ---
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)



# --- Helper Function for Parsing Scraped Numeric Values ---
def parse_numeric_value(text: Any) -> Optional[float]:
    """
    Attempts to extract a numeric (float or int) value from a string.
    Handles common text suffixes and returns None if parsing fails.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        # If it's already a number, we just return it (or convert to float)
        try:
            return float(text)
        except (ValueError, TypeError):
            return None

    # Clean the string: remove common text, currency symbols, commas, etc.
    clean_text = text.replace('Sq Ft', '').replace('Bed', '').replace('Bath', '').replace('+', '').strip()
    clean_text = clean_text.replace('$', '').replace(',', '').replace('–',
                                                                      '-').strip()  # Handle ranges like "$1,000 - $2,000"

    try:
        # Handle ranges like "2 - 3" by taking the first number, or simple numbers
        if '-' in clean_text:
            parts = clean_text.split('-')
            if parts[0].strip().isdigit():  # Only take if the first part is a digit
                return float(parts[0].strip())
        return float(clean_text)  # Attempt to convert to float (handles integers too)
    except ValueError:
        return None  # Return None if conversion fails






# --- Data Saving Function ---
def save_scraped_data_to_db(scraped_data: List[Dict[str, Any]]):
    """
    Saves a list of scraped property data (dictionaries) to the PostgreSQL database.
    It handles upsert logic (updating existing properties or inserting new ones)
    and related floor plan data.
    """
    logging.info(f"Starting to save {len(scraped_data)} properties to the database...")

    with Session(engine) as session:  # Use a context manager for the session
        for prop_data in scraped_data:
            property_link = prop_data.get('property_link')
            if not property_link:
                logging.warning(f"Skipping property due to missing property_link: {prop_data.get('title', 'N/A')}")
                continue

            try:
                # Check if property already exists based on unique property_link
                existing_property = session.exec(
                    select(Property).where(Property.property_link == property_link)).first()

                # --- Prepare Property Data ---
                # Convert lease_options list to JSON string for storage
                lease_options_str = json.dumps(prop_data['lease_options']) if isinstance(prop_data.get('lease_options'),
                                                                                         list) else None

                # Parse numeric fields
                parsed_property_reviews = parse_numeric_value(prop_data.get('property_reviews'))
                parsed_year_built = parse_numeric_value(prop_data.get('year_built'))

                if existing_property:
                    # Update existing property
                    logging.info(f"Updating existing property: {prop_data.get('title', 'N/A')}")
                    existing_property.title = prop_data.get('title')
                    existing_property.address = prop_data.get('address')
                    existing_property.street = prop_data.get('street')
                    existing_property.city = prop_data.get('city')
                    existing_property.state = prop_data.get('state')
                    existing_property.zip_code = prop_data.get('zip_code')  # This should be a string
                    existing_property.property_reviews = parsed_property_reviews
                    existing_property.listing_verification = prop_data.get('listing_verification')
                    existing_property.lease_options = lease_options_str
                    existing_property.year_built = parsed_year_built
                    existing_property.validation_status = prop_data.get('validation_status', 'pending')
                    existing_property.property_type = prop_data.get('property_type', 'apartment')
                    existing_property.timestamp = datetime.now(timezone.utc)  # Update timestamp on change

                    session.add(existing_property)  # Add back to session to mark as modified

                    # For floor plans: Delete old ones and insert new ones
                    # This is a simple approach. For complex scenarios, you'd compare and update.
                    session.exec(Pricing_and_floor_plans).filter_by(property_id=existing_property.id).delete()
                    session.flush()  # Ensure deletions are processed before adding new ones
                else:
                    # Create new property
                    logging.info(f"Inserting new property: {prop_data.get('title', 'N/A')}")
                    new_property = Property(
                        property_link=property_link,
                        title=prop_data.get('title'),
                        address=prop_data.get('address'),
                        street=prop_data.get('street'),
                        city=prop_data.get('city'),
                        state=prop_data.get('state'),
                        zip_code=prop_data.get('zip_code'),  # This should be a string now
                        property_reviews=parsed_property_reviews,
                        listing_verification=prop_data.get('listing_verification'),
                        lease_options=lease_options_str,
                        year_built=parsed_year_built,
                        validation_status=prop_data.get('validation_status', 'pending'),
                        property_type=prop_data.get('property_type', 'apartment'),
                        timestamp=datetime.now(timezone.utc)
                    )
                    session.add(new_property)

                    session.flush()  # Flush to get the new_property.id for floor plans

                    existing_property = new_property  # Set for subsequent floor plan processing

                # --- Save Floor Plans associated with this property ---
                for fp_data in prop_data.get('pricing_and_floor_plans',
                                             []):  # Use 'pricing_and_floor_plans' from scraper output
                    # Parse numeric fields for floor plan
                    parsed_bedrooms = parse_numeric_value(fp_data.get('bedrooms'))
                    parsed_bathrooms = parse_numeric_value(fp_data.get('bathrooms'))
                    parsed_sqft = parse_numeric_value(fp_data.get('sqft'))
                    parsed_base_rent = parse_numeric_value(fp_data.get('base_rent'))

                    new_floor_plan = Pricing_and_floor_plans(
                        property=existing_property,  # Link to the parent property object
                        apartment_name=fp_data.get('apartment_name'),  # Use 'apartment_name' from scraper output
                        rent_price_range=fp_data.get('rent_price_range'),
                        bedrooms=parsed_bedrooms,
                        bathrooms=parsed_bathrooms,
                        sqft=parsed_sqft,
                        unit=fp_data.get('unit'),
                        base_rent=parsed_base_rent,
                        availability=fp_data.get('availability'),
                        details_link=fp_data.get('details_link'),
                        timestamp=datetime.now(timezone.utc)
                    )
                    session.add(new_floor_plan)
                    session.flush()

            except IntegrityError as ie:
                session.rollback()
                logging.error(f"Integrity Error (e.g., duplicate unique field) for {property_link}: {ie}")
                logging.info("Attempting to re-fetch and update if necessary based on unique constraint.")
                # This block would need more sophisticated logic to handle specific unique constraint violations later
                # if you intend to only update *specific* fields on conflict rather than re-inserting....but for now we leave it like that update it when needed
            except Exception as e:
                session.rollback()  # Rollback changes for current property if any error occurs
                logging.error(f"Error saving property {property_link} to database: {e}", exc_info=True)

        try:
            session.commit()  # Commit all changes for the batch
            logging.info("All properties processed. Changes committed successfully.")
        except Exception as e:
            session.rollback()
            logging.error(f"Error committing transaction: {e}", exc_info=True)


if __name__ == '__main__':
    # This block is for testing database operations directly if needed
    # You would typically call create_db_and_tables() and save_scraped_data_to_db()
    # from your main scraper script or a separate orchestration script.

    # 1. Create tables (run this once, or let it run on app startup if using FastAPI lifespan)


    # 2. Example of dummy data to test saving
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
            'street': '456 Demo Ave', 'city': 'Chicago', 'IL': 'IL', 'zip_code': '60602',
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
    save_scraped_data_to_db(dummy_scraped_data)
    logging.info("Database operations script finished.")