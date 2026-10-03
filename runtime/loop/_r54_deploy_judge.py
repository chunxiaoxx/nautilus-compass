"""R54 部署 v3 判分脚本到 A100 并执行(一次会话:SFTP 上传→运行→回读 verdict)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
sftp = c.open_sftp()
sftp.put("tools/g1_judge_v1.py", "/root/g1_judge_v1.py")
sftp.close()
print("[deploy] /root/g1_judge_v1.py <- tools/g1_judge_v1.py")
_, out, err = c.exec_command("python3 /root/g1_judge_v1.py", timeout=60)
txt = out.read().decode()
print(txt[-2600:] if len(txt) > 2600 else txt)
e = err.read().decode().strip()
if e:
    print("[stderr]", e[:500])
c.close()
