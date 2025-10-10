from pyvesc import VESC
from pyvesc.messages import GetValues
import serial
import time

ser = serial.Serial("/dev/serial0", 115200, timeout=0.5)
vesc = VESC(serial_port=ser)

try:
    while True:
        values = vesc.get_values()
        print({
            'temp_fet': values.temp_fet,
            'temp_motor': values.temp_motor,
            'current_motor': values.current_motor,
            'current_in': values.current_in,
            'duty': values.duty_cycle
        })
        time.sleep(0.5)
except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
