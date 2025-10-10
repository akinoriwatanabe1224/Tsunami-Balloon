from pyvesc.messages.getters import GetValues
from pyvesc.protocol.interface import encode_request, decode
import serial

# シリアル
ser = serial.Serial("/dev/serial0", 115200, timeout=0.5)

# GET_VALUES メッセージ作成
msg = GetValues()  # クラスのインスタンス
pkt = encode_request(msg)

# 送信
ser.write(pkt)

# 受信
data = ser.read(1024)
print(data)
