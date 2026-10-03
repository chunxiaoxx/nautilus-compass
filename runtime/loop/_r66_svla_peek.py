"""R66 svla_qc_v0 新目录特征查(只读)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
_, out, _ = c.exec_command(
    "find /root/vdd3/pipe_art/svla_qc_v0 -maxdepth 2 | head -20;"
    "echo ---; for f in $(find /root/vdd3/pipe_art/svla_qc_v0 -maxdepth 1 -name '*.md' -o -maxdepth 1 -name '*.json' | head -3); do echo \"== $f\"; head -c 600 \"$f\"; echo; done", timeout=20)
print(out.read().decode())
c.close()
