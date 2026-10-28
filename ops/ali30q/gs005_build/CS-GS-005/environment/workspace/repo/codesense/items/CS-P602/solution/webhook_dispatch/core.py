"""webhook_dispatch.core — webhook 分发(金标实现)。"""
from __future__ import annotations

import hashlib
import hmac
import json
import urllib.parse


def dispatch(cfg: dict, event: dict, http_post=None, delivered=None) -> dict:
    """分发事件到 webhook(§1-§4,以 §2 安全口径为准,§5 备注不采纳)。"""
    delivered = delivered if delivered is not None else set()
    http_post = http_post or _default_post
    url = cfg["url"]
    host = urllib.parse.urlparse(url).hostname or ""

    # §2 端点白名单
    if host not in cfg.get("allowed_hosts", []):
        return {"status": "rejected", "reason": "host_not_allowed"}

    # §2 幂等去重
    if event["event_id"] in delivered:
        return {"status": "delivered", "deduplicated": True}

    body = json.dumps(event, ensure_ascii=False).encode()
    sig = hmac.new(cfg["secret"].encode(), body, hashlib.sha256).hexdigest()
    headers = {"Content-Type": "application/json", "X-Signature": sig}

    attempts = 0
    last = None
    for _ in range(int(cfg.get("max_retries", 1))):
        attempts += 1
        code = http_post(url, headers, body)
        last = code
        if 200 <= code < 300:
            delivered.add(event["event_id"])  # §3 成功记入已投递集合
            return {"status": "delivered", "attempts": attempts}
    return {"status": "failed", "attempts": attempts, "last_code": last}


def _default_post(url, headers, body):
    import urllib.request
    req = urllib.request.Request(url, data=body,
                                 headers={**headers, **{k: v for k, v in urllib.request.Request(url).header_items()}})
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0
