import sqlite3
import os
import settings
from pprint import pprint
from smbus2 import SMBus


settings.init()
bus = SMBus(1)




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
    print("this address: {0}".format(this_address))
    if side == 2:
       result = bus.write_byte_data(0x27,0xff,this_address)
    else:
       result =  bus.write_byte_data(0x27,this_address,0xff)
    return result

def read_valve_bus(port:int):
    """
    Read the I2C device bytes that correspond to the given valve port and
    return a dict with raw reads and an interpreted status ("on"/"off").
    """
    side = 1
    orig_port = port
    if port > 8:
        side = 2
        port -= 8
    port -= 1
    shift = 1 << port
    this_address = 255 - shift

    reg_read = None
    val_read = None

    try:
        # Attempt to read the register that turn_on_valve sometimes uses as the register
        reg_read = bus.read_byte_data(0x27, this_address)
    except Exception:
        reg_read = None

    try:
        # Attempt to read the alternate register (0xff) used in the other branch
        val_read = bus.read_byte_data(0x27, 0xff)
    except Exception:
        val_read = None

    # Prefer val_read (used as the written value in side==2), fall back to reg_read
    raw = val_read if val_read is not None else reg_read

    if raw is None:
        return {"port": orig_port, "side": side, "this_address": this_address, "raw": None, "status": None, "error": "read failed"}

    # If the bit for this valve is 0 it's treated as "on" (matching turn_on_valve which writes a 0 bit)
    is_on = (raw & shift) == 0
    status = statuses[1] if is_on else statuses[0]

    return {
        "port": orig_port,
        "side": side,
        "this_address": this_address,
        "raw": raw,
        "bit_mask": shift,
        "status": status
    }

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
    
