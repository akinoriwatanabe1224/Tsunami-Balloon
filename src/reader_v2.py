# src/reader_v2.py - 診断ログ付き・状態リセット修正版
import struct
import time
import threading
import csv
import os
import traceback

COMM_GET_VALUES = 4


# CRC16計算
def _make_crc16_table():
    poly = 0x1021
    table = []
    for i in range(256):
        crc = 0
        c = i << 8
        for _ in range(8):
            if (crc ^ c) & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
            c = (c << 1) & 0xFFFF
        table.append(crc)
    return table

CRC16_TABLE = _make_crc16_table()


def crc16(data: bytes) -> int:
    crc = 0
    for b in data:
        crc = ((crc << 8) & 0xFFFF) ^ CRC16_TABLE[((crc >> 8) ^ b) & 0xFF]
    return crc & 0xFFFF


def build_packet(payload: bytes) -> bytes:
    if len(payload) <= 256:
        header = bytes([0x02, len(payload)])
    else:
        header = bytes([0x03, (len(payload) >> 8) & 0xFF, len(payload) & 0xFF])
    crc = crc16(payload)
    crc_bytes = bytes([(crc >> 8) & 0xFF, crc & 0xFF])
    return header + payload + crc_bytes + bytes([0x03])


def extract_packets(buf: bytes):
    packets = []
    consumed = 0
    i = 0
    while i < len(buf):
        if buf[i] == 0x02:
            if i + 2 > len(buf):
                break
            length = buf[i + 1]
            packet_len = 2 + length + 2 + 1
            if i + packet_len > len(buf):
                break
            if buf[i + packet_len - 1] == 0x03:
                payload = buf[i + 2:i + 2 + length]
                crc_received = (buf[i + 2 + length] << 8) | buf[i + 2 + length + 1]
                if crc16(payload) == crc_received:
                    packets.append(payload)
                    consumed = i + packet_len
                    i = consumed
                else:
                    i += 1
            else:
                i += 1
        else:
            i += 1
    return packets, buf[consumed:]


def parse_getvalues(payload):
    try:
        if payload[0] == COMM_GET_VALUES:
            payload = payload[1:]
        if len(payload) < 46:
            return None

        offset = 0
        temp_fet = struct.unpack('>h', payload[offset:offset+2])[0] / 10.0
        offset += 2
        temp_motor = struct.unpack('>h', payload[offset:offset+2])[0] / 10.0
        offset += 2
        current_motor = struct.unpack('>i', payload[offset:offset+4])[0] / 100.0
        offset += 4
        current_in = struct.unpack('>i', payload[offset:offset+4])[0] / 100.0
        offset += 4
        id_val = struct.unpack('>i', payload[offset:offset+4])[0] / 100.0
        offset += 4
        iq_val = struct.unpack('>i', payload[offset:offset+4])[0] / 100.0
        offset += 4
        duty_now = struct.unpack('>h', payload[offset:offset+2])[0] / 1000.0
        offset += 2
        rpm = struct.unpack('>i', payload[offset:offset+4])[0]
        offset += 4
        v_in = struct.unpack('>h', payload[offset:offset+2])[0] / 10.0
        offset += 2
        amp_hours = struct.unpack('>i', payload[offset:offset+4])[0] / 10000.0
        offset += 4
        amp_hours_charged = struct.unpack('>i', payload[offset:offset+4])[0] / 10000.0
        offset += 4
        watt_hours = struct.unpack('>i', payload[offset:offset+4])[0] / 10000.0
        offset += 4
        watt_hours_charged = struct.unpack('>i', payload[offset:offset+4])[0] / 10000.0
        offset += 4

        return {
            'temp_fet': temp_fet,
            'temp_motor': temp_motor,
            'current_motor': current_motor,
            'current_in': current_in,
            'duty': duty_now,
            'rpm': rpm,
            'v_in': v_in,
            'amp_hours': amp_hours,
            'amp_hours_charged': amp_hours_charged,
            'watt_hours': watt_hours,
            'watt_hours_charged': watt_hours_charged,
        }
    except Exception:
        return None


