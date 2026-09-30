# -*- coding: utf-8 -*-
"""上传续跑脚本并重启训练(防 channel 挂起:启动与验证分步)。"""
import paramiko, sys, time

HOST, PORT, USER, PW = "js2.blockelite.cn", 15124, "root", "REDACTED_JS2_PW"

def run(c, cmd, timeout=30):
    _, out, err = c.exec_command(cmd, timeout=timeout)
    return out.read().decode("utf-8", "replace").strip(), err.read().decode("utf-8", "replace").strip()

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)

    sftp = c.open_sftp()
    sftp.put("runtime/p2v2_resume_and_train.sh", "/root/p2v2_resume_and_train.sh")
    sftp.close()
    run(c, "sed -i 's/\\r$//' /root/p2v2_resume_and_train.sh")

    run(c, "(setsid bash /root/p2v2_resume_and_train.sh > /root/runtime/judge_lora/run.log 2>&1 < /dev/null &)")
    time.sleep(10)
    o, _ = run(c, "ps aux | grep -c '[r]esume_and_train'")
    print("resume_procs:", o)
    o, _ = run(c, "tail -6 /root/runtime/judge_lora/run.log")
    print("== run.log:"); print(o)
    c.close()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
