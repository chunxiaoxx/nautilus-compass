"""R78c:modelscope 权重就位,续跑 S3 实测(2 epochs)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
_, out, _ = c.exec_command(
    "ls /root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master/*.safetensors | head -3;"
    "cd /root && nohup /root/vdd2/p0_full/venv/bin/python tools/train_judge_incremental.py "
    "--ticket runtime/judge_lora_p3/ticket_s3test.json "
    "--model /root/.cache/modelscope/models/Qwen--Qwen3-1.7B/snapshots/master "
    "--champion-adapter /root/runtime/judge_lora_p2v2/best_lora "
    "--epochs 2 > /root/p3_s3test.log 2>&1 & echo relaunched", timeout=15)
print(out.read().decode())
c.close()
