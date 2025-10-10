import serial
import time
from pyvesc.protocol.interface import encode_request, decode

PORT = "/dev/serial0"
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=0.5)

COMM_GET_VALUES = 4  # VESC GET_VALUES

try:
    while True:
        # GET_VALUESリクエストを作成
        pkt = encode_request(COMM_GET_VALUES)
        ser.write(pkt)
        time.sleep(0.05)

        # VESCから応答を受信
        data = ser.read(1024)
        if data:
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
            print("no reply")
        time.sleep(0.5)

except KeyboardInterrupt:
    ser.close()
    print("Stopped.")
