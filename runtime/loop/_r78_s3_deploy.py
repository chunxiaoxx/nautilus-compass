"""R78 S3 工程实测部署:A100 镜像仓结构+传数据/adapter+造 mini ticket+跑 2 epochs。

留痕:共享 A100 跑 ~20min 训练(GPU 空闲窗),目的=管道链路验证(热启动/replay/双臂预测),
产物标 engineering_test 不入岗(14 条无统计意义,不过 gate 不 promote)。
"""
import json

import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
c.exec_command("mkdir -p /root/tools /root/runtime/verdict_corpus/delta "
               "/root/runtime/judge_lora_p3/evals /root/runtime/judge_lora_p2v2/best_lora", timeout=10)[1].read()
sftp = c.open_sftp()
puts = [
    ("tools/train_judge_incremental.py", "/root/tools/train_judge_incremental.py"),
    ("runtime/verdict_corpus/reg100.jsonl", "/root/runtime/verdict_corpus/reg100.jsonl"),
    ("runtime/verdict_corpus/split_train.jsonl", "/root/runtime/verdict_corpus/split_train.jsonl"),
    ("runtime/verdict_corpus/split_test.jsonl", "/root/runtime/verdict_corpus/split_test.jsonl"),
    ("runtime/verdict_corpus/delta/delta_0001.jsonl", "/root/runtime/verdict_corpus/delta/delta_0001.jsonl"),
    ("runtime/judge_lora_p3/champion.json", "/root/runtime/judge_lora_p3/champion.json"),
]
for l, r in puts:
    sftp.put(l, r)
    print("[put]", r)
import glob
for f in glob.glob("runtime/judge_lora_p2v2/best_lora/*"):
    sftp.put(f, "/root/runtime/judge_lora_p2v2/best_lora/" + f.replace("\\", "/").rsplit("/", 1)[1])
print("[put] best_lora/*")
ticket = {"ticket_id": "ticket_s3test",
          "pending_deltas": [{"file": "delta_0001.jsonl", "sha16": "ed36f118343de453"}]}
with sftp.open("/root/runtime/judge_lora_p3/ticket_s3test.json", "w") as fh:
    fh.write(json.dumps(ticket))
print("[put] ticket_s3test.json")
sftp.close()
_, out, err = c.exec_command(
    "cd /root && nohup /root/vdd2/p0_full/venv/bin/python tools/train_judge_incremental.py "
    "--ticket runtime/judge_lora_p3/ticket_s3test.json "
    "--model /root/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots/*/ "
    "--champion-adapter /root/runtime/judge_lora_p2v2/best_lora "
    "--epochs 2 > /root/p3_s3test.log 2>&1 & echo started", timeout=15)
print(out.read().decode())
c.close()
