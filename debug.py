import serial
import time
import sys

PORT = "/dev/serial0"
BAUD = 115200

def hex_dump(data, label=""):
    """データをHEX+ASCIIで表示"""
    if label:
        print(f"\n{'='*60}")
        print(f"{label}")
        print('='*60)
    
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        print(f"{i:04x}  {hex_part:<48}  {ascii_part}")
    print(f"Total: {len(data)} bytes\n")

def test_connection():
    """シリアルポート接続テスト"""
    print("=== シリアルポート接続テスト ===\n")
    
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1.0)
        print(f"✓ ポート {PORT} をボーレート {BAUD} で開きました")
        print(f"  - Bytesize: {ser.bytesize}")
        print(f"  - Parity: {ser.parity}")
        print(f"  - Stopbits: {ser.stopbits}")
        print(f"  - Timeout: {ser.timeout}s")
        return ser
    except Exception as e:
        print(f"✗ 接続失敗: {e}")
        return None

def test_raw_read(ser, duration=3):
    """生データ読み取りテスト"""
    print(f"\n=== 生データ受信テスト ({duration}秒間) ===\n")
    print("VESCが自発的にデータを送信しているか確認...")
    
    ser.reset_input_buffer()
    start = time.time()
    total_bytes = 0
    
    while time.time() - start < duration:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            total_bytes += len(data)
            hex_dump(data, f"受信データ ({len(data)} bytes)")
        time.sleep(0.1)
    
    print(f"\n合計受信: {total_bytes} bytes")
    
    if total_bytes == 0:
        print("→ VESCからの自発的な送信はありません（正常）")
    else:
        print("→ VESCが何かデータを送信しています")
    
    return total_bytes

def test_get_values(ser):
    """GET_VALUESコマンドテスト"""
    print("\n=== GET_VALUESコマンドテスト ===\n")
    
    # パケット作成
    payload = bytes([0x04])  # COMM_GET_VALUES
    crc = calculate_crc16(payload)
    packet = bytes([0x02, len(payload)]) + payload + bytes([(crc >> 8) & 0xFF, crc & 0xFF, 0x03])
    
    print("送信パケット:")
    hex_dump(packet, "GET_VALUES request")
    
    ser.reset_input_buffer()
    ser.write(packet)
    print("✓ パケット送信完了")
    
    # 応答待ち
    print("\n応答を待っています...")
    time.sleep(0.1)
    
    response = b''
    for _ in range(10):  # 最大1秒待機
        if ser.in_waiting > 0:
            response += ser.read(ser.in_waiting)
        if len(response) > 0:
            time.sleep(0.05)  # 追加データ待ち
            if ser.in_waiting == 0:
                break
        time.sleep(0.1)
    
    if response:
        hex_dump(response, f"受信データ ({len(response)} bytes)")
        analyze_packet(response)
    else:
        print("✗ 応答がありません")
        print("\n【トラブルシューティング】")
        print("1. VESC Tool でUART通信が有効か確認")
        print("2. TX/RXのピン配線を確認")
        print("3. ボーレート設定を確認 (デフォルト: 115200)")
        print("4. VESCの電源が入っているか確認")

def calculate_crc16(data):
    """CRC16計算"""
    poly = 0x1021
    crc = 0
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def analyze_packet(data):
    """パケット構造を解析"""
    print("\n--- パケット解析 ---")
    
    if len(data) < 5:
        print("✗ データが短すぎます（最低5バイト必要）")
        return
    
    if data[0] == 0x02:
        print(f"✓ スタートバイト: 0x02 (ショートパケット)")
        length = data[1]
        print(f"  ペイロード長: {length} bytes")
        
        expected_len = 2 + length + 2 + 1
        print(f"  期待パケット長: {expected_len} bytes")
        print(f"  実際のデータ長: {len(data)} bytes")
        
        if len(data) >= expected_len:
            if data[expected_len - 1] == 0x03:
                print(f"✓ エンドバイト: 0x03")
                
                payload = data[2:2+length]
                crc_received = (data[2+length] << 8) | data[2+length+1]
                crc_calculated = calculate_crc16(payload)
                
                print(f"\nCRCチェック:")
                print(f"  受信CRC: 0x{crc_received:04x}")
                print(f"  計算CRC: 0x{crc_calculated:04x}")
                
                if crc_received == crc_calculated:
                    print("  ✓ CRC正常")
                    print(f"\nペイロード ({len(payload)} bytes):")
                    hex_dump(payload)
                    
                    if payload[0] == 0x04:
                        print("→ これはGET_VALUESの応答です！")
                else:
                    print("  ✗ CRCエラー")
            else:
                print(f"✗ エンドバイトが不正: 0x{data[expected_len-1]:02x} (期待: 0x03)")
        else:
            print("✗ パケットが不完全です")
    else:
        print(f"✗ スタートバイトが不正: 0x{data[0]:02x} (期待: 0x02)")

def main():
    print("╔════════════════════════════════════════╗")
    print("║   VESC UART 診断ツール v1.0           ║")
    print("╚════════════════════════════════════════╝")
    
    # 1. 接続テスト
    ser = test_connection()
    if not ser:
        return
    
    input("\nEnterを押して次へ...")
    
    # 2. 生データ受信テスト
    test_raw_read(ser, duration=2)
    
    input("\nEnterを押して次へ...")
    
    # 3. GET_VALUESテスト
    test_get_values(ser)
    
    print("\n" + "="*60)
    print("診断完了")
    print("="*60)
    
    ser.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断されました")
    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()