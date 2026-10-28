"""Print an audit-safe, read-only Bitable schema summary for one explicit Base."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping
from urllib.parse import quote, urlencode


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.fde_assignment_runner import FEISHU, _http, tenant_token
from services.fde_phase3_feishu import probe_schema, validate_explicit_base_token


class FeishuEnvelopeError(RuntimeError):
    """A metadata response did not carry Feishu's successful API envelope."""


class ReadOnlySchemaClient:
    """Feishu HTTP adapter limited to the Bitable tables and fields endpoints."""

    def __init__(self, tenant_access_token: str):
        self._tenant_access_token = tenant_access_token

    def list_tables(self, base_token: str) -> list[Mapping[str, Any]]:
        return self._list_schema_pages(base_token=base_token, table_id=None)

    def list_fields(self, base_token: str, table_id: str) -> list[Mapping[str, Any]]:
        return self._list_schema_pages(base_token=base_token, table_id=table_id)

    def _list_schema_pages(
        self, *, base_token: str, table_id: str | None
    ) -> list[Mapping[str, Any]]:
        app_route = f"/bitable/v1/apps/{quote(base_token, safe='')}"
        if table_id is None:
            fixed_route = f"{app_route}/tables"
        else:
            fixed_route = (
                f"{app_route}/tables/{quote(table_id, safe='')}/fields"
            )
        items: list[Mapping[str, Any]] = []
        page_token: str | None = None
        seen_page_tokens: set[str] = set()
        while True:
            query: dict[str, str] = {"page_size": "100"}
            if page_token is not None:
                query["page_token"] = page_token
            response = _http(
                "GET",
                f"{FEISHU}{fixed_route}?{urlencode(query)}",
                token=self._tenant_access_token,
            )
            data = self._require_success_data(response)
            page_items = data.get("items")
            if not isinstance(page_items, list) or not all(
                isinstance(item, Mapping) for item in page_items
            ):
                raise FeishuEnvelopeError("Feishu metadata envelope has invalid items")
            items.extend(page_items)
            has_more = data.get("has_more")
            if has_more is False:
                return items
            if has_more is not True:
                raise FeishuEnvelopeError(
                    "Feishu metadata envelope has invalid has_more"
                )
            next_page_token = data.get("page_token")
            if (
                not isinstance(next_page_token, str)
                or not next_page_token.strip()
            ):
                raise FeishuEnvelopeError("Feishu metadata envelope has no next page token")
            if next_page_token in seen_page_tokens:
                raise FeishuEnvelopeError("Feishu metadata pagination repeated a page token")
            seen_page_tokens.add(next_page_token)
            page_token = next_page_token

    @staticmethod
    def _require_success_data(response: Any) -> Mapping[str, Any]:
        if (
            not isinstance(response, Mapping)
            or type(response.get("code")) is not int
            or response["code"] != 0
        ):
            raise FeishuEnvelopeError("Feishu metadata request failed its code check")
        data = response.get("data")
        if not isinstance(data, Mapping):
            raise FeishuEnvelopeError("Feishu metadata envelope has no data mapping")
        return data


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only Bitable schema metadata probe for one explicit Base."
    )
    parser.add_argument(
        "--base-token",
        required=True,
        help="Explicit Bitable Base token. It is used only in memory and is never printed.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        base_token = validate_explicit_base_token(args.base_token)
        result = probe_schema(
            ReadOnlySchemaClient(tenant_token()),
            base_token=base_token,
        )
    except Exception as exc:  # Do not stringify exceptions; URLs can contain the Base token.
        print(
            json.dumps(
                {"error": "schema_probe_failed", "exception_type": type(exc).__name__},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result.to_audit_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
