"""link_machines.py · Windows 侧打通 新机→旧盘机 的 key auth(重租后必跑,幂等)
用法: python vtf/link_machines.py <old_host> <old_port> <old_password>
新机连接参数读 gpu_ssh.py 的 env/默认值。
"""
import sys

import paramiko

sys.path.insert(0, "vtf")
import gpu_ssh  # noqa: E402


def main():
    old_host, old_port, old_pw = sys.argv[1], int(sys.argv[2]), sys.argv[3]

    # 1. 新机:确保有 keypair,取 pubkey
    new = gpu_ssh.client()
    _, o, _ = new.exec_command(
        "[ -f /root/.ssh/id_ed25519.pub ] || ssh-keygen -t ed25519 -N '' -f /root/.ssh/id_ed25519 -q; "
        "cat /root/.ssh/id_ed25519.pub", timeout=30)
    pub = o.read().decode().strip()
    assert pub.startswith("ssh-ed25519"), f"pubkey 读取失败: {pub[:100]}"

    # 2. 旧机:密码登录,装 pubkey
    old = paramiko.SSHClient()
    old.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    old.connect(old_host, old_port, "root", old_pw, timeout=20)
    cmd = (
        "mkdir -p /root/.ssh && chmod 700 /root/.ssh && "
        f"grep -qF '{pub}' /root/.ssh/authorized_keys 2>/dev/null || echo '{pub}' >> /root/.ssh/authorized_keys; "
        "chmod 600 /root/.ssh/authorized_keys && echo KEY_INSTALLED"
    )
    _, o, e = old.exec_command(cmd, timeout=30)
    print("old:", o.read().decode().strip(), e.read().decode()[:200])
    old.close()

    # 3. 新机验证免密登旧机
    _, o, e = new.exec_command(
        f"ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=10 "
        f"-p {old_port} root@{old_host} 'echo KEY_AUTH_OK; hostname'", timeout=30)
    print("verify:", o.read().decode().strip(), e.read().decode()[:200])
    new.close()


if __name__ == "__main__":
    main()
