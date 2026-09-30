# -*- coding: utf-8 -*-
"""杀旧进程 → 上传镜像下载脚本 → 重启管道(镜像下载 → 训练)。"""
import paramiko, sys, time

HOST, PORT, USER, PW = "js2.blockelite.cn", 15124, "root", "Coh9ech3"

CHAIN = (
    "python3 /root/p2v2_dl_mirror.py && "
    "echo '=== [train] start ===' && "
    "python3 /root/tools/train_judge_lora.py && "
    "echo '=== DONE ==='"
)

def run(c, cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode("utf-8", "replace").strip(), err.read().decode("utf-8", "replace").strip()

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)

    sftp = c.open_sftp()
    sftp.put("runtime/p2v2_dl_mirror.py", "/root/p2v2_dl_mirror.py")
    sftp.close()

    # 杀掉卡死的旧 resume 管道
    run(c, "pkill -f resume_and_train; pkill -f 'snapshot_download'; sleep 1; "
           "ps aux | grep -c '[r]esume_and_train' || true")

    run(c, f"(setsid bash -c '{CHAIN}' > /root/runtime/judge_lora/run.log 2>&1 < /dev/null &)")
    time.sleep(10)
    o, _ = run(c, "ps aux | grep -c '[p]2v2_dl_mirror'")
    print("dl_procs:", o)
    o, _ = run(c, "tail -5 /root/runtime/judge_lora/run.log")
    print("== run.log:"); print(o)
    c.close()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
