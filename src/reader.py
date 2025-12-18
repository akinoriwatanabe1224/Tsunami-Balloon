# src/reader.py (モーター動作中は読み取り停止版)
# 元の test_read.py をモジュール化（パース/CRC/パケット抽出はオリジナルのまま）
import struct
import time
import threading
import csv
import os

COMM_GET_VALUES = 4

# CRC16 テーブル（元コードと同じロジック）
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
                    print(f"[CRC ERROR] 受信: {crc_received:04x}, 計算: {crc16(payload):04x}")
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
            print(f"[WARN] ペイロード長が短い: {len(payload)} bytes")
            print(f"[HEX] {payload.hex()}")
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
        tachometer = struct.unpack('>i', payload[offset:offset+4])[0]
        offset += 4
        tachometer_abs = struct.unpack('>i', payload[offset:offset+4])[0]
        return {
            'temp_fet': temp_fet,
            'temp_motor': temp_motor,
            'current_motor': current_motor,
            'current_in': current_in,
            'id': id_val,
            'iq': iq_val,
            'duty': duty_now,
            'rpm': rpm,
            'v_in': v_in,
            'amp_hours': amp_hours,
            'amp_hours_charged': amp_hours_charged,
            'watt_hours': watt_hours,
            'watt_hours_charged': watt_hours_charged,
            'tachometer': tachometer,
            'tachometer_abs': tachometer_abs
        }
    except Exception as e:
        print(f"[ERROR] パース失敗: {e}")
        print(f"[HEX] {payload.hex()}")
        return None

class VESCReader:
    def __init__(self, ser, interval=0.5,
                 csv_enable=False,
                 csv_filename="vesc_data.csv",
                 csv_fields=None):
        """
        ser: serial.Serial オブジェクト
        interval: サンプリング周期 [s]
        csv_enable: True のときCSV出力を有効化
        csv_filename: 出力ファイル名
        csv_fields: 出力したいキーのリスト（例: ["rpm", "duty", "v_in"]）
        """
        self.ser = ser
        self.interval = interval
        self._buffer = b''
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()  # 一時停止フラグ
        self._thread = None
        self.request_count = 0
        self.success_count = 0

        # === CSV設定 ===
        self.csv_enable = csv_enable
        self.csv_filename = csv_filename
        self.csv_fields = csv_fields
        self._csv_file = None
        self._csv_writer = None
        self._start_time = None

    # ---- 一時停止機能 ----
    def pause(self):
        """読み取りを一時停止（モーター動作中に使用）"""
        self._pause_flag.set()
        print("[READER] Paused")

    def resume(self):
        """読み取りを再開"""
        self._pause_flag.clear()
        print("[READER] Resumed")

    # ---- CSV初期化 ----
    def _init_csv(self):
        if not self.csv_enable:
            return
        os.makedirs(os.path.dirname(self.csv_filename) or ".", exist_ok=True)
        file_exists = os.path.isfile(self.csv_filename)
        self._csv_file = open(self.csv_filename, mode="a", newline="")
        self._csv_writer = csv.DictWriter(self._csv_file, fieldnames=self.csv_fields)
        if not file_exists:
            self._csv_writer.writeheader()
        self._start_time = time.time()
        print(f"[CSV] 出力開始: {self.csv_filename}")

    def _write_csv(self, parsed):
        if not self.csv_enable or self._csv_writer is None:
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

    # ---- VESC通信処理 ----
    def send_get_values(self):
        pkt = build_packet(bytes([COMM_GET_VALUES]))
        self.ser.write(pkt)
        self.request_count += 1

    def _loop(self):
        self._init_csv()
        while not self._stop_flag.is_set():
            try:
                # 一時停止中はスキップ
                if self._pause_flag.is_set():
                    time.sleep(0.1)
                    continue
                
                self.send_get_values()
                time.sleep(0.05)
                data = self.ser.read(self.ser.in_waiting or 256)
                if data:
                    self._buffer += data
                    packets, self._buffer = extract_packets(self._buffer)
                    for payload in packets:
                        parsed = parse_getvalues(payload)
                        if parsed:
                            self.success_count += 1
                            self._write_csv(parsed)
                            # 詳細なログ表示
                            print(f"\n--- データ #{self.success_count} ---")
                            # print(f"FET温度:    {parsed['temp_fet']:.1f}°C")
                            # print(f"モーター温度: {parsed['temp_motor']:.1f}°C")
                            # print(f"モーター電流: {parsed['current_motor']:.2f}A")
                            # print(f"入力電流:   {parsed['current_in']:.2f}A")
                            # print(f"入力電圧:   {parsed['v_in']:.1f}V")
                            print(f"Duty比:     {parsed['duty']:.3f}")
                            print(f"RPM:        {parsed['rpm']}")
                            # print(f"電力量:     {parsed['watt_hours']:.3f}Wh")
                time.sleep(max(0, self.interval - 0.05))
            except Exception as e:
                print(f"[ERROR in reader loop] {e}")
                time.sleep(0.5)
        # 終了時にCSVを閉じる
        if self._csv_file:
            self._csv_file.close()
            print("[CSV] ファイルを閉じました。")

    def start(self):
        if self._thread is None:
            self._stop_flag.clear()
            self._pause_flag.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        if self._thread is not None:
            self._stop_flag.set()
            self._thread.join(timeout=1.0)
            self._thread = None