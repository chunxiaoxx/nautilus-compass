#!/usr/bin/env python3
"""R280:B/C 发车一体化(上传+nohup 发车,带退避重试)。"""
import glob
import posixpath
import time

import paramiko

HOST, PORT, USER, PW = '223.109.239.30', 23236, 'root', 'REDACTED_A100_PW'


def connect():
    last = None
    for i, wait in enumerate((5, 20, 40, 60, 90), 1):
        try:
            c = paramiko.SSHClient()
            c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            c.connect(HOST, port=PORT, username=USER, password=PW, timeout=20)
            print(f'connect ok (attempt {i})', flush=True)
            return c
        except Exception as e:
            last = e
            print(f'connect fail {i}: {type(e).__name__}, wait {wait}s', flush=True)
            time.sleep(wait)
    raise last


c = connect()
_, out, _ = c.exec_command(
    'mkdir -p /root/vdd4/robust_exp/corpus /root/vdd4/adapters/best_lora && echo MKDIR_OK',
    timeout=20)
print(out.read().decode().strip(), flush=True)

sftp = c.open_sftp()
sftp.put('runtime/robust_exp/precor_replay_bnb.py',
         '/root/vdd4/robust_exp/precor_replay_bnb.py')
print('up: precor_replay_bnb.py', flush=True)
for src, dst in (('runtime/verdict_corpus/split_test_v1.jsonl',
                  '/root/vdd4/robust_exp/corpus/split_test_v1.jsonl'),
                 ('runtime/verdict_corpus/split_dev_v1.jsonl',
                  '/root/vdd4/robust_exp/corpus/split_dev_v1.jsonl')):
    sftp.put(src, dst)
    print('up:', dst, flush=True)
for f in glob.glob('runtime/judge_lora_p2v2/best_lora/*'):
    name = posixpath.basename(f.replace(os.sep, '/'))
    sftp.put(f, '/root/vdd4/adapters/best_lora/' + name)
    print('up adapter:', name, flush=True)
sftp.close()

_, out, _ = c.exec_command(
    'cd /root/vdd4/robust_exp && '
    'setsid nohup python3 precor_replay_bnb.py '
    '> /root/vdd4/robust_exp/run.log 2>&1 < /dev/null & '
    'echo LAUNCHED_PID=$!', timeout=20)
print(out.read().decode().strip(), flush=True)
time.sleep(5)
_, out, _ = c.exec_command('tail -5 /root/vdd4/robust_exp/run.log; '
                           'nvidia-smi --query-gpu=memory.used --format=csv,noheader',
                           timeout=25)
print(out.read().decode(), flush=True)
c.close()
print('LAUNCH DONE', flush=True)
