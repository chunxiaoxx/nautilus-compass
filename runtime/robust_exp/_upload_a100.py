#!/usr/bin/env python3
"""R279 发车上传件:A100 robust_exp 三件(脚本/语料/adapter)。"""
import glob
import os
import posixpath

import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('223.109.239.30', port=23236, username='root', password='REDACTED_A100_PW', timeout=15)
sftp = c.open_sftp()
for d in ('/root/vdd4/robust_exp', '/root/vdd4/robust_exp/corpus', '/root/vdd4/adapters/best_lora'):
    try:
        sftp.mkdir(d)
    except IOError:
        pass

sftp.put('runtime/robust_exp/precor_replay_bnb.py', '/root/vdd4/robust_exp/precor_replay_bnb.py')
sftp.put('runtime/verdict_corpus/split_test_v1.jsonl', '/root/vdd4/robust_exp/corpus/split_test_v1.jsonl')
sftp.put('runtime/verdict_corpus/split_dev_v1.jsonl', '/root/vdd4/robust_exp/corpus/split_dev_v1.jsonl')
for f in glob.glob('runtime/judge_lora_p2v2/best_lora/*'):
    name = posixpath.basename(f.replace(os.sep, '/'))
    sftp.put(f, '/root/vdd4/adapters/best_lora/' + name)
    print('uploaded adapter:', name)
sftp.close()

_, out, _ = c.exec_command(
    'ls -la /root/vdd4/adapters/best_lora/; ls -la /root/vdd4/robust_exp/ /root/vdd4/robust_exp/corpus/',
    timeout=20)
print(out.read().decode())
c.close()
