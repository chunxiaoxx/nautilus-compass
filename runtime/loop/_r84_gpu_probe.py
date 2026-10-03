"""R84 GPU 探针:A100(674042 lyg1132)活性+计费状态+关键资产盘点。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=15)
_, out, _ = c.exec_command(
    "uptime;"
    "echo ---GPU---; nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv 2>&1 | head -5;"
    "echo ---PROC---; ps aux | grep -E 'python|train|infer' | grep -v grep | head -8;"
    "echo ---DISK---; df -h /root 2>/dev/null | tail -2;"
    "echo ---CKPT---; ls /root/openpi/checkpoints/ 2>/dev/null | head; ls /root/vdd2/ 2>/dev/null | head -8;"
    "echo ---LAST---; ls -lt /root/vdd3/pipe_art/ 2>/dev/null | head -6", timeout=40)
print(out.read().decode())
c.close()
