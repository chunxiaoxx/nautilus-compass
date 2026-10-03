"""R65 部署 rollout 判读脚本并执行。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
sftp = c.open_sftp()
sftp.put("tools/pusht_rollout_judge_v1.py", "/root/pusht_rollout_judge_v1.py")
sftp.close()
print("[deploy] /root/pusht_rollout_judge_v1.py")
_, out, err = c.exec_command("python3 /root/pusht_rollout_judge_v1.py 2>&1 | tail -12", timeout=60)
print(out.read().decode())
c.close()
