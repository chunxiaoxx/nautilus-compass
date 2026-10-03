"""R67 新 rollout 批 144237 内容查。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
_, out, _ = c.exec_command(
    "ls /root/vdd3/pipe_art/pusht_rollout_20261003_144237/;"
    "echo ---; cat /root/vdd3/pipe_art/pusht_rollout_20261003_144237/env_fingerprint.json 2>/dev/null | head -30;"
    "echo ---; for f in /root/vdd3/pipe_art/pusht_rollout_20261003_144237/rollout_*_summary.json; do"
    " [ -f \"$f\" ] && echo \"== $f\" && cat \"$f\"; done", timeout=20)
print(out.read().decode())
c.close()
