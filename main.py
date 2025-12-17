# main.py
import serial
from src.duty_forward_revers import VESCDutyController
from src.relay import RelayController

# ====== 設定 ======
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 115200

MAX_DUTY = 10
STEP_DELAY = 0.05
RUN_TIME_SEC = 5        # 回転時間を指定
# ==================

def main():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    duty = VESCDutyController(
        ser,
        max_duty=MAX_DUTY,
        step_delay=STEP_DELAY
    )

    relay = RelayController(pin_forward=17, pin_reverse=27)

    # GPIO17 → 正転
    relay.on_forward = lambda: duty.ramp_and_hold(
        target_duty=+MAX_DUTY,
        hold_time=RUN_TIME_SEC
    )

    # GPIO27 → 逆転
    relay.on_reverse = lambda: duty.ramp_and_hold(
        target_duty=-MAX_DUTY,
        hold_time=RUN_TIME_SEC
    )

    try:
        relay.wait()
    finally:
        duty._send_duty(0)
        ser.close()

if __name__ == "__main__":
    main()
