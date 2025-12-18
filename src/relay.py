# src/relay.py - クールダウン機能付き
from gpiozero import DigitalInputDevice
from signal import pause
import time
import threading


class RelayController:
    """
    GPIO入力制御クラス（クールダウン機能付き）
    
    - 1回のトリガー後、cooldown_time秒間は次の入力を無視
    - チャタリング防止機能搭載
    """
    
    def __init__(self, pin_forward=17, pin_reverse=27, 
                 debounce_time=0.5, cooldown_time=15.0):
        """
        Args:
            pin_forward: 正転用GPIOピン番号
            pin_reverse: 逆転用GPIOピン番号
            debounce_time: チャタリング防止時間（秒）
            cooldown_time: クールダウン時間（秒）
        """
        # GPIO設定
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
        
        # コールバック関数
        self.on_forward = None
        self.on_reverse = None
        
        # クールダウン管理
        self.cooldown_time = cooldown_time
        self._forward_lock = threading.Lock()
        self._reverse_lock = threading.Lock()
        self._forward_last_time = 0
        self._reverse_last_time = 0
        
        # イベントハンドラ登録
        self.forward.when_activated = self._forward_handler
        self.reverse.when_activated = self._reverse_handler
    
    def _forward_handler(self):
        """正転トリガーハンドラ（クールダウン機能付き）"""
        with self._forward_lock:
            current_time = time.time()
            elapsed = current_time - self._forward_last_time
            
            # クールダウン中は無視
            if elapsed < self.cooldown_time:
                print(f"GPIO17 IGNORED (cooldown: {elapsed:.1f}s / {self.cooldown_time:.1f}s)")
                return
            
            # トリガー時刻を更新
            self._forward_last_time = current_time
        
        # コールバック実行
        print("GPIO17 TRIGGERED (FORWARD)")
        if self.on_forward:
            try:
                self.on_forward()
            except Exception as e:
                print(f"Error in forward callback: {e}")
    
    def _reverse_handler(self):
        """逆転トリガーハンドラ（クールダウン機能付き）"""
        with self._reverse_lock:
            current_time = time.time()
            elapsed = current_time - self._reverse_last_time
            
            # クールダウン中は無視
            if elapsed < self.cooldown_time:
                print(f"GPIO27 IGNORED (cooldown: {elapsed:.1f}s / {self.cooldown_time:.1f}s)")
                return
            
            # トリガー時刻を更新
            self._reverse_last_time = current_time
        
        # コールバック実行
        print("GPIO27 TRIGGERED (REVERSE)")
        if self.on_reverse:
            try:
                self.on_reverse()
            except Exception as e:
                print(f"Error in reverse callback: {e}")
    
    def wait(self):
        """GPIO入力待機（ブロッキング）"""
        print("Waiting for GPIO events...")
        pause()


if __name__ == "__main__":
    # テスト用
    def test_forward():
        print("Forward action executed")
        time.sleep(2)
        print("Forward action completed")
    
    def test_reverse():
        print("Reverse action executed")
        time.sleep(2)
        print("Reverse action completed")
    
    relay = RelayController(
        pin_forward=17,
        pin_reverse=27,
        debounce_time=0.5,
        cooldown_time=10.0
    )
    
    relay.on_forward = test_forward
    relay.on_reverse = test_reverse
    
    print("Test started. Try triggering GPIO17 or GPIO27...")
    relay.wait()