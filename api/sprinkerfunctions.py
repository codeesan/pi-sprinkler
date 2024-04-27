import sqlite3
import os
import settings
from pprint import pprint

from gpiozero import DigitalOutputDevice
from gpiozero.pins.pigpio import PiGPIOFactory

settings.init()

#make valve persistant so it doesn't shut off when the function returns
valve = None

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

def turn_on_valve(bcm:int):
    if bcm == settings.current_bcm or settings.current_bcm == None:    
        global valve
        print("Valve ON")
        if not valve:
            if settings.devmode:
                factory = PiGPIOFactory(host=settings.devip)
                valve = DigitalOutputDevice(bcm, pin_factory=factory)
            else:
                valve = DigitalOutputDevice(bcm)
        valve.on()
        settings.current_bcm = bcm
        pprint(valve)
        print("valve property: {0}".format(valve.value))
        return True
    else:
        return False
    

def turn_off_valve(bcm:int):
    if bcm == settings.current_bcm or settings.current_bcm == None: 
        global valve
        print("Valve OFF")
        if not valve:
            if settings.devmode:
                factory = PiGPIOFactory(host=settings.devip)
                valve = DigitalOutputDevice(bcm, pin_factory=factory)
            else:
                valve = DigitalOutputDevice(bcm)
        valve.off()
        settings.current_bcm = None
        pprint(valve)
        print("valve property: {0}".format(valve.value))
        return True
    else:
        return False
    

def get_valve_status(bcm:int):
    print("Valve Status")
    if settings.devmode:
        factory = PiGPIOFactory(host=settings.devip)
        valve = DigitalOutputDevice(bcm, pin_factory=factory)
    else:
        valve = DigitalOutputDevice(bcm)
    pprint(valve)
    print("valve is_active: {0}".format(valve.is_active))
    print("valve status: {0}".format(valve.value))
    print("")
    print("")
    return True