"""R78b:检查缓存缺失分片+modelscope 补下载 Qwen3-1.7B。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
_, out, _ = c.exec_command(
    "ls -la /root/.cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots/*/ 2>/dev/null;"
    "echo ---; /root/vdd2/p0_full/venv/bin/pip install -q modelscope 2>&1 | tail -1;"
    "nohup /root/vdd2/p0_full/venv/bin/python -c \""
    "from modelscope import snapshot_download;"
    "p = snapshot_download('Qwen/Qwen3-1.7B');"
    "print('[done]', p)\" > /root/ms_dl_17b.log 2>&1 & echo dl_started", timeout=120)
print(out.read().decode())
c.close()
