"""R89:exp2 扫描链发车——6 组合串行(LR×epochs),预注册判读规则先落盘后跑。

矩阵:exp2a(5e-5,3) b(2e-4,3) c(1e-4,5) d(5e-5,5) e(2e-4,5) f(1e-4,8)
预计每 run ~7min,总 ~45min;日志 /root/p3_exp2.log,summary 逐个落 exp/。
"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=15)
s = c.open_sftp()
s.put("tools/exp_runner.py", "/root/tools/exp_runner.py")
s.close()

runs = [("exp2a", "5e-5", 3), ("exp2b", "2e-4", 3), ("exp2c", "1e-4", 5),
        ("exp2d", "5e-5", 5), ("exp2e", "2e-4", 5), ("exp2f", "1e-4", 8)]
PY = "./vdd2/p0_full/venv/bin/python"
chain = " && ".join(
    f"{PY} tools/exp_runner.py --tag {t} --lr {lr} --epochs {ep}" for t, lr, ep in runs)
cmd = (f"cd /root && (setsid nohup bash -c '{chain}' "
       f"> /root/p3_exp2.log 2>&1 < /dev/null &) ; echo chain_launched")
_, out, _ = c.exec_command(cmd, timeout=15)
print(out.read().decode())

import time
time.sleep(10)
_, out, _ = c.exec_command(
    "ps aux | grep exp_runner | grep -v grep | head -2; echo ---; tail -3 /root/p3_exp2.log 2>/dev/null",
    timeout=20)
print(out.read().decode())
c.close()
