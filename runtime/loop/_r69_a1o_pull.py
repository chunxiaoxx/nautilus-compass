"""R69 拉 A1O 扩 n(100集) summary+逐集 coverage 分布。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=10)
_, out, _ = c.exec_command(
    "cat /root/vdd3/pipe_art/pusht_rollout_20261003_144237/rollout_A1O_summary.json;"
    "echo ---; python3 -c \""
    "import json;"
    "rows=[json.loads(l) for l in open('/root/vdd3/pipe_art/pusht_rollout_20261003_144237/rollout_A1O.jsonl')];"
    "covs=sorted(r.get('final_coverage',0) for r in rows);"
    "print('n:',len(rows));"
    "print('max:',round(covs[-1],4),'p95:',round(covs[int(len(covs)*0.95)-1],4),'median:',round(covs[len(covs)//2],4));"
    "print('ge_0.3:',sum(1 for x in covs if x>=0.3),'ge_0.5:',sum(1 for x in covs if x>=0.5))\"", timeout=20)
print(out.read().decode())
c.close()
