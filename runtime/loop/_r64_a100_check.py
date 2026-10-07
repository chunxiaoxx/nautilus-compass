"""R64 A100 值守:G1/pusht 材料 mtime+新目录+GPU 占用一查。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="A100_PW_ENV", timeout=10)
_, out, _ = c.exec_command(
    "ls -lt /root/vdd3/pipe_art/ | head -12;"
    "echo ---; sha256sum /root/vdd3/pipe_art/g1_infer_G/infer_compare.jsonl"
    " /root/vdd3/pipe_art/g1_infer_B2/infer_compare.jsonl 2>/dev/null | cut -c1-16,66-;"
    "echo ---; ls /root/vdd3/pipe_art/ | grep -i rollout;"
    "echo ---; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader;"
    "echo ---; ps aux | grep -E 'rollout|infer' | grep -v grep | head -5", timeout=20)
print(out.read().decode())
c.close()
