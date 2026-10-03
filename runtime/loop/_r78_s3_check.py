"""R78 S3 实测日志检查(启动 3min 后)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
_, out, _ = c.exec_command("tail -25 /root/p3_s3test.log", timeout=15)
print(out.read().decode())
c.close()
