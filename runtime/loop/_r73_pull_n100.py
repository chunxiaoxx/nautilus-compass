"""R73 终判数据回拉:n=100 四窗逐局 jsonl+全 summary。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
sftp = c.open_sftp()
base = "/root/vdd3/pipe_art/pusht_rollout_20261003_144237"
import pathlib
out = pathlib.Path("runtime/loop/_r73_n100")
out.mkdir(exist_ok=True)
for w in ("A1O", "A1N", "A2F", "A2N"):
    sftp.get(f"{base}/rollout_{w}.jsonl", str(out / f"rollout_{w}.jsonl"))
sftp.get(f"{base}/rollout_all_summary.json", str(out / "rollout_all_summary.json"))
sftp.close()
print("[pulled] 4 jsonl + all_summary")
_, o, _ = c.exec_command(f"sha256sum {base}/rollout_*.jsonl {base}/rollout_all_summary.json", timeout=15)
print(o.read().decode())
c.close()
