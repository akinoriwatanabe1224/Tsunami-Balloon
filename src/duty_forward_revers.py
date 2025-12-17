# src/duty.py
import time
import threading
from pyvesc.messages.setters import SetDutyCycle
from pyvesc.interface import encode

class VESCDutyController:
    def __init__(self, ser, max_duty=10, step_delay=0.05):
        self.ser = ser
        self.max_duty = max_duty
        self.step_delay = step_delay
        self._lock = threading.Lock()

    def _send_duty(self, duty):
        duty = max(-100.0, min(100.0, duty))
        duty_int = int(duty * 1000)
        msg = SetDutyCycle(duty_int)
        self.ser.write(encode(msg))

    def ramp_and_hold(self, target_duty, hold_time):
        """
        target_duty : +max_duty or -max_duty
        hold_time   : 秒
        """
        with self._lock:
            step = self.max_duty / abs(self.max_duty)
            step = step if target_duty > 0 else -step

            # 0 → target_duty
            d = 0
            while abs(d) < abs(target_duty):
                d += step
                self._send_duty(d)
                time.sleep(self.step_delay)

            # 保持
            self._send_duty(target_duty)
            time.sleep(hold_time)

            # target_duty → 0
            while abs(d) > 0:
                d -= step
                self._send_duty(d)
                time.sleep(self.step_delay)

            self._send_duty(0)
