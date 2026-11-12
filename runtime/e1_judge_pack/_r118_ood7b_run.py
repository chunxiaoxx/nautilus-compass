import time
import paramiko

HOST, PORT, USER, PWD = "223.109.239.30", 23236, "root", "iefe4Eey"


def connect():
    last = None
    for attempt in range(8):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30)
            return c
        except Exception as e:  # banner 限流退避
            last = e
            print(f"[retry {attempt}] {type(e).__name__}: {e}", flush=True)
            time.sleep(125)
    raise last


c = connect()
# [e] 修法防 pgrep 自匹配(第 4 次同坑)
_, out, _ = c.exec_command('pgrep -f "[e]1_j2_batch_judge_ood_7b" | head -3')
running = out.read().decode().strip()
if running:
    print(f"[skip] already running: {running}", flush=True)
else:
    _, out, _ = c.exec_command(
        "cd /root/runtime/e1_judge_pack && setsid nohup /root/venv/bin/python "
        "e1_j2_batch_judge_ood_7b.py > ood_7b_run.log 2>&1 & echo launched")
    print(f"[launch] {out.read().decode().strip()}", flush=True)
    time.sleep(5)
    _, out, _ = c.exec_command('pgrep -f "[e]1_j2_batch_judge_ood_7b" | head -3')
    print(f"[confirm pid] {out.read().decode().strip() or 'NONE!'}", flush=True)

for k in range(24):
    time.sleep(30)
    _, out, _ = c.exec_command(
        'tail -2 /root/runtime/e1_judge_pack/ood_7b_run.log 2>/dev/null; '
        'pgrep -f "[e]1_j2_batch_judge_ood_7b" >/dev/null && echo RUNNING || echo EXITED')
    txt = out.read().decode(errors="replace").strip()
    print(f"--- poll {k} --- {txt}", flush=True)
    if "[done]" in txt or "EXITED" in txt or "Error" in txt or "Traceback" in txt:
        break

_, out, _ = c.exec_command("tail -15 /root/runtime/e1_judge_pack/ood_7b_run.log 2>/dev/null")
print(out.read().decode(errors="replace"), flush=True)
c.close()