class VESCReader:
    """
    VESCからデータを読み取ってCSVに保存するクラス

    使い方:
    1. start() で連続ログ開始、stop() で停止
    2. start_temporary(duration) で一時的ログ（自動停止）
    """

    def __init__(self, ser, interval=0.05,
                 csv_filename="vesc_data.csv", csv_fields=None, serial_lock=None):
        self.ser = ser
        self.interval = interval
        self._buffer = b''
        self._stop_flag = threading.Event()
        self._thread = None
        self.count = 0

        # CSV設定
        self.csv_filename = csv_filename
        self.csv_fields = csv_fields or ["time", "duty", "rpm"]
        self._csv_file = None
        self._csv_writer = None
        self._start_time = None

        # 一時的使用のためのタイマー
        self._duration = None
        self._timer_thread = None

        # 診断カウンタ
        self._diag_read_count = 0
        self._diag_empty_count = 0
        self._diag_packet_count = 0
        self._diag_parse_fail_count = 0

        # シリアルポート排他制御用（DutyControllerと共有）
        self._serial_lock = serial_lock if serial_lock else threading.Lock()

    def _reset_state(self):
        """セッション間の状態リセット"""
        self._buffer = b''
        self.count = 0
        self._csv_file = None
        self._csv_writer = None
        self._start_time = None
        self._diag_read_count = 0
        self._diag_empty_count = 0
        self._diag_packet_count = 0
        self._diag_parse_fail_count = 0

    def _init_csv(self):
        """CSV初期化"""
        os.makedirs(os.path.dirname(self.csv_filename) or ".", exist_ok=True)
        self._csv_file = open(self.csv_filename, mode="w", newline="")
        self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=self.csv_fields)
        self._csv_writer.writeheader()
        self._csv_file.flush()

        self._start_time = time.time()
        print(f"[CSV] Logging to: {self.csv_filename}")

    def _write_csv(self, parsed):
        """CSV書き込み"""
        if self._csv_writer is None:
            return

        elapsed = time.time() - self._start_time
        row = {}
        for field in self.csv_fields:
            if field == "time":
                row["time"] = round(elapsed, 3)
            elif field in parsed:
                row[field] = parsed[field]

        self._csv_writer.writerow(row)
        self._csv_file.flush()

    def _loop(self):
        """メインループ"""
        self._init_csv()

        while not self._stop_flag.is_set():
            try:
                # COMM_GET_VALUES送信（排他制御を最小化）
                pkt = build_packet(bytes([COMM_GET_VALUES]))
                with self._serial_lock:
                    self.ser.write(pkt)

                # ロック外で待機（VESC応答待ち＆Dutyコマンド割り込み許可）
                time.sleep(0.05)

                # 応答読み取り（ノンブロッキング：ロック時間を最小化）
                with self._serial_lock:
                    waiting = self.ser.in_waiting
                    if waiting > 0:
                        data = self.ser.read(waiting)
                    else:
                        data = b''

                self._diag_read_count += 1

                if data:
                    self._buffer += data
                    packets, self._buffer = extract_packets(self._buffer)

                    for payload in packets:
                        self._diag_packet_count += 1
                        parsed = parse_getvalues(payload)
                        if parsed:
                            self.count += 1
                            self._write_csv(parsed)

                            # データ表示
                            print(f"\n--- データ #{self.count} ---")
                            print(f"Duty比:     {parsed['duty']:.3f}")
                            print(f"RPM:        {parsed['rpm']}")
                            print(f"入力電圧:   {parsed['v_in']:.1f}V")
                            print(f"入力電流:   {parsed['current_in']:.2f}A")
                            print(f"モーター電流: {parsed['current_motor']:.2f}A")
                            print(f"FET温度:    {parsed['temp_fet']:.1f}°C")
                        else:
                            self._diag_parse_fail_count += 1
                            print(f"[DIAG] parse_getvalues failed: payload_len={len(payload)}, "
                                  f"cmd_id={payload[0] if payload else 'N/A'}")
                else:
                    self._diag_empty_count += 1
                    # 5回に1回診断出力（頻度を抑える）
                    if self._diag_empty_count % 5 == 1:
                        print(f"[DIAG] No data from VESC "
                              f"(empty={self._diag_empty_count}/{self._diag_read_count}, "
                              f"buf={len(self._buffer)}B)")

                # インターバル待機
                time.sleep(max(0, self.interval - 0.05))

            except Exception as e:
                print(f"[Reader Error] {e}")
                traceback.print_exc()
                time.sleep(0.1)

        # 終了処理
        print(f"[CSV] Closing. samples={self.count}, "
              f"reads={self._diag_read_count}, empty={self._diag_empty_count}, "
              f"packets={self._diag_packet_count}, parse_fail={self._diag_parse_fail_count}")
        if self._csv_file:
            self._csv_file.close()

    def start(self, csv_filename=None):
        """
        ログ取得開始（手動でstop()するまで継続）

        Args:
            csv_filename: CSVファイルパス（省略時はself.csv_filename）
        """
        if self._thread is not None:
            print("[Reader] Already running, stopping first...")
            self.stop()
            time.sleep(0.5)

        if csv_filename:
            self.csv_filename = csv_filename

        self._reset_state()
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print(f"[Reader] Started (continuous)")

    def start_temporary(self, duration, csv_filename=None):
        """
        一時的にログ取得を開始（duration秒後に自動停止）

        Args:
            duration: ログ取得時間（秒）
            csv_filename: CSVファイルパス（省略時はself.csv_filename）
        """
        if self._thread is not None:
            print("[Reader] Already running, stopping first...")
            self.stop()
            time.sleep(0.5)

        if csv_filename:
            self.csv_filename = csv_filename

        self._duration = duration
        self._reset_state()
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        # タイマースレッド開始
        def timer_func():
            time.sleep(duration)
            if not self._stop_flag.is_set():
                print(f"[Reader] Auto-stopping after {duration}s")
                self.stop()

        self._timer_thread = threading.Thread(target=timer_func, daemon=True)
        self._timer_thread.start()

        print(f"[Reader] Started (will auto-stop after {duration}s)")

    def stop(self):
        """読み取り停止"""
        if self._thread is not None:
            self._stop_flag.set()
            self._thread.join(timeout=3.0)
            self._thread = None
            print("[Reader] Stopped")


if __name__ == "__main__":
    # テスト用
    import serial
    ser = serial.Serial("/dev/serial0", 115200, timeout=0.1)

    reader = VESCReader(
        ser,
        interval=0.1,
        csv_filename="test.csv",
        csv_fields=["time", "duty", "rpm"]
    )

    print("Starting reader for 5 seconds...")
    reader.start_temporary(5)

    # 待機
    time.sleep(10)

    print("Test completed")
    ser.close()
