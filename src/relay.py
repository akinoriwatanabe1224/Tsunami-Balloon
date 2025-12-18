# src/relay.py
from gpiozero import DigitalInputDevice
from signal import pause
import time
import threading


class RelayController:
    def __init__(self, pin_forward=17, pin_reverse=27, debounce_time=0.2, lockout_time=10.0):
        """
        pin_forward: 正転用GPIOピン番号
        pin_reverse: 逆転用GPIOピン番号
        debounce_time: チャタリング防止時間（秒）
        lockout_time: 1回の実行後に次の入力を受け付けない時間（秒）
        """
        self.forward = DigitalInputDevice(
            pin_forward,
            pull_up=False,
            bounce_time=debounce_time
        )
        self.reverse = DigitalInputDevice(
            pin_reverse,
            pull_up=False,
            bounce_time=debounce_time
        )

        self.on_forward = None
        self.on_reverse = None
        
        # ロックアウト管理
        self.lockout_time = lockout_time
        self._forward_lock = threading.Lock()
        self._reverse_lock = threading.Lock()
        self._forward_last_trigger = 0
        self._reverse_last_trigger = 0

        self.forward.when_activated = self._forward_trigger
        self.reverse.when_activated = self._reverse_trigger

    def _forward_trigger(self):
        """正転トリガー（ロックアウト機能付き）"""
        with self._forward_lock:
            current_time = time.time()
            time_since_last = current_time - self._forward_last_trigger
            
            # ロックアウト期間中は無視
            if time_since_last < self.lockout_time:
                print(f"GPIO17 IGNORED (lockout: {time_since_last:.1f}s < {self.lockout_time}s)")
                return
            
            # 最後のトリガー時刻を更新
            self._forward_last_trigger = current_time
            
        print("GPIO17 CONNECTED (FORWARD)")
        if self.on_forward:
            self.on_forward()

    def _reverse_trigger(self):
        """逆転トリガー（ロックアウト機能付き）"""
        with self._reverse_lock:
            current_time = time.time()
            time_since_last = current_time - self._reverse_last_trigger
            
            # ロックアウト期間中は無視
            if time_since_last < self.lockout_time:
                print(f"GPIO27 IGNORED (lockout: {time_since_last:.1f}s < {self.lockout_time}s)")
                return
            
            # 最後のトリガー時刻を更新
            self._reverse_last_trigger = current_time
            
        print("GPIO27 CONNECTED (REVERSE)")
        if self.on_reverse:
            self.on_reverse()

    def wait(self):
        print("waiting for GPIO events...")
        pause()