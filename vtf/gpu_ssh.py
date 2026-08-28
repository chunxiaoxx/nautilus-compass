"""GPU 机非交互 SSH 执行器(paramiko)· 用法: python3 gpu_ssh.py "command" [upload local remote]"""
import sys

import paramiko

HOST, PORT, USER, PW = "223.109.239.32", 10516, "root", "ieco7Xah"
# 2026-08-29 · js3.blockelite.cn 域名解析不稳(180.127.11.1 拒连),改用户提供的
# 移动线直连 IP;备用:电信 180.127.11.166:10516 · vipuser/ieco7Xah


def client():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, PORT, USER, PW, timeout=20)
    return c


def main():
    c = client()
    try:
        if sys.argv[1] == "upload":
            sftp = c.open_sftp()
            sftp.put(sys.argv[2], sys.argv[3])
            print(f"UPLOADED {sys.argv[2]} -> {sys.argv[3]}")
            return
        cmd = sys.argv[1]
        _, out, err = c.exec_command(cmd, timeout=300)
        o = out.read().decode("utf-8", "replace")
        e = err.read().decode("utf-8", "replace")
        print(o, end="")
        if e.strip():
            print("[stderr]", e[:2000], end="")
        rc = out.channel.recv_exit_status()
        sys.exit(rc)
    finally:
        c.close()


if __name__ == "__main__":
    main()
