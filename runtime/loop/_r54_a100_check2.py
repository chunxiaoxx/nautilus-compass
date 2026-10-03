"""R54 探针自检(只读):g1 材料真实目录结构+08:21 verdict 后是否有新增。"""
import paramiko

CMDS = [
    "ls -la /root/vdd3/pipe_art/ 2>&1",
    "ls -la /root/vdd3/pipe_art/g1_infer_G/ /root/vdd3/pipe_art/g1_infer_B/ 2>&1 | head -40",
    "find /root/vdd3/pipe_art -name 'summary.json' -newer /root/vdd3/pipe_art/g1_verdict.json 2>/dev/null",
    "find /root/vdd3/pipe_art -newermt '2026-10-03 08:21' -type f 2>/dev/null | head -20",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=10)
for cmd in CMDS:
    _, out, err = c.exec_command(cmd, timeout=20)
    print(f"$ {cmd}")
    print(out.read().decode().strip() or err.read().decode().strip() or "(空)")
    print("---")
c.close()
