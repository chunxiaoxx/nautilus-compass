"""R54 探查三(只读):G 新材料内容 vs 三条修复建议核对 + B 臂现状。"""
import paramiko

CMDS = [
    "cat /root/vdd3/pipe_art/g1_infer_G/infer_summary.json",
    "cat /root/vdd3/pipe_art/g1_infer_B/infer_summary.json",
    "head -c 1500 /root/vdd3/pipe_art/g1_infer_G/infer_compare.jsonl",
    "wc -l /root/vdd3/pipe_art/g1_infer_G/infer_compare.jsonl /root/vdd3/pipe_art/g1_infer_B/infer_compare.jsonl",
    "ps aux | grep -i 'g1_infer\\|infer_compare' | grep -v grep | head -5",
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
for cmd in CMDS:
    _, out, err = c.exec_command(cmd, timeout=20)
    print(f"$ {cmd}")
    print(out.read().decode().strip() or err.read().decode().strip() or "(空)")
    print("---")
c.close()
