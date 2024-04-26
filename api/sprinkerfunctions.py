import sqlite3
from gpiozero import DigitalOutputDevice
import os

def sqlite_to_dict(statement):
    result = []
    con = sqlite3.connect("sprinklers.db")
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    print(statement)
    for row in cur.execute(statement):
        print(dict(row))
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

# def turn_on_pin(bcm:int ):
#     led = DigitalOutputDevice(17)
#     led.on()
#     led.off()

def is_devmode():
    return os.environ.get("SPRINKLER_DEV",False)

