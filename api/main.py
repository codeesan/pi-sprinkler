from fastapi import FastAPI, Depends
from fastapi.encoders import jsonable_encoder
from sprinkerfunctions import sqlite_to_dict, sqlite_put_post
from sprinkerModels import Valve, ZoneName
from factory_reset import factory_reset
from pprint import pprint

app = FastAPI()

@app.get("/")
async def root():
    return {"health": "I'm Alive"}

@app.get("/healthz")
async def health():
    return {"health": "I'm Alive"}

@app.post("/factoryreset")
def reset_to_factory_defaults(validate_intent:str):
    result = factory_reset(validate_intent)
    return{"data":result}

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

#given a pi version return pins not in use by valves
@app.get("/pi/pinsavailable/{pi_version}")
def get_available_pins( pi_version:int):
    print("made it this far")
    result = sqlite_to_dict("select pin from pins where pi_version={0} and pin not in (select pin from valves);".format(pi_version))
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
    result = sqlite_put_post("update valves set name=\"{0}\", description=\"{1}\" where id={2}".format(name,description,valve_id))
    return {"data":result}


########
# Zones
########

@app.get("/zone/names")
def get_all_zones():
    result = sqlite_to_dict("select * from zone_names")
    return{"data":result}

@app.post("/zones/name/")
def add_zone_name(zone: ZoneName):
    add_zone_name_encoded = jsonable_encoder(zone)
    name = add_zone_name_encoded["name"]
    description = add_zone_name_encoded["description"]
    result = sqlite_put_post("insert into zone_names(\"name\",\"description\") values (\"{0}\", \"{1}\")".format(name, description))
    return{"data":result}

@app.put("/zones/names/{zone_id}")
def update_zone_name(zone_id: int, zone: ZoneName):
    update_zone_name_encoded = jsonable_encoder(zone)
    name = update_zone_name_encoded["name"]
    description = update_zone_name_encoded["description"]
    result = sqlite_put_post("update zone_names set name=\"{0}\", description=\"{1}\" where id={2}".format(name,description,zone_id))
    return{"data":result}


