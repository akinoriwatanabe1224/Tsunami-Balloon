# raw_get_values.py  (pyvesc を使わないパケット送受信テスト)
import serial
import time

PORT = "/dev/serial0"
BAUD = 115200

# COMM IDs:  (多くの実装では COMM_GET_VALUES = 4)
COMM_GET_VALUES = 4

# CRC16 テーブル版（Vedder の実装に合わせたテーブル式）
CRC16_TABLE = []
def _make_crc16_table():
    poly = 0x1021  # Vedder 実装はテーブルを使うバリエーションがある（この値で試す）
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
    """CRC-16 (table-driven). Vedderファームの crc16 実装に近いアルゴリズムを採用"""
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFF) ^ CRC16_TABLE[((crc >> 8) ^ b) & 0xFF]
    return crc & 0xFFFF

def build_packet(payload: bytes) -> bytes:
    """VESC の短パケットフォーマットでパケットを作る（payload はペイロードのみ）"""
    # 短パケット: start 0x02, 1バイト長, payload..., crc_hi, crc_lo, stop 0x03
    if len(payload) > 255:
        raise ValueError("payload too long for short packet")
    header = bytes([0x02, len(payload)])
    crc = crc16(payload)
    crc_bytes = bytes([(crc >> 8) & 0xFF, crc & 0xFF])
    return header + payload + crc_bytes + bytes([0x03])

def parse_reply(buf: bytes):
    # 単純に受け取った生データを表示して確認する関数
    print("Raw reply (len={}): {}".format(len(buf), buf.hex(' ')))
    # ここで必要なら、更にpayloadをパースして数値化できます（浮動小数変換など）
    # まずは生のバイト列を見て、どんな応答が返ってきているかを確かめるのが良いです。

ser = serial.Serial(PORT, BAUD, timeout=0.5)

try:
    while True:
        payload = bytes([COMM_GET_VALUES])  # 単純にコマンドIDだけ
        pkt = build_packet(payload)
        ser.write(pkt)
        time.sleep(0.05)
        data = ser.read(1024)
        if data:
            parse_reply(data)
        else:
            print("no reply")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("stop")
