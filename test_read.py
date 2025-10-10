import serial

ser = serial.Serial('/dev/serial0', 115200, timeout=0.5)
ser.write(b'\x02')  # 適当な1バイト送信
print(ser.read(10))
