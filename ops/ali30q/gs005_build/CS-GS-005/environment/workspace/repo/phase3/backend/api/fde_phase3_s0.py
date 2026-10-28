"""Invitation-only S0 API. It deliberately exposes no task workbench."""

from __future__ import annotations

import hmac
import html
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qs

import redis
from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from services.fde_phase3_bitable_gateway import FeishuPhase3Gateway
from services.fde_phase3_identity_service import (
    FeishuIdentity,
    FeishuOAuthClient,
    OpaqueReferenceError,
    RedisOpaqueStore,
    SignedTokenCodec,
    SignedTokenError,
)
from services.fde_phase3_s0_service import (
    ADMISSION_DECISIONS,
    REGISTRATION_FIELD_OPTIONS,
    REGISTRATION_REQUIRED_FIELDS,
    Phase3S0Service,
    S0BindingError,
    S0IdentityIntake,
    S0_VERSION,
)


router = APIRouter(prefix="/api/platform/fde/phase3/s0", tags=["FDE Phase 3 S0"])


@dataclass(frozen=True)
class S0Runtime:
    codec: SignedTokenCodec
    oauth: FeishuOAuthClient
    references: RedisOpaqueStore
    service: Phase3S0Service
    operator_secret: str
    pilot_expert_record_id: str
    pilot_expected_name: str
    public_base_url: str


_runtime_instance: S0Runtime | None = None


