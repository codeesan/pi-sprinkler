from fastapi import FastAPI, Depends, Response, status
from fastapi.encoders import jsonable_encoder
from sprinkerfunctions import *
from sprinkerModels import Valve, ZoneName
from factory_reset import factory_reset
import settings

from pprint import pprint

app = FastAPI()

#figure out the pi version
settings.pi_version = sqlite_to_dict("select * from settings where key=\"pi_version\"")[0]['value']


@app.get("/healthz")
async def health():
    health = {
        "health": "I'm Alive", 
        "Dev Mode": settings.devmode,
        "Sprinker Dev IP" : settings.devip,
        "Raspberry Pi Version" :settings.pi_version,
        "Current BCM ": settings.current_bcm,
        }
    return health

#perform a factory reset on the device - basically reloads the base sql data
@app.post("/factoryreset", status_code=200)
def reset_to_factory_defaults(validate_intent:str, response: Response):
    result = factory_reset(validate_intent)
    if result == 200:
        return{"data: Factory Reset Complete"}
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return{"data":"Aborting Factory Reset - MUST SAY 'I want to reset'"}



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
    result = sqlite_to_dict("select pin from pins where pi_version={0} and pin not in (select pin from valves);".format(pi_version))
    return{"data" : result }



######### 
# Valves
#########
#get all the valves
@app.get("/valves")
def get_all_valves():
    result = sqlite_to_dict("select * from valves")
    return{"data":result}
#update valve
@app.put("/valves/{valve_id}")
def update_valve(valve: Valve, valve_id: int):
    update_valve_encoded = jsonable_encoder(valve)
    name = update_valve_encoded["name"]
    description = update_valve_encoded["description"]
    result = sqlite_put_post("update valves set name=\"{0}\", description=\"{1}\" where id={2}".format(name,description,valve_id))
    return {"data":result}
#add a valve
@app.post("/valves")
def add_valve(valve: Valve, pin: int):
    add_valve_encoded = jsonable_encoder(valve)
    name = add_valve_encoded["name"]
    description = add_valve_encoded["description"]
    result = sqlite_put_post("insert into valves(name,description,pin) values(\"{0}\",\"{1}\",{2})".format(name,description,pin))
    return{"data":result}

#operate a valve
@app.post("/valves/operate", status_code=200)
def operate_valve(valve:int, set_status:str, response:Response):
    
    #check for valid input
    if set_status == "on":
        #result = turn_on_valve(valve)
        result = turn_on_valve_2(valve)
    elif set_status == "off":
        result = turn_off_all_valves()
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return{"data":"Aborting - valid status for set is on or off"}
    
    if result == True:
        return{"data":"Valve {0} set to {1}. result: {2}".format(valve,set_status,result)}
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return{"data":"1 Aborting - Something went wrong. result: {0}".format(result)}
    
@app.get("/valves/checkstatus", status_code=200)
def check_valve_status(valve:int, response:Response):
    #result = read_valve_bus(valve)
    result = None
    return{"data": result }
    # bcm = sqlite_to_dict("select p.bcm from pins p left join valves v on p.pin = v.pin where v.id = {0} and p.pi_version = {1}".format(valve,settings.pi_version))[0]['bcm']
    # result = get_valve_status(bcm)
    # return{"data":[{"Valve":valve,"Status": result }]}
    # # else:
    # #     response.status_code = status.HTTP_400_BAD_REQUEST
    # #     return{"data":"Aborting - The Valve you are trying to check is not the current valve."}



@app.get("/valves/allstatus", status_code=200)
def get_status_of_all_valve_bcm():
    result = get_all_valve_bcm_status()
    return{"data": result}

########
# Zones
########

#get all the zone names
@app.get("/zone/names")
def get_all_zones():
    result = sqlite_to_dict("select * from zone_names")
    return{"data":result}
#add a zone name
@app.post("/zones/name/")
def add_zone_name(zone: ZoneName):
    add_zone_name_encoded = jsonable_encoder(zone)
    name = add_zone_name_encoded["name"]
    description = add_zone_name_encoded["description"]
    result = sqlite_put_post("insert into zone_names(\"name\",\"description\") values (\"{0}\", \"{1}\")".format(name, description))
    return{"data":result}

#update zone name by id
@app.put("/zones/names/{zone_id}")
def update_zone_name(zone_id: int, zone: ZoneName):
    update_zone_name_encoded = jsonable_encoder(zone)
    name = update_zone_name_encoded["name"]
    description = update_zone_name_encoded["description"]
    result = sqlite_put_post("update zone_names set name=\"{0}\", description=\"{1}\" where id={2}".format(name,description,zone_id))
    return{"data":result}

#remove a zone name
@app.delete("/zones/names", status_code=200)
def delete_zone_name(zone_id: int, response: Response):
    #check to see if there are any valves associated with the zone
    valves = sqlite_to_dict("select * from zones where zone_id={0}".format(zone_id))
    if valves == []:
        result = sqlite_put_post("delete from zone_names where id={0}".format(zone_id))
        return{"data": result}
    else:
        response.status_code = status.HTTP_400_BAD_REQUEST
        result = "Cannot delete zone name if valves are attached to zone."
        return{"data":result}

#get valves for a given zone
@app.get("/zones/valves")
def get_valves_for_a_zone(zone_id: int):
    result = sqlite_to_dict("select * from zones where zone_id = {0}".format(zone_id))
    return{"data":result}

#add valves to a zone
@app.post("/zones/valves")
def add_valve_to_zone(zone_id: int, valve_id:int):
    result = sqlite_put_post("insert into zones(zone_id, valve) values({0},{1})".format(zone_id,valve_id))
    return{"data":result}

#remove a valve from a zone
@app.delete("/zones/valves")
def remove_valve_from_zone(zone_id:int, valve_id:int):
    result = sqlite_put_post("delete from zones where zone_id={0} and valve={1}".format(zone_id,valve_id))
    return{"data":result}
