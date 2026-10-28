#!/usr/bin/env python3
"""上传 PDF 到飞书并私发给用户会话(一次性,文件消息)。

凭据:复用 feishu_push 的 _load_env 配方(借 v5 域 scorer app 凭据);
目标会话 oc_e3db8f7cf138a31c02025ccceef2f60b(用户私聊)。
"""
import json
import mimetypes
import os
import sys
import urllib.request
import uuid

sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")
from ops.feishu_push import _load_env  # noqa: E402

_load_env()
AID = os.environ["FEISHU_APP_ID"]
SEC = os.environ["FEISHU_APP_SECRET"]
CHAT = sys.argv[2] if len(sys.argv) > 2 else "oc_e3db8f7cf138a31c02025ccceef2f60b"
PDF = sys.argv[1] if len(sys.argv) > 1 else "/tmp/nautilus_onepager_li_ning.pdf"

BASE = "https://open.feishu.cn/open-apis"


def _post(url, data, headers):
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


tok = _post(f"{BASE}/auth/v3/tenant_access_token/internal",
            json.dumps({"app_id": AID, "app_secret": SEC}).encode(),
            {"Content-Type": "application/json"})["tenant_access_token"]
print("token ok")

# multipart 上传文件
boundary = uuid.uuid4().hex
fname = os.path.basename(PDF)
with open(PDF, "rb") as f:
    payload = f.read()
parts = []
for k, v in [("file_type", "pdf"), ("file_name", fname), ("duration", "0")]:
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
parts.append((f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
              f"filename=\"{fname}\"\r\n"
              f"Content-Type: application/pdf\r\n\r\n").encode())
parts.append(payload + f"\r\n--{boundary}--\r\n".encode())
body = b"".join(parts)
up = _post(f"{BASE}/im/v1/files", body,
           {"Authorization": f"Bearer {tok}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"})
print("upload:", up.get("code"), up.get("msg"))
file_key = up["data"]["file_key"]

msg = _post(f"{BASE}/im/v1/messages?receive_id_type=chat_id",
            json.dumps({"receive_id": CHAT, "msg_type": "file",
                        "content": json.dumps({"file_key": file_key})}).encode(),
            {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
print("send:", msg.get("code"), msg.get("msg"))
