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
    global valve
    print("Valve ON")
    
    if not valve:
        if settings.devmode:
            factory = PiGPIOFactory(host=settings.devip)
            valve = DigitalOutputDevice(bcm, pin_factory=factory)
        else:
            valve = DigitalOutputDevice(bcm)
    valve.on()
    pprint(valve)
    print("valve property: {0}".format(valve.value))
    return True

def turn_off_valve(bcm:int):
    global valve
    print("Valve OFF")
    if not valve:
        if settings.devmode:
            factory = PiGPIOFactory(host=settings.devip)
            valve = DigitalOutputDevice(bcm, pin_factory=factory)
        else:
            valve = DigitalOutputDevice(bcm)
    valve.off()
    pprint(valve)
    print("valve property: {0}".format(valve.value))
    return True

def get_valve_status(bcm:int):
    global valve
    print("Valve Status")
    if not valve:
        if settings.devmode:
            factory = PiGPIOFactory(host=settings.devip)
            valve = DigitalOutputDevice(bcm, pin_factory=factory)
        else:
            valve = DigitalOutputDevice(bcm)
    pprint(valve)
    print("valve property: {0}".format(valve.value))
    return True