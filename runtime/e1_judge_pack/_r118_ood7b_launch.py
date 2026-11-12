import sys
import time
import paramiko

HOST, PORT, USER, PWD = "223.109.239.30", 23236, "root", "iefe4Eey"

c = None
for attempt in range(4):
    try:
        c = paramiko.SSHClient()
        c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(HOST, port=PORT, username=USER, password=PWD,
                  timeout=30, banner_timeout=30)
        break
    except Exception as e:
        print(f"[retry {attempt}] {type(e).__name__}", flush=True)
        time.sleep(125)
if c is None:
    sys.exit("connect failed after 4 attempts")

PG = 'pgrep -f "[e]1_j2_batch_judge_ood_7b"'
_, out, _ = c.exec_command(PG)
running = out.read().decode().strip()
if running:
    print(f"[already] pid={running}", flush=True)
else:
    _, out, _ = c.exec_command(
        "cd /root/runtime/e1_judge_pack && setsid nohup /root/venv/bin/python "
        "e1_j2_batch_judge_ood_7b.py > ood_7b_run.log 2>&1 & echo launched")
    print(f"[launch] {out.read().decode().strip()}", flush=True)
    time.sleep(6)
    _, out, _ = c.exec_command(PG)
    print(f"[confirm pid] {out.read().decode().strip() or 'NONE!'}", flush=True)
c.close()
