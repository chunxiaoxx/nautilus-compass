"""Strong Feishu identity, signed sessions, and opaque one-time references."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Mapping
from urllib.parse import urlencode

import requests


class SignedTokenError(ValueError):
    """Raised when a signed token is malformed, expired, or has the wrong use."""


class OpaqueReferenceError(ValueError):
    """Raised when an opaque reference is missing, expired, or already consumed."""


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class SignedTokenCodec:
    """Small HMAC token codec used for OAuth state and HttpOnly sessions."""

    def __init__(self, secret: bytes, *, clock: Any = time.time) -> None:
        if len(secret) < 32:
            raise ValueError("FDE Phase 3 session secret must be at least 32 bytes")
        self._secret = secret
        self._clock = clock

    def encode(self, kind: str, claims: Mapping[str, Any], ttl_seconds: int) -> str:
        now = int(self._clock())
        payload = dict(claims)
        payload.update({"kind": kind, "iat": now, "exp": now + ttl_seconds})
        body = _b64encode(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        signature = _b64encode(hmac.new(self._secret, body.encode("ascii"), hashlib.sha256).digest())
        return f"{body}.{signature}"

    def decode(self, token: str, expected_kind: str) -> dict[str, Any]:
        try:
            body, supplied_signature = token.split(".", 1)
            expected_signature = _b64encode(
                hmac.new(self._secret, body.encode("ascii"), hashlib.sha256).digest()
            )
            if not hmac.compare_digest(supplied_signature, expected_signature):
                raise SignedTokenError("invalid token signature")
            payload = json.loads(_b64decode(body).decode("utf-8"))
        except SignedTokenError:
            raise
        except Exception as exc:
            raise SignedTokenError("malformed token") from exc
        now = int(self._clock())
        if payload.get("kind") != expected_kind:
            raise SignedTokenError("wrong token purpose")
        if not isinstance(payload.get("exp"), int) or payload["exp"] < now:
            raise SignedTokenError("expired token")
        if not isinstance(payload.get("iat"), int) or payload["iat"] > now + 60:
            raise SignedTokenError("invalid token issue time")
        return payload


class RedisOpaqueStore:
    """Redis-backed one-time references; browser-visible values reveal no record IDs."""

    def __init__(self, redis_client: Any, *, namespace: str = "fde_phase3_workbench") -> None:
        self._redis = redis_client
        self._namespace = namespace

    def _key(self, purpose: str, token: str) -> str:
        return f"{self._namespace}:{purpose}:{token}"

    def issue(self, purpose: str, payload: Mapping[str, Any], ttl_seconds: int) -> str:
        encoded = json.dumps(dict(payload), ensure_ascii=False, separators=(",", ":"))
        for _ in range(8):
            token = secrets.token_urlsafe(24)
            if self._redis.set(self._key(purpose, token), encoded, ex=ttl_seconds, nx=True):
                return token
        raise RuntimeError("unable to allocate opaque reference")

    def peek(self, purpose: str, token: str) -> dict[str, Any]:
        raw = self._redis.get(self._key(purpose, token))
        if raw is None:
            raise OpaqueReferenceError("reference unavailable")
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def consume(self, purpose: str, token: str) -> dict[str, Any]:
        raw = self._redis.getdel(self._key(purpose, token))
        if raw is None:
            raise OpaqueReferenceError("reference unavailable")
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        return json.loads(raw)

    def delete(self, purpose: str, token: str) -> None:
        self._redis.delete(self._key(purpose, token))

    def replace(self, purpose: str, token: str, payload: Mapping[str, Any], ttl_seconds: int) -> None:
        encoded = json.dumps(dict(payload), ensure_ascii=False, separators=(",", ":"))
        self._redis.set(self._key(purpose, token), encoded, ex=ttl_seconds)

    @contextmanager
    def lock(self, scope: str, *, timeout_seconds: int = 30) -> Iterator[None]:
        lock = self._redis.lock(
            f"{self._namespace}:lock:{scope}",
            timeout=timeout_seconds,
            blocking_timeout=5,
        )
        if not lock.acquire(blocking=True):
            raise RuntimeError("another operation is already processing")
        try:
            yield
        finally:
            try:
                lock.release()
            except Exception:
                pass


@dataclass(frozen=True)
class FeishuIdentity:
    open_id: str
    union_id: str
    name: str


class FeishuOAuthClient:
    AUTHORIZE_URL = "https://accounts.feishu.cn/open-apis/authen/v1/authorize"
    TOKEN_URL = "https://open.feishu.cn/open-apis/authen/v2/oauth/token"
    USER_INFO_URL = "https://open.feishu.cn/open-apis/authen/v1/user_info"

    def __init__(
        self,
        *,
        app_id: str,
        app_secret: str,
        redirect_uri: str,
        scope: str = "",
        http: requests.Session | None = None,
        timeout_seconds: int = 20,
    ) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._redirect_uri = redirect_uri
        self._scope = scope.strip()
        self._http = http or requests.Session()
        self._timeout = timeout_seconds

    def authorization_url(self, state: str) -> str:
        params = {
            "client_id": self._app_id,
            "redirect_uri": self._redirect_uri,
            "state": state,
        }
        if self._scope:
            params["scope"] = self._scope
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> FeishuIdentity:
        response = self._http.post(
            self.TOKEN_URL,
            json={
                "grant_type": "authorization_code",
                "client_id": self._app_id,
                "client_secret": self._app_secret,
                "code": code,
                "redirect_uri": self._redirect_uri,
            },
            timeout=self._timeout,
        )
        token_payload = self._json_or_error(response, "Feishu OAuth token exchange")
        token_data = token_payload.get("data") or token_payload
        access_token = token_data.get("access_token")
        if not access_token:
            raise RuntimeError("Feishu OAuth response did not include access_token")
        user_response = self._http.get(
            self.USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=self._timeout,
        )
        user_payload = self._json_or_error(user_response, "Feishu user identity lookup")
        user = user_payload.get("data") or user_payload
        open_id = str(user.get("open_id") or "").strip()
        if not open_id:
            raise RuntimeError("Feishu identity response did not include open_id")
        return FeishuIdentity(
            open_id=open_id,
            union_id=str(user.get("union_id") or "").strip(),
            name=str(user.get("name") or "飞书用户").strip(),
        )

    @staticmethod
    def _json_or_error(response: requests.Response, operation: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except Exception as exc:
            raise RuntimeError(f"{operation} returned non-JSON response") from exc
        if response.status_code != 200 or payload.get("code", 0) != 0:
            raise RuntimeError(
                f"{operation} failed: http={response.status_code} "
                f"code={payload.get('code')} msg={payload.get('msg')}"
            )
        return payload
