import sqlite3
import os
import settings
from pprint import pprint
from smbus2 import SMBus


settings.init()
bus = SMBus

statuses = ["off", "on"]
def sqlite_to_dict(statement):
    result = []
    con = sqlite3.connect("sprinklers.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    #print(statement)x
    for row in cur.execute(statement):
     #   print(dict(row))
        result.append(dict(row))
    con.commit()
    con.close()
    return result

def sqlite_put_post(statement):
    result = []
    con = sqlite3.connect("sprinklers.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(statement + " RETURNING *; ")
    result = cur.fetchall()
    con.commit()
    con.close()
    return result

def turn_on_valve(port):
    print("Turn on Valve{0}".format(port) )
    #set the side of the relay to 1
    side = 1
    if port > 8:
        side = 2
        port -= 8
    #change to zero based index for address
    port -= 1
    shift = 1 << port
    this_address = 255 - shift
    print(this_address)
    if side == 2:
       result = bus.write_byte_data(0x27,0xff, this_address)
    else:
       result =  bus.write_byte_data(0x27,this_address,0xff)
    return result



def turn_off_all_valves():
    result = bus.write_byte_data(0x27,0xff,0xff)
    return result

        
# def turn_off_valve(bcm:int):
#     if settings.devmode:
#         pi = pigpio.pi(settings.devip)
#     else:
#         pi = pigpio.pi()
#     pi.write(bcm,0)
#     bcm_status = pi.read(bcm)
#     pi.stop()
#     return(True)
    
def get_valve_status(port:int):
    return True
# def get_valve_status(bcm:int):
#     if settings.devmode:
#         pi = pigpio.pi(settings.devip)
#     else:
#         pi = pigpio.pi()
#     bcm_callback = pi.callback(bcm,pigpio.EITHER_EDGE)
#     print("bcm_callback")
#     pprint(vars(bcm_callback))
#     bcm_status = statuses[pi.read(bcm)]
#     pi.stop()
#     return(bcm_status)
def get_all_valve_bcm_status():
    return True
# def get_all_valve_bcm_status():
#     #get a list of all valves in db  
#     valve_bcm = []
#     result = []
#     con = sqlite3.connect("sprinklers.db")
#     con.row_factory = sqlite3.Row
#     cur = con.cursor()
#     for row in cur.execute("select v.id, v.name, p.bcm from pins p left join valves v on p.pin = v.pin where p.pi_version = 4 and v.name NOTNULL ;"):
#         #print(dict(row))
#         valve_bcm.append(dict(row))
#     con.commit()
#     con.close()

#     if settings.devmode:
#         pi = pigpio.pi(settings.devip)
#     else:
#         pi = pigpio.pi()

#     for valve in valve_bcm:
#         #append the status to the valve
#         valve.update({"status": statuses[pi.read(valve['bcm'])]})
#         print(valve)
#         result.append(valve)

#     return result
    
