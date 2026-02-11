# src/toggle_switch.py - トグルスイッチ制御モジュール
from gpiozero import DigitalInputDevice


class ToggleSwitchController:
    """
    ON-ONトグルスイッチ制御クラス

    - モード切替スイッチ (manual/auto)
    - 電源スイッチ (ON/OFF)
    GPIOはプルダウン設定で3.3Vを検出
    """

    def __init__(self, pin_manual=5, pin_auto=6, pin_on=13, pin_off=19):
        self.manual = DigitalInputDevice(pin_manual, pull_up=False)
        self.auto = DigitalInputDevice(pin_auto, pull_up=False)
        self.on = DigitalInputDevice(pin_on, pull_up=False)
        self.off = DigitalInputDevice(pin_off, pull_up=False)

    def get_mode(self):
        """スイッチ状態に応じてモード文字列を返す"""
        if self.manual.is_active:
            return "manual"
        elif self.auto.is_active:
            return "auto"
        return "unknown"

    def get_power(self):
        """電源スイッチの状態を返す"""
        if self.on.is_active:
            return "ON"
        elif self.off.is_active:
            return "OFF"
        return "unknown"

    def is_on(self):
        return self.on.is_active

    def is_manual(self):
        return self.manual.is_active
