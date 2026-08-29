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
