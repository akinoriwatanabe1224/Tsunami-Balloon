import struct
import serial
import time

PORT = "/dev/serial0"
BAUD = 115200
COMM_GET_VALUES = 4

# =====================
# CRC16計算
# =====================
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
    if len(payload) <= 256:
        # ショートパケット
        header = bytes([0x02, len(payload)])
    else:
        # ロングパケット（通常使わない）
        header = bytes([0x03, (len(payload) >> 8) & 0xFF, len(payload) & 0xFF])
    
    crc = crc16(payload)
    crc_bytes = bytes([(crc >> 8) & 0xFF, crc & 0xFF])
    return header + payload + crc_bytes + bytes([0x03])

# =====================
# パケット抽出（改善版）
# =====================
def extract_packets(buf):
    """バッファから完全なパケットを抽出"""
    packets = []
    consumed = 0
    i = 0
    
    while i < len(buf):
        # スタートバイトを探す
        if buf[i] == 0x02:  # ショートパケット
            if i + 2 > len(buf):
                break
            length = buf[i + 1]
            packet_len = 2 + length + 2 + 1  # start(1) + len(1) + payload + crc(2) + stop(1)
            
            if i + packet_len > len(buf):
                break
            
            if buf[i + packet_len - 1] == 0x03:
                payload = buf[i + 2:i + 2 + length]
                crc_received = (buf[i + 2 + length] << 8) | buf[i + 2 + length + 1]
                
                if crc16(payload) == crc_received:
                    packets.append(payload)
                    consumed = i + packet_len
                    i = consumed
                else:
                    print(f"[CRC ERROR] 受信: {crc_received:04x}, 計算: {crc16(payload):04x}")
                    i += 1
            else:
                i += 1
        else:
            i += 1
    
    return packets, buf[consumed:]

# =====================
# GET_VALUES パース
# =====================
def parse_getvalues(payload):
    """
    VESC 6.x GET_VALUES応答
    最初のバイトがコマンドIDの場合があるので確認
    """
    try:
        # コマンドIDがエコーバックされる場合
        if payload[0] == COMM_GET_VALUES:
            payload = payload[1:]
        
        if len(payload) < 46:  # VESC 6.xは通常46バイト以上
            print(f"[WARN] ペイロード長が短い: {len(payload)} bytes")
            print(f"[HEX] {payload.hex()}")
            return None
        
        # VESC 6.x フォーマット（FW 6.0+）
        offset = 0
        temp_fet = struct.unpack('>h', payload[offset:offset+2])[0] / 10.0
        offset += 2
        temp_motor = struct.unpack('>h', payload[offset:offset+2])[0] / 10.0
        offset += 2
        current_motor = struct.unpack('>i', payload[offset:offset+4])[0] / 100.0
        offset += 4
        current_in = struct.unpack('>i', payload[offset:offset+4])[0] / 100.0
        offset += 4
        id_val = struct.unpack('>i', payload[offset:offset+4])[0] / 100.0
        offset += 4
        iq_val = struct.unpack('>i', payload[offset:offset+4])[0] / 100.0
        offset += 4
        duty_now = struct.unpack('>h', payload[offset:offset+2])[0] / 1000.0
        offset += 2
        rpm = struct.unpack('>i', payload[offset:offset+4])[0]
        offset += 4
        v_in = struct.unpack('>h', payload[offset:offset+2])[0] / 10.0
        offset += 2
        amp_hours = struct.unpack('>i', payload[offset:offset+4])[0] / 10000.0
        offset += 4
        amp_hours_charged = struct.unpack('>i', payload[offset:offset+4])[0] / 10000.0
        offset += 4
        watt_hours = struct.unpack('>i', payload[offset:offset+4])[0] / 10000.0
        offset += 4
        watt_hours_charged = struct.unpack('>i', payload[offset:offset+4])[0] / 10000.0
        offset += 4
        tachometer = struct.unpack('>i', payload[offset:offset+4])[0]
        offset += 4
        tachometer_abs = struct.unpack('>i', payload[offset:offset+4])[0]
        
        return {
            'temp_fet': temp_fet,
            'temp_motor': temp_motor,
            'current_motor': current_motor,
            'current_in': current_in,
            'id': id_val,
            'iq': iq_val,
            'duty': duty_now,
            'rpm': rpm,
            'v_in': v_in,
            'amp_hours': amp_hours,
            'amp_hours_charged': amp_hours_charged,
            'watt_hours': watt_hours,
            'watt_hours_charged': watt_hours_charged,
            'tachometer': tachometer,
            'tachometer_abs': tachometer_abs
        }
    except Exception as e:
        print(f"[ERROR] パース失敗: {e}")
        print(f"[HEX] {payload.hex()}")
        return None

# =====================
# メイン
# =====================
def main():
    print("VESC UART通信を開始...")
    print(f"ポート: {PORT}, ボーレート: {BAUD}")
    
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.5)
        time.sleep(0.1)  # 接続安定化
        print("接続成功！\n")
    except Exception as e:
        print(f"シリアルポート接続エラー: {e}")
        return
    
    buffer = b''
    request_count = 0
    success_count = 0
    
    try:
        while True:
            # GET_VALUESリクエスト送信
            pkt = build_packet(bytes([COMM_GET_VALUES]))
            ser.write(pkt)
            request_count += 1
            
            # 応答待ち
            time.sleep(0.05)
            
            # データ受信
            data = ser.read(ser.in_waiting or 256)
            
            if data:
                buffer += data
                packets, buffer = extract_packets(buffer)
                
                for payload in packets:
                    parsed = parse_getvalues(payload)
                    if parsed:
                        success_count += 1
                        print(f"\n--- データ #{success_count} ---")
                        print(f"FET温度:    {parsed['temp_fet']:.1f}°C")
                        print(f"モーター温度: {parsed['temp_motor']:.1f}°C")
                        print(f"モーター電流: {parsed['current_motor']:.2f}A")
                        print(f"入力電流:   {parsed['current_in']:.2f}A")
                        print(f"入力電圧:   {parsed['v_in']:.1f}V")
                        print(f"Duty比:     {parsed['duty']:.3f}")
                        print(f"RPM:        {parsed['rpm']}")
                        print(f"電力量:     {parsed['watt_hours']:.3f}Wh")
            else:
                print(f"[{request_count}] 応答なし")
            
            # バッファが大きくなりすぎたらクリア
            if len(buffer) > 1000:
                print(f"[WARN] バッファクリア ({len(buffer)} bytes)")
                buffer = b''
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print(f"\n\n停止しました")
        print(f"リクエスト: {request_count}, 成功: {success_count}")
    finally:
        ser.close()

if __name__ == "__main__":
    main()