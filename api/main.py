from fastapi import FastAPI, Depends
from sprinkerfunctions import sqlite_to_dict


app = FastAPI()

@app.get("/")
async def root():
    return {"health": "I'm Alive"}

@app.get("/healthz")
async def health():
    return {"health": "I'm Alive"}

#given a pi version get all pin information
@app.get("/pi/pin/{pi_version}")
def get_all_pi_pin_info(pi_version:int):
    result = sqlite_to_dict("select id,pin,bcm,pi_version from pins where pi_version={0}".format(pi_version))    
    return{"data":result }

#given a pi version and pin return the pin information
@app.get("/pi/pin/{pi_version}/{pin}")
def get_pi_pin_info( pi_version:int, pin:int):
    result = sqlite_to_dict("select * from pins where pi_version={0} and pin={1}".format(pi_version,pin))
    return{"data" : result }

