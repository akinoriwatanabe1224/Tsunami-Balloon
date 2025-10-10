import serial
import time
import pyvesc
from pyvesc import VESCMessage, encode, decode

# VESCのUARTポートとボーレートを設定
PORT = "/dev/serial0"
BAUD = 115200

# シリアルポートの初期化
ser = serial.Serial(PORT, BAUD, timeout=0.5)

# GET_VALUESメッセージの定義
class GetValues(VESCMessage):
    id = 4
    fields = [
        ('temp_fet', 'h'),
        ('temp_motor', 'h'),
        ('current_motor', 'i'),
        ('current_in', 'i'),
        ('duty', 'h'),
        ('rpm', 'i'),
        ('amp_hours', 'f'),
        ('amp_hours_charged', 'f'),
        ('watt_hours', 'f'),
        ('watt_hours_charged', 'f'),
        ('tachometer', 'i'),
        ('tachometer_abs', 'i'),
        ('fault_code', 'B')
    ]

# メインループ
try:
    while True:
        # GET_VALUESメッセージをエンコードして送信
        msg = GetValues()
        packet = encode(msg)
        ser.write(packet)
        time.sleep(0.05)

        # VESCからの応答を読み取り
        data = ser.read(1024)
        if data:
            # データをデコードして解析
            msg, _ = decode(data)
            if msg:
                print({
                    'temp_fet': msg.temp_fet / 10,
                    'temp_motor': msg.temp_motor / 10,
                    'current_motor': msg.current_motor / 100,
                    'current_in': msg.current_in / 100,
                    'duty': msg.duty / 1000
                })
        else:
            print("No data received")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
