import serial
import struct
import time

class MyVESC:
    def __init__(self, port="/dev/serial0", baudrate=115200, timeout=0.1):
        self.ser = serial.Serial(port, baudrate, timeout=timeout)

    def encode_request_getvalues(self):
        """GetValues コマンドを VESC に送る"""
        # COMM_GET_VALUES = 4
        pkt = bytes([2, 4, 0, 3])  # 0x02 0x04 0x00 0x03 (STX, cmd, len, checksum) 仮
        # 実際は CRC8 または VESC 仕様に合わせてください
        return pkt

    def read_packet(self):
        """VESC から返ってくるパケットを読み取る"""
        if self.ser.in_waiting:
            data = self.ser.read(self.ser.in_waiting)
            return data
        return None

    def get_values(self):
        """GetValues を送り、温度・電流・duty_now を返す"""
        self.ser.write(self.encode_request_getvalues())
        time.sleep(0.01)  # 少し待つ
        payload = self.read_packet()
        if payload is None or len(payload) < 14:
            return None

        # VESC 6 用 unpack
        # temp_fet, temp_motor: int16_t (0.1°C), current_motor, current_in: int32_t (0.01 A), duty_now: int16_t (0.001)
        try:
            temp_fet, temp_motor, current_motor, current_in, duty_now = struct.unpack('<hhiiH', payload[:14])
            return {
                "temp_fet": temp_fet / 10.0,         # °C
                "temp_motor": temp_motor / 10.0,     # °C
                "current_motor": current_motor / 100.0,  # A
                "current_in": current_in / 100.0,        # A
                "duty_now": duty_now / 1000.0          # -1.0 ~ 1.0
            }
        except struct.error:
            return None

    def close(self):
        self.ser.close()

# ----------------------------
# 実際に読み取る例
# ----------------------------
if __name__ == "__main__":
    vesc = MyVESC(port="/dev/serial0", baudrate=115200)
    try:
        while True:
            values = vesc.get_values()
            if values:
                print(values)
            time.sleep(0.1)
    except KeyboardInterrupt:
        vesc.close()
