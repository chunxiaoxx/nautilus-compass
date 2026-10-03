"""R78f:上传修正脚本+修正版训练器,远端重跑双臂预测,拉回本地。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=15)
s = c.open_sftp()
s.put("tools/train_judge_incremental.py", "/root/tools/train_judge_incremental_fixed.py")
s.put("runtime/loop/_r78e_repredict.py", "/root/_r78e_repredict.py")
s.close()
print("[uploaded]")
c.close()
