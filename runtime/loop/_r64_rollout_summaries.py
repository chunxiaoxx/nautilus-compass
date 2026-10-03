"""R64 回拉已完成 rollout summary(A1N/A1O+smoke A2F)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
_, out, _ = c.exec_command(
    "echo '== smoke A2F (133210)'; cat /root/vdd3/pipe_art/pusht_rollout_20261003_133210/rollout_A2F_summary.json;"
    "echo; echo '== full A1N'; cat /root/vdd3/pipe_art/pusht_rollout_20261003_133459/rollout_A1N_summary.json;"
    "echo; echo '== full A1O'; cat /root/vdd3/pipe_art/pusht_rollout_20261003_133459/rollout_A1O_summary.json;"
    "echo; echo '== env_fingerprint'; cat /root/vdd3/pipe_art/pusht_rollout_20261003_133459/env_fingerprint.json", timeout=20)
print(out.read().decode())
c.close()
