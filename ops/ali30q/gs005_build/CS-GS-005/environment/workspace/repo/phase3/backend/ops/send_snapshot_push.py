# -*- coding: utf-8 -*-
"""快照推飞书(云端侧执行器):先跑 digest_human 出人话版,发 /tmp/snap_human.txt;
digest 失败兜底发机器版 /tmp/snap.txt(9/4 用户反馈:机器版不是给人看的)。
凭据=云 .env+v5 .env.systemd。"""
import json
import os
import subprocess
import urllib.request as u

for _p in (".env", "/home/ubuntu/nautilus-v5/.env.systemd"):
    for _l in open(_p, encoding="utf-8"):
        if "=" in _l and not _l.startswith("#"):
            k, v = _l.strip().split("=", 1)
            os.environ.setdefault(k, v.strip('"'))

# 内容线读数(10/4 培育期接线):失败不阻断 digest
try:
    subprocess.run(["python3", "ops/devto_snapshot.py"], timeout=90)
except Exception as e:  # noqa: BLE001
    print("devto snapshot skipped:", str(e)[:80])

# 人话日报(LLM 归纳,失败自动落模板版;整体失败则下面直接发机器版)
try:
    subprocess.run(["python3", "ops/digest_human.py"], timeout=120, check=True)
except Exception as e:  # noqa: BLE001
    print("digest skipped:", str(e)[:80])

B = "https://open.feishu.cn/open-apis"
t = u.Request(B + "/auth/v3/tenant_access_token/internal",
              data=json.dumps({"app_id": os.environ["FEISHU_APP_ID"],
                               "app_secret": os.environ["FEISHU_APP_SECRET"]}).encode(),
              headers={"Content-Type": "application/json"}, method="POST")
tok = json.loads(u.urlopen(t, timeout=30).read())["tenant_access_token"]
_content = "/tmp/snap_human.txt" if os.path.exists("/tmp/snap_human.txt") else "/tmp/snap.txt"
m = u.Request(B + "/im/v1/messages?receive_id_type=chat_id",
              data=json.dumps({"receive_id": "oc_c9fbb71be60e8d64fb0c854078b05847",
                               "msg_type": "text",
                               "content": json.dumps(
                                   {"text": open(_content, encoding="utf-8").read()})}).encode(),
              headers={"Authorization": "Bearer " + tok,
                       "Content-Type": "application/json"}, method="POST")
print("push code:", json.loads(u.urlopen(m, timeout=30).read()).get("code"))
