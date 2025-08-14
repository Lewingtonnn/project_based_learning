from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker

DATABASE_URL= "sqlite:///database.db"
engine= create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    with Session(engine) as session :
        try:
            yield session
        finally:
            session.close()

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    print("Database and tables created successfully.")

