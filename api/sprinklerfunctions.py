import sqlite3
import os
import time
from pprint import pprint
from smbus2 import SMBus, i2c_msg

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


# ---------------------------------------------------------------------------
# PCF8575 relay board -- valve control
#
# Hardware configuration:
#   I2C bus:     1
#   I2C address: 0x27 (A0-A2 all HIGH)
#   Relay logic: active-LOW  (bit=0 -> relay ON, bit=1 -> relay OFF)
#   Port layout: data[0] = P0-P7  (valves 0-7,  low byte)
#                data[1] = P8-P15 (valves 8-15, high byte)
#
# Reads and writes use i2c_rdwr / i2c_msg -- no register byte prepended.
# ---------------------------------------------------------------------------

_I2C_BUS = 1
_I2C_ADDRESS = 0x27
_NUM_VALVES = 16
_ALL_OFF_STATE = 0xFFFF  # all bits HIGH = all relays OFF


class PCF8575:
    """Minimal driver for the PCF8575 16-bit I/O expander relay board."""

    def __init__(self, bus_number: int = _I2C_BUS, address: int = _I2C_ADDRESS) -> None:
        self.address = address
        self.bus = SMBus(bus_number)

    def _read_raw(self) -> int:
        """Return the current 16-bit port state (no register byte sent)."""
        read = i2c_msg.read(self.address, 2)
        self.bus.i2c_rdwr(read)
        data = list(read)
        return data[0] | (data[1] << 8)

    def _write_raw(self, state: int) -> None:
        """Write a 16-bit port state. low byte = P0-P7, high byte = P8-P15."""
        low = state & 0xFF
        high = (state >> 8) & 0xFF
        write = i2c_msg.write(self.address, [low, high])
        self.bus.i2c_rdwr(write)

    @staticmethod
    def _validate_valve(valve: int) -> None:
        if not (0 <= valve < _NUM_VALVES):
            raise ValueError(f"valve must be 0-{_NUM_VALVES - 1}, got {valve!r}")

    def get_all_valve_status(self) -> list[dict]:
        """Read the state of all 16 valves.

        Returns a list of 16 dicts in ascending valve order:
            [{"valve": 0, "status": "ON"|"OFF"}, ...]

        Active-LOW: bit=0 -> "ON", bit=1 -> "OFF".
        """
        state = self._read_raw()
        result = []
        for valve in range(_NUM_VALVES):
            bit = (state >> valve) & 1
            result.append({"valve": valve, "status": "OFF" if bit else "ON"})
        return result

    def turn_off_all_valves(self) -> bool:
        """Drive every pin HIGH (all relays OFF). Returns True on success."""
        self._write_raw(_ALL_OFF_STATE)
        return True

    def turn_on_valve(self, valve: int) -> None:
        """Turn ON one valve (pin LOW) without changing any other valve.

        Reads current state, clears the target bit, writes back.
        """
        self._validate_valve(valve)
        state = self._read_raw()
        state &= ~(1 << valve)   # clear bit -> pin LOW -> relay ON
        self._write_raw(state)

    def turn_off_valve(self, valve: int) -> None:
        """Turn OFF one valve (pin HIGH) without changing any other valve.

        Reads current state, sets the target bit, writes back.
        """
        self._validate_valve(valve)
        state = self._read_raw()
        state |= (1 << valve)    # set bit -> pin HIGH -> relay OFF
        self._write_raw(state)

    def get_valve_status(self, valve: int) -> dict:
        """Return the status of a single valve.

        Args:
            valve: Valve number 0-15.

        Returns:
            {"valve": <int>, "status": "ON"|"OFF"}

        Active-LOW: bit=0 -> "ON", bit=1 -> "OFF".
        """
        self._validate_valve(valve)
        state = self._read_raw()
        bit = (state >> valve) & 1
        return {"valve": valve, "status": "OFF" if bit else "ON"}

    def get_active_valves(self) -> list[int]:
        """Return a list of valve numbers (0-15) that are currently ON.

        Active-LOW: a valve is ON when its bit is 0.
        Returns an empty list when no valves are on.
        """
        state = self._read_raw()
        return [v for v in range(_NUM_VALVES) if not ((state >> v) & 1)]

    def is_any_valve_on(self) -> bool:
        """Return True if at least one valve is currently ON.

        Active-LOW: any bit that is 0 means that relay is energised.
        Equivalent to checking whether the 16-bit state differs from 0xFFFF.
        """
        return self._read_raw() != _ALL_OFF_STATE

    def run_valve(self, valve: int, seconds: float) -> None:
        """Turn a valve ON, hold for ``seconds``, then turn it OFF.

        Args:
            valve:   Valve number 0-15.
            seconds: Duration to keep the valve open (may be fractional).

        Raises:
            ValueError: if valve is outside 0-15.
        """
        self._validate_valve(valve)
        self.turn_on_valve(valve)
        try:
            time.sleep(seconds)
        finally:
            self.turn_off_valve(valve)


# Single shared instance -- SMBus opened once at import time.
_pcf = PCF8575(bus_number=_I2C_BUS, address=_I2C_ADDRESS)


def get_all_valve_status() -> list[dict]:
    """Return the status of all 16 valves as a list of dicts.

    Example::

        [{"valve": 0, "status": "ON"}, {"valve": 1, "status": "OFF"}, ...]
    """
    return _pcf.get_all_valve_status()


def turn_off_all_valves() -> bool:
    """Turn every valve OFF (all relay coils de-energised). Returns True."""
    return _pcf.turn_off_all_valves()


def turn_on_valve(valve: int) -> None:
    """Turn ON a single valve (0-15) while leaving all others unchanged."""
    _pcf.turn_on_valve(valve)


def turn_off_valve(valve: int) -> None:
    """Turn OFF a single valve (0-15) while leaving all others unchanged."""
    _pcf.turn_off_valve(valve)


def get_valve_status(valve: int) -> dict:
    """Return the status of a single valve (0-15) as a dict.

    Example::

        {"valve": 3, "status": "ON"}
    """
    return _pcf.get_valve_status(valve)


def get_active_valves() -> list[int]:
    """Return a list of valve numbers (0-15) that are currently ON.

    Example::

        [0, 4, 12]  # valves 0, 4, and 12 are open
    """
    return _pcf.get_active_valves()


def is_any_valve_on() -> bool:
    """Return True if at least one valve is currently ON, False if all are OFF."""
    return _pcf.is_any_valve_on()


def run_valve(valve: int, seconds: float) -> None:
    """Turn valve ON, wait ``seconds``, then turn it OFF.

    Args:
        valve:   Valve number 0-15.
        seconds: Duration to hold the valve open (may be fractional).
    """
    _pcf.run_valve(valve, seconds)
