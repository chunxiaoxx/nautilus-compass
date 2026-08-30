"""GPU 机非交互 SSH 执行器(paramiko)· 用法: python3 gpu_ssh.py "command" [upload local remote]
重租换端口/密码时:设 env GPU_SSH_HOST/GPU_SSH_PORT/GPU_SSH_PW 即可,不用改文件。"""
import os
import sys

import paramiko

HOST = os.environ.get("GPU_SSH_HOST", "js3.blockelite.cn")
PORT = int(os.environ.get("GPU_SSH_PORT", "10536"))
USER = os.environ.get("GPU_SSH_USER", "root")
PW = os.environ.get("GPU_SSH_PW", "zoh3Eich")
# 2026-08-29 · 实例 651799(651448 重租恢复·同容器 c1·镜像 v2608291059 + 100G 数据盘 /root/data 已挂)
# 备用 IP:移动 223.109.239.32 / 电信 180.127.11.166(同端口)· due 08-30 02:42
# 2026-08-29 · 新实例 651448(自定义镜像 v2608291059 开机+外挂 100G 数据盘 /root/data)
# 镜像验证通过:vllm 0.8.5/Qwen 断点/reranker 干净版/LME-V2 数据/e2e 全套秒级就位
# 备用:电信 180.127.11.166:10516 · Qwen 模型在 /root/data/models/qwen35-9b(软链)


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
