# test_read_decode.py
import time
import serial
from pyvesc.messages.getters import GetValues
from pyvesc.protocol.interface import encode_request, decode

PORT = "/dev/serial0"
BAUDRATE = 115200

ser = serial.Serial(PORT, BAUDRATE, timeout=0.2)

try:
    while True:
        ser.write(encode_request(GetValues()))
        time.sleep(0.05)

        data = ser.read(1024)
        if data:
            print("Raw reply (len={}):".format(len(data)), data.hex())

            res = decode(data)
            print("Decode result type:", type(res))
            print("Decode result repr:", repr(res))

            # もし (msg, consumed) の形式だったら
            if isinstance(res, tuple) and len(res) == 2:
                msg, consumed = res
                print("Decoded MSG:", msg)
            else:
                # イテレータ（複数メッセージ）形式の場合
                for m in res:
                    print("Decoded MSG:", m)

        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
