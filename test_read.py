# test_read_getvalues.py
import time
import serial
from pyvesc.messages.getters import GetValues
# encode_request/decode は protocol.interface にある場合がある
from pyvesc.protocol.interface import encode_request, decode

PORT = "/dev/serial0"
BAUDRATE = 115200

ser = serial.Serial(PORT, BAUDRATE, timeout=0.2)

try:
    while True:
        # GetValues の「リクエスト」を作る（encode_request を使う）
        ser.write(encode_request(GetValues()))

        time.sleep(0.05)               # 少しだけ待つ
        data = ser.read(1024)         # 充分なバッファを読む（受信分が来るまで待つ）
        if data:
            # decode は (msg, consumed) か、複数返す実装かもしれないので両方扱う
            res = decode(data)
            # decode が (msg, consumed) を返す場合
            if isinstance(res, tuple) and len(res) == 2 and res[0] is not None:
                msg, consumed = res
                print("Decoded:", msg)
            else:
                # decode が iterable を返す実装の場合
                for m in res:
                    print("Decoded:", m)

        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
