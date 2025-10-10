import serial

ser = serial.Serial("/dev/serial0", 115200, timeout=1)
ser.write(b"\x02\x04\x00\x00\x00\x00")  # テスト送信
resp = ser.read(10)
print("Resp:", resp)
