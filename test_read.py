import struct
import serial
import time

PORT = "/dev/serial0"
BAUD = 115200

# シリアルを開く
ser = serial.Serial(PORT, BAUD, timeout=0.5)

def parse_getvalues(buf):
    # payload のみ抽出 (短パケットなら 2 バイト目が length)
    length = buf[1]
    payload = buf[2:2+length]

    # FET 温度, モータ温度, 電流などをアンパック
    # Vedder FW 6.6.x 想定 (例)
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

try:
    while True:
        # VESC に GET_VALUES コマンドを投げるには生パケットを作る必要があります
        # 簡易版: COMM_GET_VALUES = 4
        payload = bytes([4])
        # 簡易CRC/フレーム化（ここでは Vedder FW 6.x の短パケット例）
        crc = sum(payload) & 0xFF
        pkt = bytes([2, len(payload)]) + payload + bytes([crc, 3])
        
        ser.write(pkt)
        time.sleep(0.05)
        
        data = ser.read(1024)
        if data:
            parsed = parse_getvalues(data)
            print(parsed)
        
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
