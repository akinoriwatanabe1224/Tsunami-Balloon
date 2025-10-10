import serial
import time

ser = serial.Serial("/dev/serial0", 115200, timeout=1)

# GetValuesコマンドはバイト 0x04
ser.write(b'\x04')
time.sleep(1)
data = ser.read(ser.in_waiting)
print(data)
