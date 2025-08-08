from fastapi import FastAPI, Depends
from sqlmodel import SQLModel, create_engine, Session
from database import get_session
from models import Users, Sources, Listings, Pricing_history

app= FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Real Estate API!"}

@app.post("/users/")
def create_user(user: Users, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user