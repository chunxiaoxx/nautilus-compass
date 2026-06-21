"""compass fleet 记忆胶囊客户端(cross-agent 集体学习)· 2026-06-17 · compass 交付给 V5/platform

把"飞轮 agent learning 写回 + claim 前 recall"降到两个 import 即用的函数,V5 无需自己写 HTTP。
- W1: write_learning(agent_id, task_family, reason)         解完 reward=1.0 后调
- W2: compass_recall_pits(task_family) -> [{item_id,reason}] claim/产出前调·直接喂 V5
       fde_capsule.grounded_retrieval.build_grounding_block(pits)

凭据从共享 secrets env 读(~/.claude/.cache/.fde_api_secrets.env · 非 git):
  COMPASS_FLEET_USER_ID / COMPASS_FLEET_TOKEN (过期用 COMPASS_FLEET_EMAIL/PASSPHRASE re-mint)
所有飞轮 agent 用同一 fleet user_id(cross_agent 在 user 内跨 agent)·agent_id 各异溯源。

实测(compass 6/17):recall_pits + write_learning 端到端 + 喂 V5 真 build_grounding_block → B 从 FAIL→PASS。
"""
from __future__ import annotations
import json, os, re, sys, time, urllib.request, urllib.parse, urllib.error
from typing import List, Dict, Optional

COMPASS_BASE = os.environ.get("COMPASS_BASE", "https://compass.nautilus.social")
_SECRETS = os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")

# 晋升门:只有验证正确(reward ≥ 此)的 learning 才写回 fleet。
# 防退化 keystone:错经验不入库 → 不会被 W2 跨 agent 复利成毒。默认 1.0(旧调用只在 reward=1.0 后调,不传即过门)。
MIN_WRITE_REWARD = 1.0


