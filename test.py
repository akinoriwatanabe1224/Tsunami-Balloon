#!/usr/bin/env python3
# vesc_uart_control.py
# requirements: pip3 install pyserial pyvesc

import serial
import threading
import time
import pyvesc
from pyvesc import encode, decode
from pyvesc.VESC.messages import SetDutyCycle, SetRPM, GetValues  # pyvesc のメッセージクラス

SERIAL_PORT = "/dev/serial0"   # Pi の UART. 環境により /dev/ttyAMA0 等に変更
BAUDRATE = 115200
GET_VALUES_INTERVAL = 0.5      # 秒

running = True

def open_serial():
    ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=0.1)
    # 少し待つと安定することが多い
    time.sleep(0.2)
    return ser

def send_msg(ser, msg):
    """pyvesc のメッセージをエンコードして送信"""
    pkt = encode(msg)
    ser.write(pkt)

def reader_thread(ser):
    """受信データをバッファリングして pyvesc.decode でパース、GetValues を検出して表示"""
    buf = b''
    while running:
        try:
            data = ser.read(1024)
            if data:
                buf += data
                # pyvesc.decode はバッファから次のメッセージを取り出すユーティリティ
                while True:
                    try:
                        msg, consumed = decode(buf)
                    except Exception:
                        # まだ完全なパケットが揃っていない等
                        break
                    if msg is None:
                        break
                    # 消費バイトを削る
                    buf = buf[consumed:]
                    # メッセージ内容の表示（GetValues系）
                    clsname = msg.__class__.__name__
                    # GetValues なら有用なフィールドを表示
                    if clsname.lower().find("values") >= 0 or hasattr(msg, "rpm"):
                        # msg の属性を列挙して見やすく表示
                        try:
                            # 一般的なフィールド: rpm, avg_motor_current, v_in, duty_now 等
                            info = {}
                            for k, v in msg.__dict__.items():
                                info[k] = v
                            print("[VESC values] ", info)
                        except Exception:
                            print("[VESC msg] ", msg)
                    else:
                        # デバッグで他メッセージを表示したいときは以下を有効に
                        # print("[VESC other] ", clsname, msg)
                        pass
        except serial.SerialException as e:
            print("Serial error:", e)
            break
        except Exception as e:
            # デコード失敗などは無視してループ継続
            # print("Reader thread exception:", e)
            time.sleep(0.01)

def periodic_get_values(ser):
    """定期的に COMM_GET_VALUES を投げて VESC から値を取得させる"""
    while running:
        try:
            send_msg(ser, GetValues())
        except Exception as e:
            print("send GetValues failed:", e)
        time.sleep(GET_VALUES_INTERVAL)

def control_loop(ser):
    """コンソールからスロットル指定して VESC 制御（Duty/RPM 切替可）"""
    print("Control loop: enter 'd <throttle>' for duty, 'r <rpm>' for rpm, 'stop' to stop, 'exit' to quit.")
    print(" Examples: 'd 50' (50% duty), 'd -20' (reverse -20%), 'r 3000' (set 3000 rpm)")
    while True:
        try:
            line = input(">> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("Exit control loop")
            break
        if not line:
            continue
        if line == "exit":
            global running
            running = False
            break
        if line == "stop":
            # 安全停止: duty 0
            try:
                msg = SetDutyCycle(0)  # 0 で停止
                send_msg(ser, msg)
                print("Sent duty=0")
            except Exception as e:
                print("failed to send stop:", e)
            continue
        parts = line.split()
        if len(parts) != 2:
            print("Invalid input")
            continue
        cmd, val = parts[0], parts[1]
        try:
            if cmd == 'd':
                throttle = float(val)  # user 入力の % または -100..100
                # pyvesc の SetDutyCycle は内部で拡張スケールを使う実装差があるため柔軟に扱う:
                # - 入力が -1..1 の範囲ならそれを 1e5 スケールへ
                # - 入力が -100..100 の範囲なら % として扱い、-1..1 に正規化
                if abs(throttle) <= 1.0:
                    duty_val = int(throttle * 1e5)
                else:
                    # assume percentage -100..100
                    duty_val = int((throttle / 100.0) * 1e5)
                msg = SetDutyCycle(duty_val)
                send_msg(ser, msg)
                print(f"Sent SetDutyCycle({duty_val})")
            elif cmd == 'r':
                rpm = int(float(val))
                msg = SetRPM(rpm)
                send_msg(ser, msg)
                print(f"Sent SetRPM({rpm})")
            else:
                print("Unknown command (use 'd' or 'r')")
        except Exception as e:
            print("Error sending command:", e)

def main():
    ser = open_serial()
    print("Serial opened:", ser.name)
    # 受信用スレッド
    t_reader = threading.Thread(target=reader_thread, args=(ser,), daemon=True)
    t_reader.start()
    # 定期 GET_VALUES スレッド
    t_poll = threading.Thread(target=periodic_get_values, args=(ser,), daemon=True)
    t_poll.start()
    try:
        control_loop(ser)
    finally:
        print("Shutting down...")
        ser.close()

if __name__ == "__main__":
    main()
