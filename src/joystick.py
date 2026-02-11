# src/joystick.py - MCP3008を使用したジョイスティックY軸読み取り
import spidev
import time

# SPI設定
SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED = 1000000  # 1MHz

# ADC設定
ADC_CHANNEL = 0  # CH0にVRyを接続
ADC_MAX = 1023   # 10ビットADC

# 感度設定
DEADZONE = 0.1       # 不感帯（中央付近でこの範囲は0とする）
SENSITIVITY = 2.0    # 感度曲線（1.0=リニア、2.0以上=中央付近が鈍感）
CALIBRATION_SAMPLES = 20  # キャリブレーション時のサンプル数


class Joystick:
    def __init__(self, channel=ADC_CHANNEL, deadzone=DEADZONE, sensitivity=SENSITIVITY):
        self.channel = channel
        self.deadzone = deadzone
        self.sensitivity = sensitivity
        self.spi = spidev.SpiDev()
        self.spi.open(SPI_BUS, SPI_DEVICE)
        self.spi.max_speed_hz = SPI_SPEED

        # キャリブレーション用（中央値）
        self.center = 512

    def read_raw(self):
        """MCP3008から生の値(0-1023)を取得"""
        cmd = [1, (8 + self.channel) << 4, 0]
        result = self.spi.xfer2(cmd)
        value = ((result[1] & 3) << 8) + result[2]
        return value

    def read_y(self):
        """Y軸の値を-1.0〜1.0で取得（デッドゾーン・感度曲線適用）"""
        raw = self.read_raw()
        # 中央値を0として-1〜1に正規化
        normalized = (raw - self.center) / self.center

        # デッドゾーン適用
        if abs(normalized) < self.deadzone:
            return 0.0

        # デッドゾーン外は範囲を再スケール
        if normalized > 0:
            scaled = (normalized - self.deadzone) / (1.0 - self.deadzone)
        else:
            scaled = (normalized + self.deadzone) / (1.0 - self.deadzone)

        # 感度曲線適用（べき乗で中央付近を鈍感に）
        sign = 1 if scaled >= 0 else -1
        curved = sign * (abs(scaled) ** self.sensitivity)

        # クランプ
        return max(-1.0, min(1.0, curved))

    def calibrate(self, samples=CALIBRATION_SAMPLES):
        """現在位置を中央値としてキャリブレーション（複数回サンプリング）"""
        readings = []
        for _ in range(samples):
            readings.append(self.read_raw())
            time.sleep(0.02)
        self.center = sum(readings) // len(readings)
        print(f"Calibrated center: {self.center} (from {samples} samples)")

    def close(self):
        self.spi.close()
