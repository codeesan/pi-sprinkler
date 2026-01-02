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


relay_state = 0xFFFF
def turn_on_valve_2(port):
    """
    Turn on a valve (relay) by port number (1-16)
    LOW = ON, HIGH = OFF for relays
    """
    turn_off_all_valves()

    global relay_state
    
    print(f"Turn on Valve {port}")
    
    if port < 1 or port > 16:
        raise ValueError("Port must be between 1 and 16")
    
    # Convert to 0-based index (P0-P15)
    pin = port - 1
    
    # Turn on relay by clearing the bit (set to 0)
    relay_state &= ~(1 << pin)
    
    # Write new state
    low_byte = relay_state & 0xFF
    high_byte = (relay_state >> 8) & 0xFF
    
    print(f"Pin: P{pin}, State: 0x{relay_state:04X}")
    
    result = bus.write_byte_data(0x27, low_byte, high_byte)
    print(f"I2C Write Result: {result}")
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
    
    
def probe_i2c_registers(address: int = 0x27, regs=None):
    """Probe a list of I2C register addresses on the given device and return
    a dictionary mapping register -> read result (int) or exception string.

    This is defensive: hardware reads can raise IOError/OSError when a
    register isn't present. We catch exceptions and return the exception
    string so the caller can inspect which registers responded.
    """
    if regs is None:
        # common small-registers plus 0xff which the write code uses
        regs = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0xff]

    results = {}
    for r in regs:
        try:
            val = bus.read_byte_data(address, r)
            results[r] = val
        except Exception as e:
            # store the exception string so the caller can see failures
            results[r] = f"ERROR: {type(e).__name__}: {e}"
    return results


def read_both_sides(address: int = 0x27):
    """Convenience wrapper to read candidate registers for both sides/banks.

    Because the existing `turn_on_valve` code uses different register/value
    orders for side 1 vs side 2, it's unclear which register(s) map to the
    two 8-bit banks. This function probes a set of common registers and
    returns whatever values the device answers with so you can identify
    which registers correspond to "side 1" and "side 2".

    Returns a dict mapping register -> value or error string.
    """
    # If running in a dev mode where hardware isn't available, return
    # predictable dummy values to avoid exceptions.
    try:
        if getattr(settings, "devmode", False):
            return {0x00: 0xFF, 0x01: 0xFF}
    except Exception:
        # if settings doesn't have devmode, proceed to probe
        pass

    regs_to_try = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0xff]
    return probe_i2c_registers(address, regs_to_try)


def demo_probe_and_print(address: int = 0x27):
    """Small safe demo helper that prints probe results.

    Use this from a REPL or a small script to inspect what the expander
    returns for different register addresses. The function catches
    exceptions and prints them rather than raising.
    """
    results = read_both_sides(address)
    pprint(results)
    return results


def detect_bank_mapping(port: int, address: int = 0x27, regs=None, restore=True):
    """Auto-detect which I2C register and bit correspond to the given valve port.

    Procedure:
    - Probe a set of registers (using `regs` or defaults) before any change.
    - Toggle the valve on using existing `turn_on_valve(port)`.
    - Re-probe the same registers and compute differences.
    - Turn off all valves to restore state (if `restore` True).

    Returns a dict with:
    - before: {reg: val_or_error}
    - after: {reg: val_or_error}
    - diffs: {reg: {'before': val, 'after': val, 'xor': xor, 'changed_bits': [bit_indexes]}}
    - inferred_side: 1 or 2 (based on port > 8 logic)
    - probe_regs: list of registers probed

    Notes:
    - This performs an actual hardware write using `turn_on_valve`. If your
      environment sets `settings.devmode`, the function will still run but
      may use dev-safe behavior defined elsewhere.
    - If a register read raises an exception, the exception string is stored
      in the before/after maps and that register will not be considered for
      diffs.
    """
    if regs is None:
        regs = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0xff]

    result = {
        'probe_regs': regs,
        'before': {},
        'after': {},
        'diffs': {},
        'inferred_side': 1 if port <= 8 else 2,
    }

    # Probe before
    before = probe_i2c_registers(address, regs)
    result['before'] = before

    # Attempt to turn on the valve. Catch and record any errors but continue.
    try:
        turn_on_valve(port)
    except Exception as e:
        result.setdefault('errors', []).append(f"turn_on_valve error: {type(e).__name__}: {e}")

    # Probe after
    after = probe_i2c_registers(address, regs)
    result['after'] = after

    # Compute diffs (only for integer reads)
    for r in regs:
        b = before.get(r)
        a = after.get(r)
        # only compute diffs if both are ints
        if isinstance(b, int) and isinstance(a, int):
            xor = b ^ a
            changed_bits = []
            if xor != 0:
                for bit in range(8):
                    if xor & (1 << bit):
                        changed_bits.append(bit)
            result['diffs'][r] = {'before': b, 'after': a, 'xor': xor, 'changed_bits': changed_bits}
        else:
            # store the raw values if not ints
            result['diffs'][r] = {'before': b, 'after': a, 'xor': None, 'changed_bits': []}

    # Restore device state: turn off all valves (best-effort)
    if restore:
        try:
            turn_off_all_valves()
        except Exception as e:
            result.setdefault('errors', []).append(f"turn_off_all_valves error: {type(e).__name__}: {e}")

    return result

