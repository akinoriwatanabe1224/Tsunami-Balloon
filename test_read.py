# read_vesc_values.py
import serial
from pyvesc import get_values

PORT = "/dev/serial0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=0.5)

try:
    while True:
        values = get_values(ser)  # VESCから生データを取得してパース
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
