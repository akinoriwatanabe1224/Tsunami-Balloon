# main.py
import serial
import time
import threading
from src.duty_forward_revers import VESCDutyController
from src.relay import RelayController
from vesc.reader import VESCReader

# ===== 設定 =====
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 115200

MAX_DUTY = 10
STEP_DELAY = 0.05
RUN_TIME_SEC = 5        # モータ回転時間
COOLDOWN_SEC = 4        # 再トリガ無視時間

LOG_INTERVAL = 0.05     # readerの取得周期
CSV_ENABLE = True
CSV_FILE = "log/0g.csv"
CSV_FIELDS = ["time", "duty", "rpm"]
# =================

busy_lock = threading.Lock()
busy = False


def with_lock(func):
    def wrapper():
        global busy
        with busy_lock:
            if busy:
                print("IGNORED (cooldown)")
                return
            busy = True

        try:
            func()
        finally:
            def release():
                global busy
                time.sleep(COOLDOWN_SEC)
                with busy_lock:
                    busy = False
                print("READY")

            threading.Thread(target=release, daemon=True).start()
    return wrapper


def main():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)

    # --- Reader（ログ・表示） ---
    reader = VESCReader(
        ser,
        interval=LOG_INTERVAL,
        csv_enable=CSV_ENABLE,
        csv_filename=CSV_FILE,
        csv_fields=CSV_FIELDS
    )

    # --- Duty制御 ---
    duty = VESCDutyController(
        ser,
        max_duty=MAX_DUTY,
        step_delay=STEP_DELAY
    )

    # --- GPIO ---
    relay = RelayController(pin_forward=17, pin_reverse=27)

    @with_lock
    def forward_action():
        print("FORWARD START")
        duty.ramp_and_hold(
            target_duty=+MAX_DUTY,
            hold_time=RUN_TIME_SEC
        )

    @with_lock
    def reverse_action():
        print("REVERSE START")
        duty.ramp_and_hold(
            target_duty=-MAX_DUTY,
            hold_time=RUN_TIME_SEC
        )

    relay.on_forward = forward_action
    relay.on_reverse = reverse_action

    try:
        print("SYSTEM READY")
        reader.start()        # ← ログ開始
        relay.wait()
    finally:
        print("SYSTEM STOP")
        reader.stop()
        duty.emergency_stop()
        ser.close()


if __name__ == "__main__":
    main()
