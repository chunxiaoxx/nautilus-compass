"""R64 rollout 目录内容特征查(判定完成信号用)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
_, out, _ = c.exec_command(
    "for d in /root/vdd3/pipe_art/pusht_rollout_*/; do echo \"== $d\"; ls -la $d | head -8; done;"
    "echo ---; tail -3 /root/vdd3/pipe_art/pusht_rollout_20261003_133459/*.log 2>/dev/null || "
    "ls /root/vdd3/pipe_art/pusht_rollout_20261003_133459/;"
    "echo ---; ps -o etime= -p 1596093 2>/dev/null", timeout=20)
print(out.read().decode())
c.close()
