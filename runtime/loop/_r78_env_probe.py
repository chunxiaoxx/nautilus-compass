"""S3 实测环境探查:A100 有无 Qwen3-1.7B+peft+transformers>=4.57。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=10)
_, out, _ = c.exec_command(
    "ls ~/.cache/modelscope/hub/models/ 2>/dev/null | head -5;"
    "echo ---; ls /root/vdd2/models/ 2>/dev/null | head -8;"
    "echo ---; /root/vdd2/p0_full/venv/bin/python -c 'import transformers,torch; print(transformers.__version__, torch.__version__)' 2>&1;"
    "echo ---; /root/vdd2/p0_full/venv/bin/python -c 'import peft; print(\"peft\", peft.__version__)' 2>&1;"
    "echo ---; find /root -maxdepth 4 -iname '*qwen3*1.7*' -o -maxdepth 4 -iname '*Qwen3-1.7B*' 2>/dev/null | head -5", timeout=30)
print(out.read().decode())
c.close()
