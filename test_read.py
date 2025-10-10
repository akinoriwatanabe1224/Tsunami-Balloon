# read_vesc.py
import serial
from pyvesc import VESC
from pyvesc.VESC import GetValues

# シリアルポート
PORT = "/dev/serial0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=0.5)
vesc = VESC(serial_port=ser)

try:
    while True:
        values = vesc.getValues()
        print({
            'temp_fet': values.temp_fet,       # °C
            'temp_motor': values.temp_motor,   # °C
            'current_motor': values.current_motor,  # A
            'current_in': values.current,           # A
            'duty': values.duty
        })
except KeyboardInterrupt:
    ser.close()
    print("Stopped")
