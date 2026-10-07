"""R63 探查配对帧材料 schema(pusht_infer_pair/)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
_, out, err = c.exec_command(
    "ls -la /root/vdd3/pipe_art/pusht_infer_pair/ 2>&1;"
    "echo ---; head -c 1200 /root/vdd3/pipe_art/pusht_infer_pair/paired_compare.jsonl 2>&1;"
    "echo; echo ---; cat /root/vdd3/pipe_art/pusht_infer_pair/paired_summary.json 2>&1;"
    "echo ---; wc -l /root/vdd3/pipe_art/pusht_infer_pair/paired_compare.jsonl 2>&1", timeout=20)
print(out.read().decode())
e = err.read().decode()
if e.strip():
    print("[stderr]", e[:500])
c.close()
