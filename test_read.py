import time
import serial
from pyvesc.interface import encode, decode
from pyvesc.messages import GetValues

PORT = "/dev/serial0"
BAUDRATE = 115200

ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

try:
    while True:
        # GetValues() のインスタンスを渡すのが正解
        ser.write(encode(GetValues()))

        # 受信データを読む
        data = ser.read(256)
        if data:
            for msg in decode(data):
                print(msg)

        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
