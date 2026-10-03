"""R65 rollout 完成态查:全 summary 落盘否。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
_, out, _ = c.exec_command(
    "ls /root/vdd3/pipe_art/pusht_rollout_20261003_133459/ | grep -E 'summary|jsonl';"
    "echo ---; ls /root/vdd3/pipe_art/ | grep rollout;"
    "echo ---; ps aux | grep pusht_rollout | grep -v grep | wc -l;"
    "echo ---; for f in /root/vdd3/pipe_art/pusht_rollout_20261003_133459/rollout_*_summary.json; do"
    " echo \"== $f\"; cat $f; echo; done", timeout=20)
print(out.read().decode())
c.close()
