import time
import serial
from pyvesc import VESC
from pyvesc.VESC.messages import SetDutyCycle

# === 設定 ===
PORT = "/dev/serial0"  # Pi Zero 2 W のUARTポート
BAUDRATE = 115200

# === 初期化 ===
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

def set_duty(duty):
    """
    duty: -1.0 ～ +1.0
    """
    duty = max(-1.0, min(1.0, duty))  # 範囲制限
    msg = SetDutyCycle(duty)
    ser.write(msg.serialize())

try:
    print("Starting VESC UART control...")
    while True:
        # 例: 徐々にデューティを上げてモーター回転
        for d in [i/20 for i in range(0, 21)]:
            set_duty(d)
            print(f"Duty: {d:.2f}")
            time.sleep(0.2)
        # 減速
        for d in [i/20 for i in range(20, -1, -1)]:
            set_duty(d)
            print(f"Duty: {d:.2f}")
            time.sleep(0.2)

except KeyboardInterrupt:
    print("Stop motor")
    set_duty(0)
    ser.close()