def _load_secret_file() -> None:
    path = Path(
        os.getenv(
            "FDE_PHASE3_FEISHU_SECRET_FILE",
            str(Path.home() / ".claude" / ".cache" / ".fde_api_secrets.env"),
        )
    )
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def _runtime() -> S0Runtime:
    global _runtime_instance
    if _runtime_instance is not None:
        return _runtime_instance
    _load_secret_file()
    required = {
        "FEISHU_APP_ID": os.getenv("FEISHU_APP_ID", ""),
        "FEISHU_APP_SECRET": os.getenv("FEISHU_APP_SECRET", ""),
        "FDE_PHASE3_APP_TOKEN": os.getenv("FDE_PHASE3_APP_TOKEN", ""),
        "FDE_PHASE3_SESSION_SECRET": os.getenv("FDE_PHASE3_SESSION_SECRET", ""),
        "FDE_PHASE3_S0_OPERATOR_SECRET": os.getenv("FDE_PHASE3_S0_OPERATOR_SECRET", ""),
        "FDE_PHASE3_S0_OPERATOR_CHAT_ID": os.getenv("FDE_PHASE3_S0_OPERATOR_CHAT_ID", ""),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError("missing S0 configuration: " + ", ".join(missing))
    pilot_record_id = os.getenv("FDE_PHASE3_S0_PILOT_EXPERT_RECORD_ID", "").strip()
    pilot_expected_name = os.getenv("FDE_PHASE3_S0_PILOT_EXPECTED_NAME", "").strip()
    if not pilot_record_id and not pilot_expected_name:
        raise RuntimeError("missing S0 pilot expert identity")

    public_base_url = os.getenv("FDE_PHASE3_PUBLIC_BASE_URL", "https://fde.nautilus.social").rstrip("/")
    redirect_uri = f"{public_base_url}/api/platform/fde/phase3/s0/bind/callback"
    redis_client = redis.Redis.from_url(
        os.getenv("FDE_PHASE3_REDIS_URL", "redis://127.0.0.1:6379/4"),
        decode_responses=True,
    )
    references = RedisOpaqueStore(redis_client, namespace="fde_phase3_s0")
    gateway = FeishuPhase3Gateway(
        app_id=required["FEISHU_APP_ID"],
        app_secret=required["FEISHU_APP_SECRET"],
        app_token=required["FDE_PHASE3_APP_TOKEN"],
    )
    codec = SignedTokenCodec(required["FDE_PHASE3_SESSION_SECRET"].encode("utf-8"))
    _runtime_instance = S0Runtime(
        codec=codec,
        oauth=FeishuOAuthClient(
            app_id=required["FEISHU_APP_ID"],
            app_secret=required["FEISHU_APP_SECRET"],
            redirect_uri=redirect_uri,
            scope=os.getenv("FDE_PHASE3_FEISHU_OAUTH_SCOPE", ""),
        ),
        references=references,
        service=Phase3S0Service(
            gateway=gateway,
            references=references,
            public_base_url=public_base_url,
            operator_chat_id=required["FDE_PHASE3_S0_OPERATOR_CHAT_ID"],
        ),
        operator_secret=required["FDE_PHASE3_S0_OPERATOR_SECRET"],
        pilot_expert_record_id=pilot_record_id,
        pilot_expected_name=pilot_expected_name,
        public_base_url=public_base_url,
    )
    return _runtime_instance


def _require_operator(authorization: str | None) -> S0Runtime:
    runtime = _runtime()
    supplied = ""
    if authorization and authorization.startswith("Bearer "):
        supplied = authorization[7:]
    if not supplied or not hmac.compare_digest(supplied, runtime.operator_secret):
        raise HTTPException(status_code=403, detail="S0 operator authorization required")
    return runtime


@router.get("/version")
def s0_version() -> dict[str, Any]:
    return {
        "version": S0_VERSION,
        "constitution_version": "t1-constitution-v1.0-20260730",
        "mode": "invitation_only_identity_first",
        "invitation_delivery": "direct_im_bound_to_open_id",
        "human_admission_gate": True,
        "workbench_exposed": False,
    }


@router.post("/pilot/invitation")
def create_pilot_invitation(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    runtime = _require_operator(authorization)
    try:
        invitation = runtime.service.issue_pilot_invitation(
            runtime.pilot_expert_record_id,
            runtime.pilot_expected_name,
        )
        runtime.service.deliver_pilot_invitation(invitation)
    except Exception as exc:
        raise _safe_http_error(exc)
    return {
        "expert_name": invitation.expert_name,
        "audit_ref": invitation.audit_ref,
        "expires_in_seconds": invitation.expires_in_seconds,
        "delivery": "direct_im_readback_confirmed",
    }


@router.get("/pilot/status")
def pilot_status(
    audit_ref: str = Query(min_length=16, max_length=200),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    runtime = _require_operator(authorization)
    try:
        return runtime.service.audit_status(audit_ref)
    except Exception as exc:
        raise _safe_http_error(exc)


@router.get("/bind/start")
def bind_start(invite: str = Query(min_length=16, max_length=200)) -> RedirectResponse:
    runtime = _runtime()
    try:
        runtime.references.peek("s0_invitation", invite)
    except OpaqueReferenceError as exc:
        raise HTTPException(status_code=410, detail="入口已失效，请使用智涌导师最新消息") from exc
    state = runtime.codec.encode(
        "s0_oauth_state",
        {"flow": "expert", "reference": invite, "nonce": secrets.token_urlsafe(12)},
        300,
    )
    return RedirectResponse(runtime.oauth.authorization_url(state), status_code=302)


@router.get("/pilot/review/start")
def review_start(review: str = Query(min_length=16, max_length=200)) -> RedirectResponse:
    runtime = _runtime()
    try:
        runtime.references.peek("s0_review", review)
    except OpaqueReferenceError as exc:
        raise HTTPException(status_code=410, detail="该准入事项已失效或已处理") from exc
    state = runtime.codec.encode(
        "s0_oauth_state",
        {"flow": "operator", "reference": review, "nonce": secrets.token_urlsafe(12)},
        300,
    )
    return RedirectResponse(runtime.oauth.authorization_url(state), status_code=302)


@router.get("/bind/callback", response_class=HTMLResponse)
def bind_callback(
    code: str = Query(min_length=4),
    state: str = Query(min_length=20),
) -> HTMLResponse:
    runtime = _runtime()
    try:
        state_claims = runtime.codec.decode(state, "s0_oauth_state")
        flow = str(state_claims.get("flow") or "")
        reference = str(state_claims.get("reference") or "")
        identity = runtime.oauth.exchange_code(code)
        if flow == "expert":
            invitation = runtime.references.consume("s0_invitation", reference)
            intake = runtime.service.start_identity_intake(invitation, identity)
            return HTMLResponse(_registration_page(intake))
        if flow == "operator":
            review = runtime.references.peek("s0_review", reference)
            runtime.service.assert_operator(identity)
            preview = runtime.service.operator_review(review)
            session = runtime.references.issue(
                "s0_operator_session",
                {
                    "review_token": reference,
                    "open_id": identity.open_id,
                    "union_id": identity.union_id,
                    "name": identity.name,
                },
                600,
            )
            return HTMLResponse(_review_page(session, preview))
        raise SignedTokenError("unknown S0 OAuth flow")
    except (SignedTokenError, OpaqueReferenceError):
        return HTMLResponse(_result_page("入口已失效", "请使用智涌导师最新消息重新进入。", False), status_code=410)
    except Exception as exc:
        message = str(exc) if isinstance(exc, S0BindingError) else "飞书身份或权威账本回读未完成。"
        return HTMLResponse(_result_page("操作未完成", message, False), status_code=409)


@router.post("/register", response_class=HTMLResponse)
async def register(request: Request) -> HTMLResponse:
    runtime = _runtime()
    try:
        form = await _urlencoded_form(request)
        registration_token = _form_value(form, "registration")
        intake = runtime.references.peek("s0_registration", registration_token)
        submitted = {
            "姓名": _form_value(form, "name"),
            "豆包UID": _form_value(form, "doubao_uid"),
            "联系方式": _form_value(form, "contact"),
            "最高学历": _form_value(form, "education"),
            "毕业院校": _form_value(form, "school"),
            "专业": _form_value(form, "major"),
            "学校层次": _form_value(form, "school_tier"),
            "工作领域": _form_value(form, "work_domain"),
            "工作年限": _form_value(form, "work_years"),
            "行业证书认证（文字描述）": _form_value(form, "certificate"),
            "每日作业时长": _form_value(form, "daily_hours"),
            "真实性与隐私承诺": _form_value(form, "consent") in {"1", "true", "on"},
        }
        runtime.service.submit_registration(intake, submitted)
        runtime.references.consume("s0_registration", registration_token)
        return HTMLResponse(
            _result_page(
                "报名已进入准入确认",
                "Agent 已完成信息检查并将证据摘要发给运营。请返回飞书等待结果。",
                True,
            )
        )
    except (OpaqueReferenceError, KeyError):
        return HTMLResponse(_result_page("报名会话已失效", "请使用智涌导师最新消息重新进入。", False), status_code=410)
    except Exception as exc:
        message = str(exc) if isinstance(exc, S0BindingError) else "权威账本写入或读回未完成，请勿重复填写。"
        return HTMLResponse(_result_page("报名未完成", message, False), status_code=409)


@router.post("/pilot/review", response_class=HTMLResponse)
async def submit_review(request: Request) -> HTMLResponse:
    runtime = _runtime()
    try:
        form = await _urlencoded_form(request)
        operator_session = runtime.references.consume(
            "s0_operator_session",
            _form_value(form, "operator_session"),
        )
        review_token = str(operator_session.get("review_token") or "")
        review = runtime.references.peek("s0_review", review_token)
        identity = FeishuIdentity(
            open_id=str(operator_session.get("open_id") or ""),
            union_id=str(operator_session.get("union_id") or ""),
            name=str(operator_session.get("name") or ""),
        )
        decision = _form_value(form, "decision")
        runtime.service.apply_admission_decision(
            review,
            identity,
            decision,
            _form_value(form, "note"),
        )
        runtime.references.consume("s0_review", review_token)
        return HTMLResponse(
            _result_page(
                "运营决定已发布",
                "Bitable 已独立读回，专家已收到只包含当前状态和下一动作的导师消息。",
                True,
            )
        )
    except (OpaqueReferenceError, KeyError):
        return HTMLResponse(_result_page("审核会话已失效", "请从运营群最新卡片重新进入。", False), status_code=410)
    except Exception as exc:
        message = str(exc) if isinstance(exc, S0BindingError) else "运营决定写入或消息读回未完成。"
        return HTMLResponse(_result_page("运营决定未完成", message, False), status_code=409)


async def _urlencoded_form(request: Request) -> dict[str, list[str]]:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/x-www-form-urlencoded":
        raise S0BindingError("仅接受当前页面提交")
    body = await request.body()
    if len(body) > 65536:
        raise S0BindingError("提交内容过大")
    return parse_qs(body.decode("utf-8"), keep_blank_values=True)


def _form_value(form: Mapping[str, list[str]], key: str) -> str:
    values = form.get(key) or [""]
    return str(values[0]).strip()


def _registration_page(intake: S0IdentityIntake) -> str:
    missing = set(intake.missing_fields)
    controls: list[str] = []
    if "姓名" in missing:
        controls.append(
            f"<label>姓名<input name='name' value='{html.escape(intake.expert_name)}' readonly></label>"
        )
    else:
        controls.append(f"<input type='hidden' name='name' value='{html.escape(intake.expert_name)}'>")
    controls.extend(
        _registration_control(field)
        for field in intake.missing_fields
        if field != "姓名"
    )
    if not intake.missing_fields:
        controls.append("<p class='hint'>已有报名信息完整。本页只确认本人身份，不要求重复填写。</p>")
    controls.append(
        f"<input type='hidden' name='registration' value='{html.escape(intake.registration_token)}'>"
    )
    controls.append("<button type='submit'>确认并交给 Agent 检查</button>")
    body = (
        "<h1>第三期 T1 · 身份与报名确认</h1>"
        "<p>系统只显示缺失项。UID 只填写一次，提交后不能在此修改。</p>"
        "<form method='post' action='/api/platform/fde/phase3/s0/register'>"
        + "".join(controls)
        + "</form><p class='hint'>提交后由 Agent 生成证据摘要，运营只做三选一确认；当前不会开放题目或交互。</p>"
    )
    return _layout("第三期 T1 身份与报名确认", body)


def _registration_control(field: str) -> str:
    config = {
        "豆包UID": ("doubao_uid", "豆包 UID（只填写一次）"),
        "联系方式": ("contact", "联系方式"),
        "最高学历": ("education", "最高学历"),
        "毕业院校": ("school", "毕业院校"),
        "专业": ("major", "专业"),
        "学校层次": ("school_tier", "学校层次"),
        "工作领域": ("work_domain", "工作领域"),
        "工作年限": ("work_years", "工作年限"),
        "行业证书认证（文字描述）": ("certificate", "行业证书（选填）"),
        "每日作业时长": ("daily_hours", "每日可参与时长"),
        "真实性与隐私承诺": ("consent", "我确认信息真实并遵守隐私要求"),
    }
    name, label = config[field]
    required = " required" if field in REGISTRATION_REQUIRED_FIELDS else ""
    if field in REGISTRATION_FIELD_OPTIONS:
        options = "<option value=''>请选择</option>" + "".join(
            f"<option value='{html.escape(option)}'>{html.escape(option)}</option>"
            for option in REGISTRATION_FIELD_OPTIONS[field]
        )
        return f"<label>{html.escape(label)}<select name='{name}'{required}>{options}</select></label>"
    if field == "真实性与隐私承诺":
        return (
            "<label class='check'><input type='checkbox' name='consent' value='true' required>"
            f"<span>{html.escape(label)}</span></label>"
        )
    input_type = "password" if field == "豆包UID" else "text"
    inputmode = " inputmode='numeric'" if field == "豆包UID" else ""
    return f"<label>{html.escape(label)}<input type='{input_type}' name='{name}'{inputmode}{required}></label>"


def _review_page(operator_session: str, preview: Mapping[str, str]) -> str:
    buttons = "".join(
        f"<button type='submit' name='decision' value='{html.escape(decision)}'>{html.escape(decision)}</button>"
        for decision in ADMISSION_DECISIONS
    )
    body = (
        "<h1>T1 首题 · 运营准入确认</h1>"
        f"<p><strong>专家：</strong>{html.escape(preview['expert_name'])}</p>"
        f"<p><strong>Agent 建议：</strong>{html.escape(preview['agent_recommendation'])}</p>"
        f"<div class='evidence'>{html.escape(preview['agent_summary'])}</div>"
        "<p class='hint'>不重做评分、不修改专家内容。核对摘要后只做一个选择。</p>"
        "<form method='post' action='/api/platform/fde/phase3/s0/pilot/review'>"
        f"<input type='hidden' name='operator_session' value='{html.escape(operator_session)}'>"
        "<label>处理说明<textarea name='note' maxlength='500' placeholder='退回或升级时必填；与 Agent 建议不一致时必填'></textarea></label>"
        f"<div class='choices'>{buttons}</div></form>"
    )
    return _layout("T1 首题运营准入确认", body)


def _result_page(title: str, message: str, success: bool) -> str:
    color = "#0d6b52" if success else "#a44335"
    body = (
        f"<div class='bar' style='background:{color}'></div>"
        f"<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(message)}</p>"
        "<p class='hint'>无需填写记录号、任务编号或内部状态。</p>"
    )
    return _layout(title, body)


def _layout(title: str, body: str) -> str:
    return (
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
        "style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'\">"
        f"<title>{html.escape(title)}</title><style>"
        ":root{--ink:#14251f;--muted:#64736d;--paper:#fffdf7;--line:#d9d2c3;--accent:#0d6b52}"
        "*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 10%,#dcebdd,transparent 35%),#f3f0e7;"
        "color:var(--ink);font-family:'Microsoft YaHei',sans-serif;display:grid;place-items:center;min-height:100vh;padding:20px}"
        "main{width:min(620px,100%);background:var(--paper);border:1px solid var(--line);border-radius:24px;padding:32px;box-shadow:0 18px 60px rgba(39,55,48,.13)}"
        "h1{font-size:clamp(26px,6vw,36px);margin:18px 0}p{line-height:1.75}.bar{width:52px;height:7px;border-radius:9px}"
        "label{display:grid;gap:7px;margin:16px 0;font-weight:700}input,select,textarea{width:100%;border:1px solid #b9c4bd;border-radius:12px;padding:12px;background:white;font:inherit}"
        "textarea{min-height:92px;resize:vertical}.check{grid-template-columns:22px 1fr;align-items:start}.check input{width:auto;margin-top:5px}"
        "button{border:0;border-radius:999px;padding:12px 18px;background:var(--accent);color:white;font:inherit;font-weight:700;cursor:pointer}"
        ".choices{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}.choices button:nth-child(2){background:#b66a24}.choices button:nth-child(3){background:#8f4138}"
        ".hint{font-size:13px;color:var(--muted)}.evidence{padding:16px;border-left:5px solid var(--accent);background:#eef4ef;line-height:1.7;border-radius:8px}"
        "</style></head><body><main>"
        f"{body}</main></body></html>"
    )


def _safe_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (S0BindingError, OpaqueReferenceError)):
        return HTTPException(status_code=409, detail=str(exc))
    return HTTPException(status_code=502, detail="S0 外部写入或读回失败")
