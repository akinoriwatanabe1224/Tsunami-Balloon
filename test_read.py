import struct
import serial
import time

PORT = "/dev/serial0"
BAUD = 115200
COMM_GET_VALUES = 4  # VESC の GET_VALUES コマンド

# CRC16 テーブル作成
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
    """短パケット作成"""
    if len(payload) > 255:
        raise ValueError("Payload too long")
    header = bytes([0x02, len(payload)])
    crc = crc16(payload)
    crc_bytes = bytes([(crc >> 8) & 0xFF, crc & 0xFF])
    return header + payload + crc_bytes + bytes([0x03])

def extract_packets(buf):
    """受信バッファから短パケットをすべて抽出"""
    packets = []
    i = 0
    while i < len(buf)-4:  # 最低限 5 バイト以上必要
        if buf[i] == 0x02:  # start byte
            length = buf[i+1]
            end_index = i + 2 + length + 2 + 1  # payload + crc2 + stop
            if end_index <= len(buf) and buf[end_index-1] == 0x03:
                payload = buf[i+2:i+2+length]
                crc_received = (buf[i+2+length] << 8) | buf[i+2+length+1]
                if crc16(payload) == crc_received:
                    packets.append(payload)
                i = end_index
            else:
                break  # パケット途中の可能性
        else:
            i += 1
    return packets

def parse_getvalues(payload):
    """Vedder FW 6.xx 想定の GET_VALUES のパース"""
    if len(payload) < 18:
        return None
    temp_fet, temp_motor, current_motor, current_in, duty, rpm = struct.unpack('>hhiiih', payload[:18])
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

buffer = b''  # 受信バッファ

try:
    while True:
        # GET_VALUES コマンド送信
        pkt = build_packet(bytes([COMM_GET_VALUES]))
        ser.write(pkt)
        time.sleep(0.05)

        # 読み取り
        data = ser.read(1024)
        if data:
            buffer += data
            packets = extract_packets(buffer)
            # 正しく処理したパケット分だけバッファを削除
            consumed_len = 0
            for p in packets:
                parsed = parse_getvalues(p)
                if parsed:
                    print(parsed)
                consumed_len += len(p) + 5  # start + len + payload + crc2 + stop
            buffer = buffer[consumed_len:]
        else:
            print("no reply")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
