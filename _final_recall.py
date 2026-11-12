import socket, json, time, subprocess, glob, os
# find daemon pid by listing processes matching daemon.py
r = subprocess.run(['ps','aux'],capture_output=True,text=True)
pid = None
for line in r.stdout.splitlines():
    if 'nautilus-compass/daemon.py' in line or 'plugins/nautilus-compass/daemon.py' in line:
        parts = line.split()
        if parts and parts[1].isdigit():
            pid = parts[1]
            break
print('daemon pid:', pid)
tok_file = None
if pid:
    env = open(f'/proc/{pid}/environ','rb').read().decode(errors='replace').split('\x00')
    for e in env:
        if 'COMPASS_DAEMON_TOKEN_FILE' in e:
            tok_file = e.split('=',1)[1]
if not tok_file:
    cands = glob.glob('/home/ubuntu/**/compass_daemon_token', recursive=True)
    tok_file = cands[0] if cands else None
print('tok_file:', tok_file)
if not tok_file:
    print('ABORT: no token file'); exit(1)
tok = open(tok_file).read().strip()
s = socket.create_connection(('127.0.0.1', 9876), timeout=15)
req = {'action':'recall','query':'ORG-FUEL 语料 RAG 迁移 Mac mini','k':3,
       'token':tok,'scope':'project','project':'orgfuel-corpus'}
s.sendall((json.dumps(req)+'\n').encode())
s.settimeout(180)
d=b''
while True:
    c2=s.recv(65536)
    if not c2: break
    d+=c2
    if b'\n' in d: break
s.close()
j=json.loads(d.decode())
hits=j.get('hits') or []
print('FINAL cloud recall:', j.get('ok'), 'hits=', len(hits))
for h in hits[:3]:
    print('  ', round(h.get('score',0),3), (h.get('path') or '')[-48:])
