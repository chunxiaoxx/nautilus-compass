"""R63 复现性核验探针自修:查未配对 A2F 窗的 (ep,idx) 坐标集与配对集关系。"""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("223.109.239.30", port=23236, username="root", password="REDACTED_A100_PW", timeout=10)
_, out, _ = c.exec_command(
    "python3 -c \""
    "import json, collections;"
    "win=[json.loads(l) for l in open('/root/vdd3/pipe_art/pusht_infer_A2F/infer_compare.jsonl')];"
    "pair=[json.loads(l) for l in open('/root/vdd3/pipe_art/pusht_infer_pair/paired_compare.jsonl')];"
    "we=collections.Counter(r['ep'] for r in win); pe=collections.Counter(r['ep'] for r in pair);"
    "print('win eps:', dict(sorted(we.items())));"
    "print('pair eps:', dict(sorted(pe.items())));"
    "ws={(r['ep'],r['idx']) for r in win}; ps={(r['ep'],r['idx']) for r in pair};"
    "print('coord overlap:', len(ws & ps), '/40');"
    "wm={(r['ep'],r['idx']): r['ratio'] for r in win};"
    "same=[(k, wm[k]) for k in ws & ps];"
    "pm={(r['ep'],r['idx']): r['ratio_A2F'] for r in pair};"
    "match=[k for k in ws & ps if abs(wm[k]-pm[k])<1e-3];"
    "print('coord match w/ equal ratio:', len(match));"
    "print('sample win rows:', [(r['ep'],r['idx'],r['ratio']) for r in win[:5]])\"", timeout=30)
print(out.read().decode())
c.close()
