"""P3 前置:A100 回拉五演 verdict 锚件(g1_verdict/pusht_4win_verdict/B 修复批 summary)。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
sftp = c.open_sftp()
pulls = [
    ("/root/vdd3/pipe_art/g1_verdict.json", "runtime/loop/_p3_g1_verdict.json"),
    ("/root/vdd3/pipe_art/pusht_4win_verdict.json", "runtime/loop/_p3_pusht_4win_verdict.json"),
    ("/root/vdd3/pipe_art/g1_infer_B/infer_summary.json", "runtime/loop/_p3_B_fixed_infer_summary.json"),
]
for remote, local in pulls:
    sftp.get(remote, local)
    print("[pull]", remote, "->", local)
sftp.close()
_, out, _ = c.exec_command(
    "sha256sum /root/vdd3/pipe_art/g1_verdict.json /root/vdd3/pipe_art/pusht_4win_verdict.json"
    " /root/vdd3/pipe_art/g1_infer_B/infer_summary.json", timeout=15)
print(out.read().decode())
c.close()
