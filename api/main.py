from fastapi import FastAPI, Depends

from sqlalchemy.orm import Session
from pg_models import Pins;
from pg_database import get_db;


from pprint import pprint



app = FastAPI()

@app.get("/")
async def root():
    return {"health": "I'm Alive"}

@app.get("/healthz")
async def health():
    return {"health": "I'm Alive"}

#given a pi version get all pin information
@app.get("/pi/pin")
def get_all_pi_pin_info(pi_version:int, db: Session = Depends(get_db)):
    result = db.query(Pins).filter(Pins.pi_version==pi_version)
    return{"data": result.all()}

#given a pi version and pin return the pin information
@app.get("/pi/pin/{pi_version}/{pin}")
def get_pi_pin_info( pi_version:int, pin:int, db: Session = Depends(get_db) ):
    result = db.query(Pins).filter(Pins.pi_version==pi_version,Pins.pin==pin)
    return{"data" : result.all()}

