import time
import serial
from pyvesc_fix import SetDutyCycle, encode  # pyvesc_fix を使用

# === 設定 ===
PORT = "/dev/serial0"   # Pi Zero 2 W の UART ポート
BAUDRATE = 115200

# === シリアル初期化 ===
ser = serial.Serial(PORT, BAUDRATE, timeout=0.1)

def set_duty(duty):
    """
    VESC にデューティ比を送信
    duty: -1.0 ～ +1.0
    """
    duty = max(-1.0, min(1.0, duty))  # 範囲制限
    packet = encode(SetDutyCycle(duty_cycle=duty))
    ser.write(packet)

try:
    print("Starting VESC UART control... (Ctrl+Cで停止)")
    
    while True:
        # 徐々に加速
        for d in [i / 20 for i in range(0, 21)]:
            set_duty(d)
            print(f"Duty: {d:.2f}")
            time.sleep(0.2)

        # 徐々に減速
        for d in [i / 20 for i in range(20, -1, -1)]:
            set_duty(d)
            print(f"Duty: {d:.2f}")
            time.sleep(0.2)

except KeyboardInterrupt:
    print("Stopping motor...")
    set_duty(0)
    ser.close()
