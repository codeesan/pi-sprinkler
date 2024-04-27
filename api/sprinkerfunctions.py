import sqlite3
import os
import settings
from gpiozero import DigitalOutputDevice

settings.init()

if settings.devmode:
    from gpiozero.pins.pigpio import PiGPIOFactory

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

def turn_on_valve(gpio:int):
    if settings.devmode:
        factory = PiGPIOFactory(host=settings.devip)
        valve = DigitalOutputDevice(gpio, pin_factory=factory)
    else:
        valve = DigitalOutputDevice(gpio)
    result = valve.on()
    return result

def turn_off_valve(gpio:int):
    if settings.devmode:
        factory = PiGPIOFactory(host=settings.devip)
        valve = DigitalOutputDevice(gpio, pin_factory=factory)
    else:
        valve = DigitalOutputDevice(gpio)
    result = valve.off()
    return result

def get_valve_status(gpio:int):
    return True