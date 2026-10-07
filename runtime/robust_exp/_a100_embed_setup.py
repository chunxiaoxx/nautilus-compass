#!/usr/bin/env python3
"""A100 嵌入服务部署脚本(R301 续):杀旧下载/pattern 重下/装 fastapi/部署服务。"""
import time

import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('223.109.239.30', port=23236, username='root', password='REDACTED_A100_PW', timeout=20)

DL_SCRIPT = '''from modelscope import snapshot_download
p = snapshot_download('BAAI/bge-m3', cache_dir='/root/vdd4/modelscope/models',
    allow_patterns=['*.json', '*.txt', 'pytorch_model.bin', '*.safetensors',
                    'tokenizer*', 'sentencepiece*', 'configuration*', 'cofig*'])
print('DONE', p)
'''
sftp = c.open_sftp()
with sftp.open('/root/vdd4/dl_bge.py', 'w') as f:
    f.write(DL_SCRIPT)

_, out, _ = c.exec_command(
    "pkill -f 'snapshot_download' 2>/dev/null; pkill -f 'dl_bge' 2>/dev/null; sleep 1; "
    'rm -rf /root/vdd4/modelscope/models/BAAI--bge-m3; '
    'cd /root/vdd4 && setsid nohup python3 dl_bge.py > bge_download.log 2>&1 < /dev/null & '
    'sleep 3; tail -1 bge_download.log; echo DL_RESTARTED', timeout=25)
print(out.read().decode().strip(), flush=True)

_, out, _ = c.exec_command(
    'pip install -q --break-system-packages fastapi uvicorn 2>&1 | tail -1; '
    "python3 -c 'import fastapi; print(\"fastapi\", fastapi.__version__)'", timeout=120)
print(out.read().decode().strip()[-120:], flush=True)
sftp.close()
c.close()
print('SETUP PHASE DONE')
