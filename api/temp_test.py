"""
Read and display status of all 16 relays on PCF8575
"""

from smbus2 import SMBus
import time

class PCF8575:
    def __init__(self, bus_number=1, address=0x27):
        self.bus = SMBus(bus_number)
        self.address = address

    def read_all(self):
        """Read 16-bit value from PCF8575 using i2c_rdwr"""
        # Read 2 bytes from PCF8575
        from smbus2 import i2c_msg
        read = i2c_msg.read(self.address, 2)
        self.bus.i2c_rdwr(read)
        data = list(read)
        # Combine bytes: data[0] is low byte (P0-P7), data[1] is high byte (P8-P15)
        return data[0] | (data[1] << 8)

    def digital_read(self, pin):
        """Read individual pin state (pin 0-15)"""
        data = self.read_all()
        return (data >> pin) & 1

    def get_relay_status(self, pin):
        """Get relay status as ON/OFF (remember: LOW=ON, HIGH=OFF)"""
        state = self.digital_read(pin)
        return "OFF" if state else "ON"


def main():
    # Initialize PCF8575
    pcf8575 = PCF8575(bus_number=1, address=0x27)

    print("Reading status of all 16 relays...")
    print("=" * 50)

    try:
        # Read all bits at once
        state = pcf8575.read_all()
        print(f"\nRaw 16-bit value: 0x{state:04X}")
        print(f"Binary: {state:016b}")
        print("-" * 50)

        for relay in range(16):
            bit_value = (state >> relay) & 1
            status = "OFF" if bit_value else "ON"
            print(f"Relay {relay:2d} (P{relay:2d}): {status:3s} (bit: {bit_value})")

        # Show summary
        print("\n" + "=" * 50)
        relays_on = [i for i in range(16) if not ((state >> i) & 1)]
        relays_off = [i for i in range(16) if ((state >> i) & 1)]

        print(f"Relays ON:  {relays_on if relays_on else 'None'}")
        print(f"Relays OFF: {relays_off if relays_off else 'None'}")

    except Exception as e:
        print(f"Error reading from PCF8575: {e}")
        print("\nTrying alternative read method...")

        # Alternative: use read_i2c_block_data
        try:
            data = pcf8575.bus.read_i2c_block_data(pcf8575.address, 0, 2)
            state = data[0] | (data[1] << 8)
            print(f"Raw value: 0x{state:04X} (binary: {state:016b})")
        except Exception as e2:
            print(f"Alternative method also failed: {e2}")


if __name__ == "__main__":
    main()