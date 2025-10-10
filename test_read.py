import serial
from pyvesc.messages.getters import GetValues
from pyvesc.interface import encode, decode
import time

ser = serial.Serial("/dev/serial0", 115200, timeout=0.5)

ser.write(encode(GetValues()))  # リクエスト送信

time.sleep(0.1)  # 少し待つ

data = ser.read(256)  # 受信

print("Raw:", data)

msgs = list(decode(data))
print("Decoded:", msgs)
