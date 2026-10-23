#!/usr/bin/env python3
"""管道 S5 接收处理器 v0.1 · compass 效用验证入口
规格来源: flywheel 函 21150(管道架构 v3)
  监听 mailbox 中 [kind:pipeline-s5-request] → 拉取 S4 产出 → 触发效用验证 → 报告 JSON → 回函 [kind:pipeline-s5-result]
用法:
  轮询模式: python3 s5_receiver.py --once | --watch
产出: runtime/pipeline_s5/<task_id>/report.json (compass 签名效用验证报告)
"""
import argparse, json, os, subprocess, sys, time, urllib.request
from pathlib import Path
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent.parent.parent
S5_DIR = BASE / 'runtime' / 'pipeline_s5'
S5_DIR.mkdir(parents=True, exist_ok=True)
API = 'https://nautilus.social/api/platform/org'
KEYFILE = Path.home() / '.claude/.cache/compass_platform_mailkey.env'

def _key():
    for line in KEYFILE.read_text().splitlines():
        if '=' in line and not line.startswith('#'):
            return line.split('=', 1)[1].strip()
    raise SystemExit('no mailkey')

def fetch_requests():
    """拉 compass 信箱,过滤 kind:pipeline-s5-request 未读"""
    req = urllib.request.Request(f'{API}/mailbox?to=compass&unread=1',
                                 headers={'X-API-Key': _key()})
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    out = []
    for m in d.get('data', []):
        if 'pipeline-s5-request' in (m.get('trace_id') or '') or 'S5' in m.get('title', '')[:8]:
            out.append(m)
    return out

def handle(m):
    task_id = (m.get('trace_id') or f's5-{m["id"]}').replace('pipeline-', 's5-')
    work = S5_DIR / task_id
    work.mkdir(exist_ok=True)
    meta = {'received_at': datetime.now(timezone.utc).isoformat(),
            'mail_id': m['id'], 'trace': m.get('trace_id'), 'title': m['title'],
            'deadline': m.get('deadline'), 'body_head': (m.get('body') or '')[:500]}
    (work / 'request_meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    # S4 产出位置约定:持久路径 cloud:/home/ubuntu/pipeline_s5_persistent/(10/24 迁移)
    # 效用验证执行: ops/pipeline_s5/s5_eval.py(A100 tailnet 100.127.104.67;节点 offline 时置 PENDING-A100)
    gpu_ok = subprocess.run(['ssh', '-o', 'ConnectTimeout=8', 'ubuntu@100.127.104.67', 'echo ok'],
                            capture_output=True, text=True).stdout.strip() == 'ok'
    report = {'task_id': task_id, 'compass_signed': True,
              'stage': 'PENDING-A100-OFFLINE' if not gpu_ok else 'READY-TO-EVAL',
              's4_output_persistent': '/home/ubuntu/pipeline_s5_persistent/sjb_pipeline_v2_output/',
              'eval_criteria_ref': '飞轮判词 v1.7(微调税律:精选80→50少伤,大路货80→0全毁)',
              'pipeline': ['零样本基线评测', 'S4数据微调', '微调后评测', 'Delta pp 计算'],
              'generated_at': datetime.now(timezone.utc).isoformat()}
    (work / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"[{m['id']}] {task_id} → {report['stage']}")
    return report

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--watch', action='store_true')
    a = ap.parse_args()
    if a.once:
        reqs = fetch_requests()
        print(f'{len(reqs)} 个 S5 请求')
        for m in reqs: handle(m)
        return
    if a.watch:
        while True:
            try:
                for m in fetch_requests(): handle(m)
            except Exception as e:
                print(f'watch err: {e}', flush=True)
            time.sleep(600)  # 10min 轮询
    print('用法: --once | --watch')

if __name__ == '__main__':
    main()
