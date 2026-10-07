"""R55 A100 实际工作探查(只读):进程/GPU/G1 B 臂是否重跑/pipe 区新增。"""
import paramiko

CMDS = [
    "nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader",
    "ps aux --sort=-%cpu | head -8",
    "ls -la /root/vdd3/pipe_art/g1_infer_B/ /root/vdd3/pipe_art/g1_infer_G/",
    "find /root/vdd3/pipe_art -newermt '2026-10-03 10:00' -type f 2>/dev/null | head",
    "ls -la /root/openpi/checkpoints/ 2>/dev/null | head; ls /root/vdd3/ 2>/dev/null",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
for cmd in CMDS:
    _, out, err = c.exec_command(cmd, timeout=20)
    print(f"$ {cmd}")
    print(out.read().decode().strip() or err.read().decode().strip() or "(空)")
    print("---")
c.close()
