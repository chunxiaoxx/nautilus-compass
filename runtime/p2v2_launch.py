# -*- coding: utf-8 -*-
"""上传启动脚本并 setsid 后台启动 P2v2 LoRA 训练。"""
import paramiko, sys, time

HOST, PORT, USER, PW = "js2.blockelite.cn", 15124, "root", "REDACTED_JS2_PW"

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)

    sftp = c.open_sftp()
    sftp.put("runtime/p2v2_bootstrap_and_train.sh", "/root/p2v2_bootstrap_and_train.sh")
    sftp.close()

    # 防 Windows CRLF 行尾炸 bash
    _, out, err = c.exec_command(
        "sed -i 's/\\r$//' /root/p2v2_bootstrap_and_train.sh && chmod +x /root/p2v2_bootstrap_and_train.sh && "
        "setsid nohup bash /root/p2v2_bootstrap_and_train.sh > /root/runtime/judge_lora/run.log 2>&1 < /dev/null & "
        "echo started_pid=$!", timeout=30)
    print(out.read().decode().strip())
    e = err.read().decode().strip()
    if e:
        print("stderr:", e)
    time.sleep(3)
    _, out, _ = c.exec_command("tail -5 /root/runtime/judge_lora/run.log && ps aux | grep -c '[t]rain_judge_lora\\|[b]ootstrap_and_train'", timeout=20)
    print("== run.log head:"); print(out.read().decode().strip())
    c.close()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
