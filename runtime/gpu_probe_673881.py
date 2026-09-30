# -*- coding: utf-8 -*-
"""GPU 实例 673881(js2:15124)环境探针:GPU/torch/数据/磁盘 一次性实测。"""
import paramiko, sys

CMDS = [
    ("gpu", "nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader"),
    ("torch", "python3 -c \"import torch; print('torch', torch.__version__, 'cuda', torch.cuda.is_available())\" 2>&1 | tail -1"),
    ("pip_pkgs", "python3 -m pip list 2>/dev/null | grep -i -E '^(torch|transformers|peft|accelerate|bitsandbytes|trl|datasets)' | head -8"),
    ("pip_still_running", "ps aux | grep -E 'pip|get-pip' | grep -v grep | head -3"),
    ("splits", "ls -la /root/nautilus-compass/runtime/verdict_corpus/ 2>/dev/null || ls -la /root/*/runtime/verdict_corpus/ 2>/dev/null || find /root -maxdepth 4 -name 'split_*.jsonl' 2>/dev/null | head -5"),
    ("train_script", "find /root -maxdepth 4 -name 'train_judge_lora.py' 2>/dev/null | head -2"),
    ("disk", "df -h /root | tail -1"),
    ("hf_cache", "ls ~/.cache/huggingface/hub 2>/dev/null | head -5"),
]

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect("js2.blockelite.cn", port=15124, username="root", password="Coh9ech3", timeout=20)
    for name, cmd in CMDS:
        _, out, err = c.exec_command(cmd, timeout=60)
        text = (out.read().decode("utf-8", "replace") + err.read().decode("utf-8", "replace")).strip()
        print(f"== {name}\n{text}\n")
    c.close()

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
