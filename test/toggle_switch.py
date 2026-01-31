#!/usr/bin/env python3
"""
ON-ONトグルスイッチでGPIOを監視し、manual/auto、on/offを表示するプログラム
GPIOはプルダウン設定で3.3Vを検出
"""

import RPi.GPIO as GPIO
import time

# グローバル変数: GPIOピン番号
# モード切替スイッチ (manual/auto)
GPIO_MANUAL = 5   # manual側のGPIOピン
GPIO_AUTO = 6     # auto側のGPIOピン

# オン/オフスイッチ
GPIO_ON = 13      # ON側のGPIOピン
GPIO_OFF = 19     # OFF側のGPIOピン


def setup_gpio():
    """GPIOの初期設定"""
    GPIO.setmode(GPIO.BCM)
    # モード切替スイッチ
    GPIO.setup(GPIO_MANUAL, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(GPIO_AUTO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # オン/オフスイッチ
    GPIO.setup(GPIO_ON, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(GPIO_OFF, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def get_mode():
    """スイッチ状態に応じてモード文字列を返す"""
    manual_state = GPIO.input(GPIO_MANUAL)
    auto_state = GPIO.input(GPIO_AUTO)

    if manual_state == GPIO.HIGH:
        return "manual"
    elif auto_state == GPIO.HIGH:
        return "auto"
    else:
        return "unknown"


def get_power():
    """オン/オフスイッチの状態を返す"""
    on_state = GPIO.input(GPIO_ON)
    off_state = GPIO.input(GPIO_OFF)

    if on_state == GPIO.HIGH:
        return "ON"
    elif off_state == GPIO.HIGH:
        return "OFF"
    else:
        return "unknown"


def main():
    """メイン処理"""
    try:
        setup_gpio()
        print("ON-ONトグルスイッチ監視開始")
        print(f"  manual: GPIO{GPIO_MANUAL}")
        print(f"  auto:   GPIO{GPIO_AUTO}")
        print(f"  ON:     GPIO{GPIO_ON}")
        print(f"  OFF:    GPIO{GPIO_OFF}")
        print("Ctrl+C で終了")
        print("-" * 30)

        previous_mode = None
        previous_power = None

        while True:
            current_mode = get_mode()
            current_power = get_power()

            # モードが変化した時のみ表示
            if current_mode != previous_mode:
                print(f"モード: {current_mode}")
                previous_mode = current_mode

            # 電源状態が変化した時のみ表示
            if current_power != previous_power:
                print(f"電源: {current_power}")
                previous_power = current_power

            time.sleep(0.1)  # チャタリング防止

    except KeyboardInterrupt:
        print("\n終了します")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
