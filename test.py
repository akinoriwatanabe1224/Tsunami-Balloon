import time
import serial
from pyvesc.messages.setters import SetDutyCycle  # pyvesc 1.0.5 構造
from pyvesc.interface import encode

PORT = "/dev/serial0"
BAUDRATE = 115200

ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

def set_duty(duty: float):
    duty = max(-1.0, min(1.0, duty))
    msg = SetDutyCycle(duty)
    ser.write(encode(msg))

try:
    while True:
        for d in [i/20 for i in range(21)]:
            set_duty(d)
            print(d)
            time.sleep(0.2)
        for d in [i/20 for i in range(20,-1,-1)]:
            set_duty(d)
            print(d)
            time.sleep(0.2)
except KeyboardInterrupt:
    set_duty(0)
    ser.close()
