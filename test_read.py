import struct
import serial
import time

PORT = "/dev/serial0"
BAUD = 115200

COMM_GET_VALUES = 4  # VESC の GET_VALUES コマンド

# CRC16 テーブルを作る
CRC16_TABLE = []
def _make_crc16_table():
    poly = 0x1021
    table = []
    for i in range(256):
        crc = 0
        c = i << 8
        for _ in range(8):
            if (crc ^ c) & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
            c = (c << 1) & 0xFFFF
        table.append(crc)
    return table

CRC16_TABLE = _make_crc16_table()

def crc16(data: bytes) -> int:
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFF) ^ CRC16_TABLE[((crc >> 8) ^ b) & 0xFF]
    return crc & 0xFFFF

def build_packet(payload: bytes) -> bytes:
    if len(payload) > 255:
        raise ValueError("Payload too long")
    header = bytes([0x02, len(payload)])
    crc = crc16(payload)
    crc_bytes = bytes([(crc >> 8) & 0xFF, crc & 0xFF])
    return header + payload + crc_bytes + bytes([0x03])

def parse_getvalues(buf):
    length = buf[1]
    payload = buf[2:2+length]
    temp_fet, temp_motor, current_motor, current_in, duty, rpm = struct.unpack('>hhiiih', payload[:20])
    temp_fet /= 10
    temp_motor /= 10
    current_motor /= 100
    current_in /= 100
    duty /= 1000
    return {
        'temp_fet': temp_fet,
        'temp_motor': temp_motor,
        'current_motor': current_motor,
        'current_in': current_in,
        'duty': duty,
        'rpm': rpm
    }

# シリアルオープン
ser = serial.Serial(PORT, BAUD, timeout=0.5)

try:
    while True:
        pkt = build_packet(bytes([COMM_GET_VALUES]))
        ser.write(pkt)
        time.sleep(0.05)
        data = ser.read(1024)
        if data:
            parsed = parse_getvalues(data)
            print(parsed)
        else:
            print("no reply")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
