# vesc_temp_current.py
import struct
import serial
import time

PORT = "/dev/serial0"
BAUD = 115200
COMM_GET_VALUES = 4  # VESC GET_VALUES コマンド

# =====================
# CRC16 計算
# =====================
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

# =====================
# パケット作成
# =====================
def build_packet(payload: bytes) -> bytes:
    if len(payload) > 255:
        raise ValueError("Payload too long")
    header = bytes([0x02, len(payload)])
    crc = crc16(payload)
    crc_bytes = bytes([(crc >> 8) & 0xFF, crc & 0xFF])
    return header + payload + crc_bytes + bytes([0x03])

# =====================
# パケット抽出
# =====================
def extract_packets(buf):
    packets = []
    i = 0
    while i < len(buf) - 4:
        if buf[i] == 0x02:
            length = buf[i+1]
            end_index = i + 2 + length + 2 + 1
            if end_index <= len(buf) and buf[end_index-1] == 0x03:
                payload = buf[i+2:i+2+length]
                crc_received = (buf[i+2+length] << 8) | buf[i+2+length+1]
                if crc16(payload) == crc_received:
                    packets.append(payload)
                i = end_index
            else:
                break
        else:
            i += 1
    return packets

# =====================
# GET_VALUES パース（温度と電流のみ）
# =====================
def parse_getvalues(payload):
    """Vedder VESC 6.xx 想定（温度・電流のみ）"""
    if len(payload) < 12:  # temp_fet(2)+temp_motor(2)+current_motor(4)+current_in(4)
        return None

    # little-endian に変更
    temp_fet, temp_motor, current_motor, current_in , duty = struct.unpack('>hhiih', payload[:14])


    return {
        'temp_fet': temp_fet / 10,       # °C
        'temp_motor': temp_motor / 10,   # °C
        'current_motor': current_motor / 100,  # A
        'current_in': current_in / 100,        # A
         'duty': duty / 1000
    }

# =====================
# シリアル初期化
# =====================
ser = serial.Serial(PORT, BAUD, timeout=0.5)
buffer = b''

# =====================
# メインループ
# =====================
try:
    while True:
        pkt = build_packet(bytes([COMM_GET_VALUES]))
        ser.write(pkt)
        time.sleep(0.05)

        data = ser.read(1024)
        if data:
            buffer += data
            packets = extract_packets(buffer)
            consumed_len = 0
            for p in packets:
                parsed = parse_getvalues(p)
                if parsed:
                    print(parsed)
                consumed_len += len(p) + 5
            buffer = buffer[consumed_len:]
        else:
            print("no reply")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
