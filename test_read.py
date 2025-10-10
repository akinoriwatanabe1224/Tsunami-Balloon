import time
import serial
from pyvesc.messages.getters import GetValues
from pyvesc.interface import encode, decode

PORT = "/dev/serial0"
BAUDRATE = 115200

ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

try:
    while True:
        # 値リクエストを送信
        ser.write(encode(GetValues()))
        
        # 受信バッファからデコード
        data = ser.read(100)  # 100バイト程度読む
        if data:
            for msg in decode(data):
                print(msg)  # VESCから返ってきたステータス
        
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
