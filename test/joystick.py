# joystick.py - MCP3008を使用したジョイスティックY軸読み取り
import spidev
import time

# SPI設定
SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED = 1000000  # 1MHz

# ADC設定
ADC_CHANNEL = 0  # CH0にVRyを接続
ADC_MAX = 1023   # 10ビットADC


class Joystick:
    def __init__(self, channel=ADC_CHANNEL):
        self.channel = channel
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
        """Y軸の値を-1.0〜1.0で取得"""
        raw = self.read_raw()
        # 中央値を0として-1〜1に正規化
        normalized = (raw - self.center) / self.center
        # クランプ
        return max(-1.0, min(1.0, normalized))

    def calibrate(self):
        """現在位置を中央値としてキャリブレーション"""
        self.center = self.read_raw()
        print(f"Calibrated center: {self.center}")

    def close(self):
        self.spi.close()


def main():
    js = Joystick()

    print("Joystick Y-axis Reader")
    print("Press Ctrl+C to exit")
    print("-" * 30)

    # 起動時にキャリブレーション（ジョイスティックを中央に）
    print("Calibrating... Keep joystick centered")
    time.sleep(1)
    js.calibrate()
    print("-" * 30)

    try:
        while True:
            raw = js.read_raw()
            y = js.read_y()
            print(f"Raw: {raw:4d} | Y: {y:+.3f}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        js.close()


if __name__ == "__main__":
    main()
