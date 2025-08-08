from sqlmodel import SQLModel, create_engine, Session
from models import Users, Sources, Listings, Pricing_history
from datetime import datetime, UTC
DATABASE_URL= "sqlite:///./database.db"

engine= create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session :
        yield session

SQLModel.metadata.create_all(engine)



print("Database and tables created successfully.")