"""R67 A100 轻查:pipe_art mtime 头+G1 双锚+svla 新踪迹。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=10)
_, out, _ = c.exec_command(
    "ls -lt /root/vdd3/pipe_art/ | head -8;"
    "echo ---; sha256sum /root/vdd3/pipe_art/g1_infer_G/infer_compare.jsonl"
    " /root/vdd3/pipe_art/g1_infer_B2/infer_compare.jsonl 2>/dev/null | cut -c1-16;"
    "echo ---; ls /root/vdd3/pipe_art/svla_qc_v0/ 2>/dev/null | wc -l;"
    "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader;"
    "ps aux | grep -E 'rollout|infer|qc' | grep -v grep | wc -l", timeout=20)
print(out.read().decode())
c.close()
