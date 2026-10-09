"""R78d:退避后验证 S3 进程+必要时补发车。"""
import time

import paramiko

time.sleep(300)
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=15)
_, out, _ = c.exec_command(
    "n=$(ps aux | grep train_judge_incr | grep -v grep | wc -l); echo procs=$n; "
    "if [ \"$n\" = \"0\" ]; then cd /root && nohup /root/vdd2/p0_full/venv/bin/python "
    "tools/train_judge_incremental.py --ticket runtime/judge_lora_p3/ticket_s3test.json "
    "--model /root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master "
    "--champion-adapter /root/runtime/judge_lora_p2v2/best_lora --epochs 2 "
    "> /root/p3_s3test.log 2>&1 & echo relaunched; else echo already_running; fi; "
    "sleep 2; tail -3 /root/p3_s3test.log", timeout=30)
print(out.read().decode())
c.close()
