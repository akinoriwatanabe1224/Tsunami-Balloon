import time
import serial
from pyvesc.messages.setters import SetDutyCycle
from pyvesc.interface import encode

PORT = "/dev/serial0"
BAUDRATE = 115200
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

def set_duty(duty: float):
    duty = max(-100.0, min(100.0, duty))
    duty_int = int(duty * 1000)  # 0～1000 に変換
    msg = SetDutyCycle(duty_int)
    ser.write(encode(msg))
max_duty = 10
try:
    while True:
        for d in [i/max_duty for i in range(max_duty+1)]:
            set_duty(d*max_duty)
            print(d*max_duty)
            time.sleep(0.2)
        for d in [i/max_duty for i in range(max_duty,-1,-1)]:
            set_duty(d*max_duty)
            print(d*max_duty)
            time.sleep(0.2)
except KeyboardInterrupt:
    set_duty(0)
    ser.close()
