"""R56 G1 B 臂与 GPU 快查(只读,单连接)。"""
import paramiko

CMDS = [
    "ls -la /root/vdd3/pipe_art/g1_infer_B/",
    "nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader; nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader",
    "ps aux | grep -E 'train.py|g1_infer|infer_compare' | grep -v grep | head -5",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
for cmd in CMDS:
    _, out, err = c.exec_command(cmd, timeout=20)
    print(f"$ {cmd}")
    print(out.read().decode().strip() or err.read().decode().strip() or "(空)")
    print("---")
c.close()
