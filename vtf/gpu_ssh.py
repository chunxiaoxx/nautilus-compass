"""GPU 机非交互 SSH 执行器(paramiko)· 用法: python3 gpu_ssh.py "command" [upload local remote]
重租换端口/密码时:设 env GPU_SSH_HOST/GPU_SSH_PORT/GPU_SSH_PW 即可,不用改文件。"""
import os
import sys

import paramiko

HOST = os.environ.get("GPU_SSH_HOST", "js1.blockelite.cn")
PORT = int(os.environ.get("GPU_SSH_PORT", "11224"))
USER = os.environ.get("GPU_SSH_USER", "root")
PW = os.environ.get("GPU_SSH_PW", "pei9teiL")
# 2026-09-04 · 实例 654686(lyg0002xh c4 · js1:11224)· cheap-tier 跑分现役机
# 密码轮换从 get_connection_info 的 ssh_url query 取(base64 解码)——SSH 认证失败
# 先查实例 status(Status=1=活着)再重取凭证,别急着判实例没了(9/4 教训)
# 2026-08-29 · 实例 651799/651448(js3:10536 · 旧密码 zoh3Eich)已退役


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
        if sys.argv[1] == "writefile":
            # blockelite SFTP stat/open 怪癖绕法:exec 通道 base64 流写文件
            import base64
            from pathlib import Path

            data = Path(sys.argv[2]).read_bytes()
            b64 = base64.b64encode(data).decode()
            remote = sys.argv[3]
            _, out, err = c.exec_command(
                f"base64 -d > {remote} && echo WROTE $(wc -c < {remote})"
            )
            out.channel.sendall(b64.encode())
            out.channel.shutdown_write()
            o = out.read().decode("utf-8", "replace")
            e = err.read().decode("utf-8", "replace")
            print(o, end="")
            if e.strip():
                print("[stderr]", e[:1000], end="")
            sys.exit(0 if "WROTE" in o else 1)
        if sys.argv[1] == "readfile":
            # SFTP download 怪癖的 exec 通道绕法:远端 base64 输出流,本地解码
            import base64

            _, out, err = c.exec_command(f"base64 {sys.argv[2]} && echo B64_DONE")
            b64 = out.read().decode("ascii", "replace")
            e = err.read().decode("utf-8", "replace")
            ok = "B64_DONE" in b64
            body = b64.replace("B64_DONE", "") if ok else ""
            data = base64.b64decode(body) if ok else b""
            if data:
                from pathlib import Path

                Path(sys.argv[3]).write_bytes(data)
            print(f"READ {len(data)} bytes -> {sys.argv[3]}")
            if e.strip():
                print("[stderr]", e[:1000], end="")
            sys.exit(0 if ok else 1)
        if sys.argv[1] == "download":
            sftp = c.open_sftp()
            sftp.get(sys.argv[2], sys.argv[3])
            print(f"DOWNLOADED {sys.argv[2]} -> {sys.argv[3]}")
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
