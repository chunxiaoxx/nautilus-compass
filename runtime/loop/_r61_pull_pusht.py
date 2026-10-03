"""R61 拉取 pusht 四窗材料(只读,单连接)+ A2F/A2N 字节一致核验。"""
import paramiko
from pathlib import Path

OUT = Path(__file__).parent
WINS = ("A1O", "A1N", "A2F", "A2N")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
_, out, _ = c.exec_command(
    "ls -la /root/vdd3/pipe_art/ | grep pusht; "
    "sha256sum /root/vdd3/pipe_art/pusht_infer_A2F/infer_compare.jsonl "
    "/root/vdd3/pipe_art/pusht_infer_A2N/infer_compare.jsonl | cut -c1-80", timeout=20)
print(out.read().decode())
for w in WINS:
    for fn in ("infer_compare.jsonl", "infer_summary.json"):
        _, out, _ = c.exec_command(f"cat /root/vdd3/pipe_art/pusht_infer_{w}/{fn}", timeout=20)
        data = out.read()
        (OUT / f"_r61_{w}_{fn}").write_bytes(data)
        print(f"[pull] {w}/{fn} {len(data)}B")
_, out, _ = c.exec_command("cat /root/vdd3/pipe_art/pusht_infer_all_summary.json", timeout=20)
(OUT / "_r61_all_summary.json").write_bytes(out.read())
print("[pull] all_summary", len(out.read() if False else b"") or "ok")
c.close()
