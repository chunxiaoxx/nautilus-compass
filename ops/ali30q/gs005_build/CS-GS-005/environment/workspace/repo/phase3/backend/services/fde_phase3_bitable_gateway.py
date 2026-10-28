"""Narrow production gateway for the authoritative Phase 3 Feishu Base."""

from __future__ import annotations

import json
import threading
import time
from pathlib import PurePath
from typing import Any, Iterable, Mapping

import requests


class FeishuGatewayError(RuntimeError):
    pass


class FeishuPhase3Gateway:
    API_ROOT = "https://open.feishu.cn/open-apis"

    def __init__(
        self,
        *,
        app_id: str,
        app_secret: str,
        app_token: str,
        http: requests.Session | None = None,
        timeout_seconds: int = 25,
    ) -> None:
        self._app_id = app_id
        self._app_secret = app_secret
        self._app_token = app_token
        self._http = http or requests.Session()
        self._timeout = timeout_seconds
        self._token = ""
        self._token_expiry = 0.0
        self._token_lock = threading.Lock()
        self._table_ids: dict[str, str] | None = None

    @property
    def app_token(self) -> str:
        return self._app_token

    def table_id(self, table_name: str) -> str:
        if self._table_ids is None:
            self._table_ids = {
                str(item.get("name")): str(item.get("table_id"))
                for item in self._paginate(f"/bitable/v1/apps/{self._app_token}/tables")
            }
        table_id = self._table_ids.get(table_name)
        if not table_id:
            raise FeishuGatewayError(f"canonical table unavailable: {table_name}")
        return table_id

    def list_records(self, table_name: str) -> list[dict[str, Any]]:
        table_id = self.table_id(table_name)
        return self._paginate(
            f"/bitable/v1/apps/{self._app_token}/tables/{table_id}/records",
            params={"page_size": 500, "automatic_fields": "true"},
        )

    def get_record(self, table_name: str, record_id: str) -> dict[str, Any]:
        table_id = self.table_id(table_name)
        data = self._request(
            "GET",
            f"/bitable/v1/apps/{self._app_token}/tables/{table_id}/records/{record_id}",
            params={"automatic_fields": "true"},
        )
        record = data.get("record")
        if not isinstance(record, dict):
            raise FeishuGatewayError(f"record read-back missing: {table_name}")
        return record

    def create_record(
        self,
        table_name: str,
        fields: Mapping[str, Any],
        *,
        verify_fields: Iterable[str] = (),
    ) -> dict[str, Any]:
        table_id = self.table_id(table_name)
        data = self._request(
            "POST",
            f"/bitable/v1/apps/{self._app_token}/tables/{table_id}/records",
            params={"user_id_type": "open_id"},
            json_body={"fields": dict(fields)},
        )
        record = data.get("record") or {}
        record_id = str(record.get("record_id") or "")
        if not record_id:
            raise FeishuGatewayError(f"record creation returned no ID: {table_name}")
        readback = self.get_record(table_name, record_id)
        self._assert_readback(fields, readback.get("fields") or {}, verify_fields)
        return readback

    def update_record(
        self,
        table_name: str,
        record_id: str,
        fields: Mapping[str, Any],
        *,
        verify_fields: Iterable[str] = (),
    ) -> dict[str, Any]:
        table_id = self.table_id(table_name)
        self._request(
            "PUT",
            f"/bitable/v1/apps/{self._app_token}/tables/{table_id}/records/{record_id}",
            params={"user_id_type": "open_id"},
            json_body={"fields": dict(fields)},
        )
        readback = self.get_record(table_name, record_id)
        self._assert_readback(fields, readback.get("fields") or {}, verify_fields)
        return readback

    def upload_bitable_media(self, *, file_name: str, content: bytes, content_type: str) -> str:
        safe_name = PurePath(file_name).name[:250] or "evidence.bin"
        response = self._http.post(
            f"{self.API_ROOT}/drive/v1/medias/upload_all",
            headers={"Authorization": f"Bearer {self._tenant_token()}"},
            data={
                "file_name": safe_name,
                "parent_type": "bitable_file",
                "parent_node": self._app_token,
                "size": str(len(content)),
            },
            files={"file": (safe_name, content, content_type)},
            timeout=self._timeout,
        )
        payload = self._response_payload(response, "Bitable media upload")
        file_token = str((payload.get("data") or {}).get("file_token") or "")
        if not file_token:
            raise FeishuGatewayError("Bitable media upload returned no file_token")
        return file_token

    def send_interactive_card(
        self,
        receive_id: str,
        card: Mapping[str, Any],
        *,
        receive_id_type: str = "open_id",
    ) -> str:
        if receive_id_type not in {"open_id", "chat_id"}:
            raise FeishuGatewayError("unsupported message receive_id_type")
        data = self._request(
            "POST",
            "/im/v1/messages",
            params={"receive_id_type": receive_id_type},
            json_body={
                "receive_id": receive_id,
                "msg_type": "interactive",
                "content": json.dumps(dict(card), ensure_ascii=False),
            },
        )
        return str(data.get("message_id") or "")

    def list_chat_member_open_ids(self, chat_id: str) -> tuple[str, ...]:
        return tuple(
            str(item.get("member_id") or "")
            for item in self.list_chat_members(chat_id)
            if str(item.get("member_id") or "")
        )

    def list_chat_members(self, chat_id: str) -> tuple[dict[str, Any], ...]:
        items = self._paginate(
            f"/im/v1/chats/{chat_id}/members",
            params={"member_id_type": "open_id", "page_size": 100},
        )
        return tuple(dict(item) for item in items)

    def get_message(self, message_id: str) -> dict[str, Any]:
        data = self._request("GET", f"/im/v1/messages/{message_id}")
        items = data.get("items") or []
        if not items:
            raise FeishuGatewayError("Mentor message read-back returned no message")
        message = items[0]
        if str(message.get("message_id") or "") != message_id:
            raise FeishuGatewayError("Mentor message read-back ID mismatch")
        return message

    def _paginate(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token = ""
        while True:
            query = dict(params or {})
            query.setdefault("page_size", 100)
            if page_token:
                query["page_token"] = page_token
            data = self._request("GET", path, params=query)
            items.extend(data.get("items") or [])
            if not data.get("has_more"):
                return items
            page_token = str(data.get("page_token") or "")
            if not page_token:
                raise FeishuGatewayError("Feishu pagination indicated more data without page_token")

    def _tenant_token(self) -> str:
        if self._token and time.monotonic() < self._token_expiry:
            return self._token
        with self._token_lock:
            if self._token and time.monotonic() < self._token_expiry:
                return self._token
            response = self._http.post(
                f"{self.API_ROOT}/auth/v3/tenant_access_token/internal",
                json={"app_id": self._app_id, "app_secret": self._app_secret},
                timeout=self._timeout,
            )
            payload = self._response_payload(response, "tenant token")
            token = str(payload.get("tenant_access_token") or "")
            if not token:
                raise FeishuGatewayError("tenant token response did not include a token")
            self._token = token
            self._token_expiry = time.monotonic() + max(60, int(payload.get("expire") or 7200) - 120)
            return token

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        response = self._http.request(
            method,
            f"{self.API_ROOT}{path}",
            headers={
                "Authorization": f"Bearer {self._tenant_token()}",
                "Content-Type": "application/json; charset=utf-8",
            },
            params=dict(params or {}),
            json=dict(json_body) if json_body is not None else None,
            timeout=self._timeout,
        )
        payload = self._response_payload(response, f"Feishu {method} {path}")
        return payload.get("data") or {}

    @staticmethod
    def _response_payload(response: requests.Response, operation: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except Exception as exc:
            raise FeishuGatewayError(f"{operation} returned non-JSON response") from exc
        if response.status_code != 200 or payload.get("code", 0) != 0:
            raise FeishuGatewayError(
                f"{operation} failed: http={response.status_code} "
                f"code={payload.get('code')} msg={payload.get('msg')}"
            )
        return payload

    @classmethod
    def _assert_readback(
        cls,
        expected: Mapping[str, Any],
        actual: Mapping[str, Any],
        fields: Iterable[str],
    ) -> None:
        for name in fields:
            if name not in actual:
                raise FeishuGatewayError(f"Bitable read-back missing field: {name}")
            if cls._normalise(expected.get(name)) != cls._normalise(actual.get(name)):
                raise FeishuGatewayError(f"Bitable read-back mismatch: {name}")

    @classmethod
    def _normalise(cls, value: Any) -> Any:
        if isinstance(value, dict):
            if "file_token" in value:
                return value["file_token"]
            if "record_id" in value:
                return value["record_id"]
            if "id" in value and len(value) <= 3:
                return value["id"]
            return {key: cls._normalise(item) for key, item in sorted(value.items())}
        if isinstance(value, list):
            return sorted((cls._normalise(item) for item in value), key=lambda item: str(item))
        return value


def linked_record_ids(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            record_id = item.get("record_id") or item.get("id")
            if record_id:
                result.append(str(record_id))
    return tuple(result)
