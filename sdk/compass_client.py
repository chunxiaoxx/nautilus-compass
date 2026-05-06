"""compass v0.9 · Multi-agent ingest SDK.

让任何 agent (OpenClaw / Hermes / Cursor / Codex / 自家产品) 把 obs 写入
compass platform · 实现"用户跨 agent 交互历史融合".

设计原则:
  1. user 是一等公民 (不是 tenant)
  2. agent_id 标识来源 (claude-code / openclaw / hermes / cursor / codex / custom)
  3. 端到端加密 ready (encrypt_payload=True 时本地 AES-GCM 加密)
  4. 离线缓冲 (.cache/pending_obs.jsonl) · 网络恢复时回放
  5. 极简依赖 (urllib + json · 不引入 requests)

Usage (3 行接入):

    from compass_client import CompassClient
    client = CompassClient(user_id="u_chunx", agent_id="ag_openclaw_main")
    client.ingest_obs(name="...", description="...", body="...", drift="green")

API endpoints (compass.nautilus.social):
  POST /v1/observations    Bearer JWT · 写单条 obs
  POST /v1/observations/batch  · 批量
  GET  /v1/recall          · 读 (跨 agent 默认)
  GET  /v1/profile         · 用户画像 (server-side 聚合)
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DEFAULT_BASE = "https://compass.nautilus.social"
TIMEOUT = 10
PENDING_DIR = Path.home() / ".compass" / "pending"

KNOWN_AGENT_TYPES = {
    "claude-code", "openclaw", "hermes", "cursor", "codex",
    "zenmind", "nautilus", "caishen", "custom",
}
DRIFT_VALUES = {"green", "yellow", "red"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class CompassClient:
    def __init__(
        self,
        user_id: str,
        agent_id: str,
        agent_type: str = "custom",
        token: Optional[str] = None,
        base_url: str = DEFAULT_BASE,
        encrypt_payload: bool = False,
        offline_buffer: bool = True,
        verbose: bool = False,
    ):
        if not user_id or not user_id.startswith("u_"):
            raise ValueError("user_id must start with 'u_' (e.g. u_chunx)")
        if not agent_id or not agent_id.startswith("ag_"):
            raise ValueError("agent_id must start with 'ag_' (e.g. ag_openclaw_main)")
        if agent_type not in KNOWN_AGENT_TYPES:
            sys.stderr.write(f"[compass] unknown agent_type={agent_type} · using 'custom'\n")
            agent_type = "custom"

        self.user_id = user_id
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.base_url = base_url.rstrip("/")
        self.token = token or os.environ.get("COMPASS_TOKEN")
        self.encrypt = encrypt_payload
        self.offline_buffer = offline_buffer
        self.verbose = verbose

        # v1.0 E2EE · master_key passed in or derived
        self._master_key: Optional[bytes] = None
        if self.encrypt:
            try:
                from compass_crypto import encrypt_obs as _enc, decrypt_obs as _dec
                self._encrypt_obs = _enc
                self._decrypt_obs = _dec
                # master_key must be set via .set_master_key() before encryption
                # (typically derived after auth.login from passphrase + encryption_salt)
            except ImportError:
                sys.stderr.write("[compass] encrypt_payload=True but compass_crypto not installed · falling back to plaintext\n")
                self.encrypt = False

    def set_master_key(self, master_key: bytes) -> None:
        """Set the E2EE master key · derive from passphrase via compass_crypto.derive_master_key().

        Call after login · before any encrypted ingest_obs.
        """
        if len(master_key) != 32:
            raise ValueError("master_key must be 32 bytes (AES-256)")
        self._master_key = master_key

    # ---- Core API ----

    def ingest_obs(
        self,
        name: str,
        description: str = "",
        body: str = "",
        type_: str = "discovery",
        concept: str = "pattern",
        drift: str = "green",
        drift_signals: Optional[list[str]] = None,
        extra_meta: Optional[dict] = None,
    ) -> dict:
        """Write one observation · returns {ok, obs_id, ...} or buffers if offline."""
        if drift not in DRIFT_VALUES:
            drift = "green"
        payload = {
            "obs_id": _gen_id("ob"),
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "ts": _now_iso(),
            "meta": {  # 明文 · server 索引
                "type": type_,
                "concept": concept,
                "drift": drift,
                "drift_signals": drift_signals or [],
            },
            "content": {  # E2EE 时加密这块
                "name": name,
                "description": description,
                "body": body,
            },
        }
        if extra_meta:
            payload["meta"].update(extra_meta)

        if self.encrypt and self._master_key is not None:
            payload["encrypted_body"] = self._encrypt_obs(
                self._master_key, payload["obs_id"], payload["content"]
            )
            payload["encryption_version"] = "v1"
            del payload["content"]
        elif self.encrypt and self._master_key is None:
            sys.stderr.write("[compass] encrypt_payload=True but master_key not set · call client.set_master_key() first · falling back to plaintext for this obs\n")

        return self._post("/v1/observations", payload)

    def ingest_batch(self, observations: list[dict]) -> dict:
        """Batch write · same shape as ingest_obs but in list."""
        return self._post("/v1/observations/batch", {"observations": observations})

    def recall(self, query: str, top_k: int = 5, cross_agent: bool = True,
               agent_id: Optional[str] = None, drift: Optional[str] = None) -> dict:
        params = {"q": query, "top_k": top_k, "cross_agent": str(cross_agent).lower()}
        if agent_id:
            params["agent_id"] = agent_id
        if drift:
            params["drift"] = drift
        return self._get("/v1/recall", params)

    def profile(self) -> dict:
        return self._get("/v1/profile", {})

    # ---- Transport ----

    def _post(self, path: str, body: dict) -> dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST", headers=self._headers(json_body=True))
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            if self.verbose:
                sys.stderr.write(f"[compass] POST {path} fail: {e}\n")
            if self.offline_buffer:
                return self._buffer(path, body, error=str(e))
            return {"ok": False, "error": str(e)}

    def _get(self, path: str, params: dict) -> dict:
        from urllib.parse import urlencode
        url = f"{self.base_url}{path}?{urlencode(params)}"
        req = urllib.request.Request(url, method="GET", headers=self._headers(json_body=False))
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _headers(self, json_body: bool) -> dict:
        h = {
            "User-Agent": f"compass-sdk/0.9 ({self.agent_type})",
            "X-User-ID": self.user_id,
            "X-Agent-ID": self.agent_id,
            "X-Agent-Type": self.agent_type,
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if json_body:
            h["Content-Type"] = "application/json"
        return h

    # ---- Offline buffer (resilient) ----

    def _buffer(self, path: str, body: dict, error: str) -> dict:
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        fp = PENDING_DIR / f"{self.user_id}_{int(time.time())}.jsonl"
        with fp.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"path": path, "body": body, "error": error,
                                "ts": _now_iso()}, ensure_ascii=False) + "\n")
        return {"ok": False, "buffered": True, "buffer_file": str(fp), "error": error}

    def replay_buffer(self) -> dict:
        """Try sending buffered obs · returns counts."""
        if not PENDING_DIR.exists():
            return {"sent": 0, "remain": 0}
        sent = 0; remain = 0
        for fp in list(PENDING_DIR.glob(f"{self.user_id}_*.jsonl")):
            keep_lines: list[str] = []
            for line in fp.read_text(encoding="utf-8").splitlines():
                try:
                    rec = json.loads(line)
                    r = self._post(rec["path"], rec["body"])
                    if r.get("ok") or r.get("obs_id"):
                        sent += 1
                    else:
                        keep_lines.append(line); remain += 1
                except Exception:
                    keep_lines.append(line); remain += 1
            if keep_lines:
                fp.write_text("\n".join(keep_lines), encoding="utf-8")
            else:
                fp.unlink()
        return {"sent": sent, "remain": remain}


# ---- Convenience helpers ----

def from_env(agent_type: str = "custom") -> CompassClient:
    """Quick client from env vars: COMPASS_USER_ID · COMPASS_AGENT_ID · COMPASS_TOKEN."""
    user_id = os.environ.get("COMPASS_USER_ID") or "u_anonymous"
    agent_id = os.environ.get("COMPASS_AGENT_ID") or _gen_id("ag")
    return CompassClient(user_id=user_id, agent_id=agent_id, agent_type=agent_type)


if __name__ == "__main__":
    # 自测
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--user-id", default="u_test")
    p.add_argument("--agent-id", default="ag_test_cli")
    p.add_argument("--agent-type", default="custom")
    p.add_argument("--name", default="SDK self-test")
    p.add_argument("--base-url", default=DEFAULT_BASE)
    args = p.parse_args()
    c = CompassClient(user_id=args.user_id, agent_id=args.agent_id,
                      agent_type=args.agent_type, base_url=args.base_url, verbose=True)
    r = c.ingest_obs(
        name=args.name,
        description="SDK CLI smoke test · 验证 client 能调通 compass platform",
        body="自测一条 · 应该 buffer 因为 /v1/observations 还没在 server 实现",
        drift="green",
    )
    print(json.dumps(r, ensure_ascii=False, indent=2))
