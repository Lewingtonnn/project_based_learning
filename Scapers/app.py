from fastapi import FastAPI, Depends, Header, HTTPException
from sqlalchemy.sql.annotation import Annotated
from sqlmodel import Session, select
from dbmodels import Property, Pricing_and_floor_plans
from contextlib import asynccontextmanager
from db_ops import getting_session


class Authorisation():
    async def __call__(self, x_token:Annotated[str, Header()]) ->str:
        if x_token != "lewis7205":
            raise HTTPException(status_code=403, detail="Invalid Token")
        else:
            return x_token

@asynccontextmanager
async def permission():
    Authorisation()
    return {"Hi there, Welcome"}

app=FastAPI()


app.get("/")
async def welcome():
    return {" Message: Welcome to the Real estate API"}

app.get("/All-listings")
async def get_listings(session: Session=Depends(getting_session(), Authorisation)):
    statement=select(Property)
    all_properties= session.exec(statement).all()
    return all_properties

app.get("/{property_id}/Floor-plans")
async def get_floor_plans(property_id: int ,session:Session= Depends(getting_session(), Authorisation)):
    statement=select(Pricing_and_floor_plans).where(Pricing_and_floor_plans.property_id == property_id)
    floor_plans=session.exec(statement).all
    return floor_plans

app.get("/{x}/top-x-most-affordable-properties")
async def get_top_x_most_affordable_properties(x: int, session:Session= Depends(getting_session,Authorisation)):
    statement=select(Pricing_and_floor_plans).order_by(Pricing_and_floor_plans.base_rent.asc).limit(x)
    properties=session.exec(statement).all
    return properties

app.get("/{x}/top-x-most-expensive-properties")
async def get_top_x_most_expensive_properties(x: int, session:Session= Depends(getting_session,Authorisation)):
    statement=select(Pricing_and_floor_plans).order_by(Pricing_and_floor_plans.base_rent.desc).limit(x)
    properties=session.exec(statement).all
    return properties

@app.get("/this-weeks-listings")
def get_this_weeks_listings(session: Session = Depends(getting_session)):
    from datetime import datetime, timedelta
    one_week_ago = datetime.now() - timedelta(days=7)
    statement = select(Property).where(Property.timestamp >= one_week_ago)
    properties = session.exec(statement).all()
    return properties


