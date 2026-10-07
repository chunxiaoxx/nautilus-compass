"""R59 部署 v3 判分脚本并以 B2 批为锚执行(SFTP+env 覆盖+回读 verdict 关键段)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
sftp = c.open_sftp()
sftp.put("tools/g1_judge_v1.py", "/root/g1_judge_v1.py")
sftp.close()
print("[deploy] /root/g1_judge_v1.py <- tools/g1_judge_v1.py")
_, out, err = c.exec_command(
    "G1_B_DIR=g1_infer_B2 python3 /root/g1_judge_v1.py >/tmp/g1j.out 2>/tmp/g1j.err;"
    "python3 -c \"import json; v=json.load(open('/root/vdd3/pipe_art/g1_verdict.json'));"
    "print(v['ts'], v['judge'], v['material_dirs']);"
    "print('verdict:', v['verdict']);"
    "print('quality:', v['material_quality']);"
    "import json as j; print('diff:', j.dumps(v['differential'], ensure_ascii=False));"
    "print('G:', v['arms']['G']['rows_sha16'], 'B:', v['arms']['B']['rows_sha16'])\"",
    timeout=60)
print(out.read().decode())
e = err.read().decode().strip()
if e:
    print("[stderr]", e[:300])
c.close()
