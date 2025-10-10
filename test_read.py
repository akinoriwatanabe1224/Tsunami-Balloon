import serial
import time

COMM_GET_VALUES = 4

def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
    return crc

def build_get_values_packet():
    payload = bytes([COMM_GET_VALUES])
    length = len(payload)
    pkt = bytearray()
    pkt.append(2)           # STX
    if length >= 256:
        pkt.append(255)
        pkt.append(length - 255)
    else:
        pkt.append(length)
    pkt.extend(payload)
    pkt.append(crc8(payload))
    pkt.append(3)           # ETX
    return pkt

ser = serial.Serial("/dev/serial0", 115200, timeout=0.1)

ser.write(build_get_values_packet())
time.sleep(0.05)

if ser.in_waiting:
    data = ser.read(ser.in_waiting)
    print("RAW:", data)
else:
    print("No response")
