"""R69 扩 n 批 144237 进展查。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=10)
_, out, _ = c.exec_command(
    "ls /root/vdd3/pipe_art/pusht_rollout_20261003_144237/ | grep -c final_A1O;"
    "ls /root/vdd3/pipe_art/pusht_rollout_20261003_144237/ | grep -c final_A1N;"
    "ls /root/vdd3/pipe_art/pusht_rollout_20261003_144237/ | grep -c final_A2F;"
    "ls /root/vdd3/pipe_art/pusht_rollout_20261003_144237/ | grep -c final_A2N;"
    "echo ---; ls /root/vdd3/pipe_art/pusht_rollout_20261003_144237/ | grep summary;"
    "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader", timeout=20)
print(out.read().decode())
c.close()
