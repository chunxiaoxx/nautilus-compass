# -*- coding: utf-8 -*-
"""拉回 P2v2 训练产物(eval_report/run.log/best_lora)到本地并验证完整性。"""
import paramiko, sys, os

HOST, PORT, USER, PW = "js2.blockelite.cn", 15124, "root", "Coh9ech3"
REMOTE = "/root/runtime/judge_lora"
LOCAL = "runtime/judge_lora_p2v2"

def main():
    os.makedirs(LOCAL + "/best_lora", exist_ok=True)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)
    sftp = c.open_sftp()

    for f in ("eval_report.json", "run.log"):
        sftp.get(f"{REMOTE}/{f}", f"{LOCAL}/{f}")
        print("got", f, os.path.getsize(f"{LOCAL}/{f}"), "bytes")

    for f in sftp.listdir(f"{REMOTE}/best_lora"):
        sftp.get(f"{REMOTE}/best_lora/{f}", f"{LOCAL}/best_lora/{f}")
        print("got best_lora/" + f, os.path.getsize(f"{LOCAL}/best_lora/{f}"), "bytes")

    sftp.close(); c.close()
    # 完整性: adapter safetensors 应 ~25MB
    sz = os.path.getsize(f"{LOCAL}/best_lora/adapter_model.safetensors")
    print("[verify] adapter size:", round(sz / 1e6, 1), "MB ->", "PASS" if sz > 20e6 else "FAIL")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
