"""E1 自动编排:轮询 VL 下载 DONE→exp2 链清→launch 批判→拉回结果。

本地后台跑(每 5min 探一次);状态落 runtime/e1_judge_pack/orchestrate_state.json。
SSH 限流退避 300s;远端命令一律脚本文件(已上传 _vl_download/e1_j2_batch_judge)。
"""
import json
import time
from pathlib import Path

import paramiko

STATE = Path("runtime/e1_judge_pack/orchestrate_state.json")


def probe(c):
    _, out, _ = c.exec_command(
        "grep -c DONE /root/vl_download.log 2>/dev/null; "
        "grep -c 'done:' /root/p3_exp2.log 2>/dev/null; "
        "ls /root/runtime/e1_judge_pack/j2_answers.jsonl 2>/dev/null | wc -l", timeout=30)
    dl_done, exp2_done, ans = [x.strip() for x in out.read().decode().splitlines()]
    return int(dl_done or 0), int(exp2_done or 0), int(ans or 0)


def connect():
    for i in range(4):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect("223.109.239.30", port=23236, username="root",
                      password="iefe4Eey", timeout=20)
            return c
        except Exception as e:
            print(f"[retry {i + 1}] {type(e).__name__}", flush=True)
            time.sleep(300)
    raise SystemExit(1)


def save(stage, **kw):
    STATE.write_text(json.dumps({"stage": stage, "ts": time.strftime("%H:%M:%S"),
                                 **kw}, ensure_ascii=False, indent=1), encoding="utf-8")


for tick in range(60):  # 最多 5h
    try:
        c = connect()
        dl, exp2, ans = probe(c)
        print(f"[{time.strftime('%H:%M:%S')}] dl_done={dl} exp2={exp2}/6 answers={ans}",
              flush=True)
        if ans > 0:  # 批判已出过件
            save("judging_done", answers=ans)
            c.close()
            break
        if dl >= 1 and exp2 >= 6:
            _, out, _ = c.exec_command(
                "cd /root && (setsid nohup ./vdd2/p0_full/venv/bin/python "
                "tools/e1_j2_batch_judge.py > /root/e1_judge.log 2>&1 < /dev/null &) ; "
                "echo judging_launched", timeout=15)
            print(out.read().decode(), flush=True)
            save("judging_launched")
            c.close()
            time.sleep(1800)  # 判读跑 ~30min,之后下轮拉回
            continue
        save("waiting", dl_done=dl, exp2=exp2)
        c.close()
    except SystemExit:
        raise
    except Exception as e:
        print(f"[err] {type(e).__name__}: {e}", flush=True)
        save("error", err=str(e)[:200])
    time.sleep(300)
