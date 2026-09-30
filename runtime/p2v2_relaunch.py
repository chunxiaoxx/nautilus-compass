# -*- coding: utf-8 -*-
"""重启 P2v2 LoRA 训练(先建目录;启动与验证分两步,避免 channel 挂起)。"""
import paramiko, sys, time

HOST, PORT, USER, PW = "js2.blockelite.cn", 15124, "root", "REDACTED_JS2_PW"

def run(c, cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode("utf-8", "replace").strip(), err.read().decode("utf-8", "replace").strip()

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)

    # 1) 纯启动:整条命令包进 () 子 shell 后台,exec 本身立即返回零输出
    run(c, "mkdir -p /root/runtime/judge_lora && "
           "(setsid bash /root/p2v2_bootstrap_and_train.sh > /root/runtime/judge_lora/run.log 2>&1 < /dev/null &)")
    time.sleep(8)

    # 2) 验证:进程在跑 + 日志有输出
    o, _ = run(c, "ps aux | grep '[b]ootstrap_and_train' | wc -l")
    print("bootstrap_procs:", o)
    o, _ = run(c, "tail -10 /root/runtime/judge_lora/run.log")
    print("== run.log:"); print(o)
    c.close()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
