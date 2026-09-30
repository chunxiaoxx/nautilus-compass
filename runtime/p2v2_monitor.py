# -*- coding: utf-8 -*-
"""P2v2 LoRA 训练监控:每 3 分钟查 run.log,出现 DONE/Traceback/断言失败即退出(由 harness 通知)。"""
import paramiko, sys, time

HOST, PORT, USER, PW = "js2.blockelite.cn", 15124, "root", "Coh9ech3"
LOG = "/root/runtime/judge_lora/run.log"
DEADLINE = time.time() + 3.2 * 3600  # 3.2h 硬上限

def tail(c, n=4000):
    _, out, _ = c.exec_command(f"tail -c {n} {LOG}", timeout=30)
    return out.read().decode("utf-8", "replace")

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    last = ""
    while time.time() < DEADLINE:
        try:
            if c.get_transport() is None or not c.get_transport().is_active():
                c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)
            txt = tail(c)
            if txt != last:
                lines = [l for l in txt.splitlines() if l.strip()]
                print(f"--- [{time.strftime('%H:%M:%S')}] tail:", lines[-1][:150] if lines else "(empty)", flush=True)
                last = txt
            if "=== DONE ===" in txt:
                print("TRAIN_DONE", flush=True)
                _, out, _ = c.exec_command("cat /root/runtime/judge_lora/eval_report.json 2>/dev/null", timeout=30)
                print(out.read().decode("utf-8", "replace"), flush=True)
                return
            for sig in ("Traceback", "J5 FAIL", "AssertionError", "CUDA out of memory", "Killed"):
                if sig in txt:
                    print(f"TRAIN_FAIL sig={sig}", flush=True)
                    print(txt[-1500:], flush=True)
                    return
        except Exception as e:
            print(f"probe_err: {e}", flush=True)
            time.sleep(20)
        time.sleep(180)
    print("MONITOR_TIMEOUT 3.2h", flush=True)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        main()
    except KeyboardInterrupt:
        pass
