"""R54 拉取 G/B 材料到本地(只读),供独立复算 J1/J2/sha。"""
import paramiko
from pathlib import Path

OUT = Path(__file__).parent
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
for arm in "GB":
    for fn in ("infer_compare.jsonl", "infer_summary.json"):
        remote = f"/root/vdd3/pipe_art/g1_infer_{arm}/{fn}"
        _, out, _ = c.exec_command(f"cat {remote}", timeout=20)
        data = out.read()
        (OUT / f"_r54_{arm}_{fn}").write_bytes(data)
        print(f"[pull] {arm}/{fn} {len(data)}B")
c.close()
