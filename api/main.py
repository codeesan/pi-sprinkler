from fastapi import FastAPI, Depends

from sqlalchemy.orm import Session
from pg_models import Pins;
from pg_database import get_db;


from pprint import pprint



app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

#given a pi version and pin return the bcm
@app.get("/pi/bcm/{pi_version}/{pin}")
def get_pi_bcm( pi_version:int, pin:int, db: Session = Depends(get_db) ):
    result = db.query(Pins).filter(Pins.pi_version==pi_version,Pins.pin==pin)
    return{"data" : result.all()}

