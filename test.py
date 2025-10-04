import time
import serial
from pyvesc.messages.setters import SetDutyCycle
from pyvesc.interface import encode

PORT = "/dev/serial0"
BAUDRATE = 115200
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

def set_duty(duty: float):
    duty = max(-10.0, min(10.0, duty))
    duty_int = int(duty * 1000)  # 0～1000 に変換
    msg = SetDutyCycle(duty_int)
    ser.write(encode(msg))

try:
    while True:
        for d in [i/20 for i0 in range(21)]:
            set_duty(d*10)
            print(d)
            time.sleep(0.2)
        for d in [i/20 for i in range(20,-1,-1)]:
            set_duty(d*10)
            print(d)
            time.sleep(0.2)
except KeyboardInterrupt:
    set_duty(0)
    ser.close()
