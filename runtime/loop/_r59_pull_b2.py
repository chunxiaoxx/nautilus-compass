"""R59 拉取 B2 材料(只读)+ 与 B(v5 批)对照。"""
import paramiko
from pathlib import Path

OUT = Path(__file__).parent
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
_, out, _ = c.exec_command("ls -la /root/vdd3/pipe_art/g1_infer_B2/ && cat /root/vdd3/pipe_art/g1_infer_B2/infer_summary.json", timeout=20)
print(out.read().decode())
for fn in ("infer_compare.jsonl", "infer_summary.json"):
    _, out, _ = c.exec_command(f"cat /root/vdd3/pipe_art/g1_infer_B2/{fn}", timeout=20)
    data = out.read()
    (OUT / f"_r59_B2_{fn}").write_bytes(data)
    print(f"[pull] B2/{fn} {len(data)}B")
c.close()