def _secret(name: str) -> Optional[str]:
    # env 优先(部署可直接注入)·否则读共享 secrets 文件
    if os.environ.get(name):
        return os.environ[name]
    try:
        with open(_SECRETS, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(name + "="):
                    return line.split("=", 1)[1]
    except FileNotFoundError:
        pass
    return None


def _http(method: str, url: str, body=None, token: Optional[str] = None, timeout: int = 30):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def _token() -> str:
    """取 fleet token·过期(401)用 email+passphrase re-mint 并回写 env(进程内)。"""
    tok = _secret("COMPASS_FLEET_TOKEN")
    if tok:
        return tok
    return _relogin()


def _relogin() -> str:
    email, pw = _secret("COMPASS_FLEET_EMAIL"), _secret("COMPASS_FLEET_PASSPHRASE")
    if not (email and pw):
        raise RuntimeError("compass fleet creds 缺失(COMPASS_FLEET_EMAIL/PASSPHRASE)")
    st, r = _http("POST", COMPASS_BASE + "/v1/auth/login", {"email": email, "passphrase": pw})
    if st != 200:
        raise RuntimeError(f"compass fleet login 失败 {st}: {r}")
    os.environ["COMPASS_FLEET_TOKEN"] = r["token"]
    return r["token"]


def _user_id() -> str:
    uid = _secret("COMPASS_FLEET_USER_ID")
    if not uid:
        raise RuntimeError("COMPASS_FLEET_USER_ID 缺失")
    return uid


def compass_recall_pits(task_family: str, top_k: int = 5,
                        min_reward: float = 0.0) -> List[Dict[str, str]]:
    """W2 · 跨 agent recall 同 family 既有 learning → [{item_id, reason}](直接喂 build_grounding_block)。

    防退化(P0·2026-06-22):
    - 屏蔽 revoke tombstone 命中的 learning(单条 revoke·按 obs_id 或 learning 子串匹配)。
    - 丢弃 reward < min_reward 的 learning(缺 reward 字段=兼容旧·视作已验证 1.0)。
    - 按 reward 降序(质量优先)·只喂高质胶囊。
    无命中返回 []。401 自动 re-login 重试一次。失败不抛(返回 [])——飞轮不应因记忆服务抖动停摆。"""
    params = urllib.parse.urlencode({"q": task_family, "cross_agent": "true", "top_k": str(top_k)})
    url = f"{COMPASS_BASE}/v1/recall?{params}"
    try:
        st, r = _http("GET", url, token=_token())
        if st == 401:
            st, r = _http("GET", url, token=_relogin())
        if st != 200:
            return []
        hits = r.get("hits", [])
        # 先收集所有 tombstone 的撤销目标(obs_id 或 learning 子串)。
        revoked_refs = set()
        for h in hits:
            c = h.get("content_or_encrypted") or {}
            if c.get("revoked") and c.get("revokes"):
                revoked_refs.add(str(c["revokes"]))
        scored: List[tuple] = []
        for h in hits:
            c = h.get("content_or_encrypted") or {}
            if c.get("revoked"):            # tombstone 本身不作为 pit
                continue
            learning = c.get("learning")
            if not learning:
                continue
            reward = float(c.get("reward", 1.0))   # 缺失=兼容旧写法
            if reward < min_reward:
                continue
            oid = str(h.get("obs_id") or "")
            if (oid and oid in revoked_refs) or any(ref in learning for ref in revoked_refs):
                continue                    # 被 revoke tombstone 屏蔽
            scored.append((reward, {"item_id": h.get("agent_id", "fleet"), "reason": learning}))
        # 质量优先稳定排序(reward 降序)·返回时剥到 {item_id, reason} 契约。
        scored.sort(key=lambda t: t[0], reverse=True)
        return [pit for _, pit in scored]
    except Exception:
        return []


def revoke_learning(agent_id: str, task_family: str, target: str) -> Optional[str]:
    """单条 revoke · 写一条 tombstone(复用 /v1/observations·无需 serving 改)。
    target = 待废 learning 的 obs_id 或其 learning 文本子串。此后 compass_recall_pits 自动屏蔽命中项。
    返回 tombstone obs_id·失败返回 None(不抛)。"""
    ts = int(time.time() * 1000)
    safe = re.sub(r"[^a-z0-9_]", "_", task_family.lower())[:24]
    obs_id = f"ob_rv_{safe}_{ts}"
    body = {
        "obs_id": obs_id, "user_id": _user_id(), "agent_id": agent_id,
        "agent_type": "fde_solver", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": {"type": "revoke", "concept": task_family},
        "content": {"revoked": True, "revokes": target, "family": task_family},
    }
    try:
        st, r = _http("POST", COMPASS_BASE + "/v1/observations", body, token=_token())
        if st == 401:
            st, r = _http("POST", COMPASS_BASE + "/v1/observations", body, token=_relogin())
        if st != 201:
            print(f"[compass_fleet] revoke_learning 非201 st={st} obs_id={obs_id} resp={r}", file=sys.stderr)
            return None
        return obs_id
    except Exception as e:
        print(f"[compass_fleet] revoke_learning 异常 obs_id={obs_id}: {e}", file=sys.stderr)
        return None


def write_learning(agent_id: str, task_family: str, reason: str,
                   task_uid: Optional[str] = None, reward: float = 1.0,
                   bucket: Optional[str] = None, score: Optional[float] = None,
                   source: Optional[str] = None) -> Optional[str]:
    """W1 · 把一行可复用 learning 写回 compass。返回 obs_id·失败返回 None(不抛)。

    防退化(P0·2026-06-22):
    - 晋升门:reward < MIN_WRITE_REWARD → 拒写(错经验不入库·不被 W2 复利成毒)。默认 1.0 兼容旧调用。
    - verdict 元数据:reward/bucket/score/source 落 content 作质量标签·供 W2 质量过滤/排序。
    """
    if reward < MIN_WRITE_REWARD:
        print(f"[compass_fleet] write_learning 拒写(reward={reward} < 晋升门 {MIN_WRITE_REWARD}) "
              f"family={task_family}", file=sys.stderr)
        return None
    ts = int(time.time() * 1000)
    # sanitize: 端点只收 obs_id 字符集 [a-z0-9_]·冒号/斜杠/空格等会被拒(非201)致静默丢写。
    safe = re.sub(r"[^a-z0-9_]", "_", task_family.lower())[:24]
    obs_id = f"ob_fw_{safe}_{ts}"
    body = {
        "obs_id": obs_id, "user_id": _user_id(), "agent_id": agent_id,
        "agent_type": "fde_solver", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": {"type": "learning", "concept": task_family},
        "content": {"learning": reason[:2000], "family": task_family, "task_uid": task_uid,
                    "reward": reward, "bucket": bucket, "score": score, "source": source,
                    "revoked": False},
    }
    try:
        st, r = _http("POST", COMPASS_BASE + "/v1/observations", body, token=_token())
        if st == 401:
            st, r = _http("POST", COMPASS_BASE + "/v1/observations", body, token=_relogin())
        if st != 201:
            # 不再静默吞:留一行便于发现"半生效"(V5 6/19 报 W1 静默丢写根因)。
            print(f"[compass_fleet] write_learning 非201 st={st} obs_id={obs_id} resp={r}", file=sys.stderr)
            return None
        return obs_id
    except Exception as e:
        print(f"[compass_fleet] write_learning 异常 obs_id={obs_id}: {e}", file=sys.stderr)
        return None


if __name__ == "__main__":
    # 自测:write → recall round-trip(probe·跑完请手动清 ob_fw_selftest_*)
    fam = f"selftest_{int(time.time())}"
    oid = write_learning("ag_selftest", fam, f"SELFTEST probe learning for {fam}")
    print("write_learning obs_id =", oid)
    pits = compass_recall_pits(fam)
    print("compass_recall_pits  =", pits)
    print("round-trip OK =", bool(oid and any(fam in p["reason"] for p in pits)))
