# main.py - シンプル版
import serial
import time
import threading
from src.duty_forward_revers import VESCDutyController
from src.relay import RelayController
from src.reader import VESCReader

# ===== 設定 =====
SERIAL_PORT = "/dev/serial0"
BAUDRATE = 115200

MAX_DUTY = 10
STEP_DELAY = 0.05
RUN_TIME_SEC = 5

# GPIO設定
GPIO_DEBOUNCE = 0.5  # チャタリング防止（秒）
GPIO_COOLDOWN = 15.0  # 1回実行後の無視時間（秒）

# ログ設定
LOG_INTERVAL = 0.1
CSV_FILE = "log/motor.csv"
CSV_FIELDS = ["time", "duty", "rpm"]
# =================


def main():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    
    # VESC制御
    duty = VESCDutyController(
        ser,
        max_duty=MAX_DUTY,
        step_delay=STEP_DELAY
    )
    
    # ログ取得
    reader = VESCReader(
        ser,
        interval=LOG_INTERVAL,
        csv_enable=True,
        csv_filename=CSV_FILE,
        csv_fields=CSV_FIELDS
    )
    
    # GPIO制御（クールダウン機能付き）
    relay = RelayController(
        pin_forward=17,
        pin_reverse=27,
        debounce_time=GPIO_DEBOUNCE,
        cooldown_time=GPIO_COOLDOWN
    )
    
    def forward_action():
        """正転動作"""
        print("\n" + "="*50)
        print("FORWARD START")
        print("="*50)
        
        # モーター制御
        duty.ramp_and_hold(+MAX_DUTY, RUN_TIME_SEC)
        
        print("="*50)
        print("FORWARD COMPLETED")
        print("="*50 + "\n")
    
    def reverse_action():
        """逆転動作"""
        print("\n" + "="*50)
        print("REVERSE START")
        print("="*50)
        
        # モーター制御
        duty.ramp_and_hold(-MAX_DUTY, RUN_TIME_SEC)
        
        print("="*50)
        print("REVERSE COMPLETED")
        print("="*50 + "\n")
    
    # コールバック設定
    relay.on_forward = forward_action
    relay.on_reverse = reverse_action
    
    try:
        print("="*50)
        print("SYSTEM READY")
        print(f"GPIO debounce: {GPIO_DEBOUNCE}s")
        print(f"GPIO cooldown: {GPIO_COOLDOWN}s")
        print("="*50 + "\n")
        
        reader.start()
        relay.wait()
        
    except KeyboardInterrupt:
        print("\n\nKeyboard Interrupt detected")
    finally:
        print("\nSYSTEM STOPPING...")
        reader.stop()
        duty.emergency_stop()
        ser.close()
        print("SYSTEM STOPPED")


if __name__ == "__main__":
    main()