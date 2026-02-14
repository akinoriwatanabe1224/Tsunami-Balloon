# main.py - トグルスイッチ + ジョイスティック統合版
import serial
import time
import os
import threading
from src.duty_forward_revers import VESCDutyController
from src.relay import RelayController
from src.reader_v2 import VESCReader
from src.toggle_switch import ToggleSwitchController
from src.joystick import Joystick

# シリアルポート排他制御用ロック（DutyController/Reader共有）
serial_lock = threading.Lock()

# ===== 設定 =====
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 115200

MAX_DUTY = 40
STEP_DELAY = 0.05
RUN_TIME_SEC = 40

# GPIO設定（リレー：autoモード用）
GPIO_PIN_FORWARD = 17
GPIO_PIN_REVERSE = 27
GPIO_DEBOUNCE = 0.5
GPIO_COOLDOWN = 15.0

# トグルスイッチGPIO
GPIO_MANUAL = 5
GPIO_AUTO = 6
GPIO_ON = 13
GPIO_OFF = 19

# ジョイスティック設定
JOYSTICK_INTERVAL = 0.05  # 50msごとにduty送信

# ログ設定
LOG_INTERVAL = 0.1
USB_LOG_DIR = "/media/pi/B5EA-9E28/log"
CSV_FIELDS = ["time", "duty", "rpm", "v_in", "current_in", "current_motor", "temp_fet"]

# ログ取得時間（モーター動作時間 + マージン）
LOG_DURATION = RUN_TIME_SEC + 3
# =================


def make_log_filename(mode):
    """ログファイル名を生成: {mode}_{YYYYMMDD}_{HHMMSS}.csv"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(USB_LOG_DIR, f"{mode}_{timestamp}.csv")


def main():
    # USBログディレクトリ作成
    os.makedirs(USB_LOG_DIR, exist_ok=True)

    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)

    # VESC制御
    duty = VESCDutyController(
        ser,
        max_duty=MAX_DUTY,
        step_delay=STEP_DELAY,
        serial_lock=serial_lock
    )

    # ログ取得
    reader = VESCReader(
        ser,
        interval=LOG_INTERVAL,
        csv_filename="",  # 都度設定する
        csv_fields=CSV_FIELDS,
        serial_lock=serial_lock
    )

    # GPIO制御（autoモード用）
    relay = RelayController(
        pin_forward=GPIO_PIN_FORWARD,
        pin_reverse=GPIO_PIN_REVERSE,
        debounce_time=GPIO_DEBOUNCE,
        cooldown_time=GPIO_COOLDOWN
    )

    # トグルスイッチ
    toggle = ToggleSwitchController(
        pin_manual=GPIO_MANUAL,
        pin_auto=GPIO_AUTO,
        pin_on=GPIO_ON,
        pin_off=GPIO_OFF
    )

    # ジョイスティック
    joystick = Joystick()

    # manualモードのログ状態管理
    manual_logging = False

    def forward_action():
        """正転動作（autoモード用・ログ付き）"""
        if not toggle.is_on():
            print("FORWARD IGNORED (power OFF)")
            return

        print("\n" + "=" * 50)
        print("AUTO FORWARD START")
        print("=" * 50)

        with serial_lock:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        time.sleep(0.2)

        log_file = make_log_filename("auto_forward")
        reader.start_temporary(LOG_DURATION, csv_filename=log_file)
        time.sleep(0.5)

        duty.ramp_and_hold(+MAX_DUTY, RUN_TIME_SEC)

        print(f"Waiting for reader to auto-stop...")
        time.sleep(LOG_DURATION - RUN_TIME_SEC + 1)

        reader.stop()

        print("Waiting for VESC stabilization...")
        time.sleep(3.0)

        with serial_lock:
            ser.reset_input_buffer()
            ser.reset_output_buffer()

        print("=" * 50)
        print("AUTO FORWARD COMPLETED")
        print("=" * 50 + "\n")

    def reverse_action():
        """逆転動作（autoモード用・ログ付き）"""
        if not toggle.is_on():
            print("REVERSE IGNORED (power OFF)")
            return

        print("\n" + "=" * 50)
        print("AUTO REVERSE START")
        print("=" * 50)

        with serial_lock:
            ser.reset_input_buffer()
            ser.reset_output_buffer()
        time.sleep(0.2)

        log_file = make_log_filename("auto_reverse")
        reader.start_temporary(LOG_DURATION, csv_filename=log_file)
        time.sleep(0.5)

        duty.ramp_and_hold(-MAX_DUTY, RUN_TIME_SEC)

        print(f"Waiting for reader to auto-stop...")
        time.sleep(LOG_DURATION - RUN_TIME_SEC + 1)

        reader.stop()

        print("Waiting for VESC stabilization...")
        time.sleep(3.0)

        with serial_lock:
            ser.reset_input_buffer()
            ser.reset_output_buffer()

        print("=" * 50)
        print("AUTO REVERSE COMPLETED")
        print("=" * 50 + "\n")

    # autoモード用コールバック設定
    relay.on_forward = forward_action
    relay.on_reverse = reverse_action

    try:
        # ジョイスティックキャリブレーション
        print("Calibrating joystick... Keep centered")
        time.sleep(1)
        joystick.calibrate()

        print("=" * 50)
        print("SYSTEM READY")
        print(f"  Power: {toggle.get_power()}")
        print(f"  Mode:  {toggle.get_mode()}")
        print(f"  Manual: joystick x MAX_DUTY({MAX_DUTY}%)")
        print(f"  Auto:   relay trigger (GPIO{GPIO_PIN_FORWARD}/{GPIO_PIN_REVERSE})")
        print(f"  Log:    {USB_LOG_DIR}/")
        print("=" * 50 + "\n")

        prev_power = None
        prev_mode = None

        while True:
            power = toggle.get_power()
            mode = toggle.get_mode()

            # 状態変化をログ
            if power != prev_power:
                print(f"[POWER] {power}")
                prev_power = power
            if mode != prev_mode:
                print(f"[MODE]  {mode}")
                prev_mode = mode

            # 電源OFF → モーター停止 & manualログ停止
            if power != "ON":
                if manual_logging:
                    reader.stop()
                    manual_logging = False
                    print("[LOG] Manual logging stopped (power OFF)")
                duty.set_duty(0)
                time.sleep(0.1)
                continue

            # manualモード: ジョイスティックでduty制御 + 連続ログ
            if mode == "manual":
                # manualログ開始（まだ開始していない場合）
                if not manual_logging:
                    log_file = make_log_filename("manual")
                    reader.start(csv_filename=log_file)
                    manual_logging = True
                    print(f"[LOG] Manual logging started: {log_file}")

                y = joystick.read_y()
                target_duty = y * MAX_DUTY
                duty.set_duty(target_duty)
                time.sleep(JOYSTICK_INTERVAL)

            # autoモード: リレーイベント待ち（バックグラウンドで処理）
            else:
                # manualログ停止
                if manual_logging:
                    reader.stop()
                    manual_logging = False
                    print("[LOG] Manual logging stopped (mode changed)")
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nKeyboard Interrupt detected")
    finally:
        print("\nSYSTEM STOPPING...")
        reader.stop()
        duty.emergency_stop()
        joystick.close()
        ser.close()
        print("SYSTEM STOPPED")


if __name__ == "__main__":
    main()
