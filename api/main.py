from fastapi import FastAPI, Depends
from fastapi.encoders import jsonable_encoder
from sprinkerfunctions import sqlite_to_dict, sqlite_put
from sprinkerModels import Valve
from pprint import pprint

app = FastAPI()

@app.get("/")
async def root():
    return {"health": "I'm Alive"}

@app.get("/healthz")
async def health():
    return {"health": "I'm Alive"}

##########
### Pins
##########
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

######### 
# Valves
#########

@app.get("/valves")
def get_all_valves():
    result = sqlite_to_dict("select * from valves")
    return{"data":result}

@app.put("/valves/{valve_id}")
def update_valve(valve: Valve, valve_id: int):
    update_valve_encoded = jsonable_encoder(valve)
    name = update_valve_encoded["name"]
    description = update_valve_encoded["description"]
    
    result = sqlite_put("valves",valve_id,"update valves set name='{0}', description='{1}' where id={2}".format(name,description,valve_id))

    return result
