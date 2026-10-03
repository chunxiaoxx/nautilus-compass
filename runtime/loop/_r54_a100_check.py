"""R54 轮一次性探查(只读):G1 新材料判定 + turbo 提取产物确认。

判定口径:R53 已判 verdict 锚定 sha G=7288ed69/B=413e6aba;
summary.json 内容 sha 不变=无新材料=不重判。turbo:产物齐=④条件不触发。
"""
import paramiko

CMDS = [
    "ls -la /root/vdd3/pipe_art/g1_infer_G/summary.json /root/vdd3/pipe_art/g1_infer_B/summary.json 2>&1",
    "sha256sum /root/vdd3/pipe_art/g1_infer_G/summary.json /root/vdd3/pipe_art/g1_infer_B/summary.json 2>&1 | cut -c1-80",
    "cat /root/vdd3/pipe_art/g1_verdict.json 2>&1 | head -c 400",
    "ls -la /root/vdd2/p0_full/out/ 2>&1",
    "nvidia-smi --query-compute-apps=pid --format=csv,noheader | wc -l",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="iefe4Eey", timeout=10)
for cmd in CMDS:
    _, out, err = c.exec_command(cmd, timeout=20)
    print(f"$ {cmd.split('2>&1')[0].strip()}")
    print(out.read().decode().strip() or err.read().decode().strip())
    print("---")
c.close()
