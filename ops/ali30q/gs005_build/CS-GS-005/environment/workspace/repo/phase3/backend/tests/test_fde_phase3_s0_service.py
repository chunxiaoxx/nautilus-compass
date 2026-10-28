import json

import pytest

from services.fde_phase3_identity_service import FeishuIdentity
from services.fde_phase3_s0_service import Phase3S0Service, S0BindingError


class FakeReferences:
    def __init__(self):
        self.values = {}
        self.counter = 0

    def replace(self, purpose, token, payload, ttl_seconds):
        self.values[(purpose, token)] = dict(payload)

    def issue(self, purpose, payload, ttl_seconds):
        self.counter += 1
        token = f"token-{purpose}-{self.counter}"
        self.values[(purpose, token)] = dict(payload)
        return token

    def peek(self, purpose, token):
        return self.values[(purpose, token)]

    def lock(self, scope):
        class Lock:
            def __enter__(self):
                return None

            def __exit__(self, *args):
                return False

        return Lock()


class FakeGateway:
    def __init__(self, records=()):
        self.records = [
            {"record_id": item["record_id"], "fields": dict(item["fields"])}
            for item in records
        ]
        self.sent = []
        self.operator_members = ("ou_operator",)
        self.chat_members = ({"member_id": "ou_expert", "name": "樊金亮"},)

    def list_chat_members(self, chat_id):
        return tuple(dict(item) for item in self.chat_members)

    def list_records(self, table):
        return [
            {"record_id": item["record_id"], "fields": dict(item["fields"])}
            for item in self.records
        ]

    def get_record(self, table, record_id):
        item = next(item for item in self.records if item["record_id"] == record_id)
        return {"record_id": item["record_id"], "fields": dict(item["fields"])}

    def create_record(self, table, fields, verify_fields=()):
        item = {"record_id": f"rec_{len(self.records) + 1}", "fields": dict(fields)}
        self.records.append(item)
        return self.get_record(table, item["record_id"])

    def update_record(self, table, record_id, fields, verify_fields=()):
        item = next(item for item in self.records if item["record_id"] == record_id)
        if item["fields"].get("豆包UID"):
            assert fields.get("豆包UID", item["fields"]["豆包UID"]) == item["fields"]["豆包UID"]
        item["fields"].update(fields)
        return self.get_record(table, record_id)

    def send_interactive_card(self, receive_id, card, receive_id_type="open_id"):
        self.sent.append((receive_id, receive_id_type, json.dumps(card, ensure_ascii=False)))
        return f"om_{len(self.sent)}"

    def get_message(self, message_id):
        return {"message_id": message_id}

    def list_chat_member_open_ids(self, chat_id):
        return self.operator_members


def registration_payload(uid="631559529706268"):
    return {
        "姓名": "樊金亮",
        "豆包UID": uid,
        "联系方式": "expert@example.test",
        "最高学历": "硕士",
        "毕业院校": "测试大学",
        "专业": "工业工程",
        "学校层次": "其它院校",
        "工作领域": "在线交互标注",
        "工作年限": "6-10年",
        "行业证书认证（文字描述）": "",
        "每日作业时长": "2-4小时",
        "真实性与隐私承诺": True,
    }


def service(gateway, refs):
    return Phase3S0Service(
        gateway=gateway,
        references=refs,
        public_base_url="https://fde.example",
        operator_chat_id="oc_operator",
    )


def test_identity_first_registration_agent_advice_and_human_gate_complete_s0():
    refs = FakeReferences()
    gateway = FakeGateway()
    subject = service(gateway, refs)
    invite = subject.issue_pilot_invitation(expected_name="樊金亮")
    invitation = refs.peek("s0_invitation", invite.invite_token)
    intake = subject.start_identity_intake(
        invitation,
        FeishuIdentity(open_id="ou_expert", union_id="on_expert", name="樊金亮"),
    )

    receipt = subject.submit_registration(
        refs.peek("s0_registration", intake.registration_token),
        registration_payload(),
    )

    record = gateway.records[0]
    assert record["fields"]["豆包UID"] == "631559529706268"
    assert record["fields"]["飞书open_id"] == "ou_expert"
    assert record["fields"]["Agent准入建议"] == "建议通过"
    assert record["fields"]["运营准入决定"] == "待确认"
    assert receipt.bitable_readback_confirmed is True
    assert gateway.sent[0][0:2] == ("oc_operator", "chat_id")
    assert "631559529706268" not in gateway.sent[0][2]

    review_key = next(key for key in refs.values if key[0] == "s0_review")
    review = refs.values[review_key]
    decision = subject.apply_admission_decision(
        review,
        FeishuIdentity(open_id="ou_operator", union_id="on_operator", name="运营"),
        "通过",
    )

    assert gateway.records[0]["fields"]["准入状态"] == "已通过"
    assert gateway.records[0]["fields"]["运营准入人open_id"] == "ou_operator"
    assert gateway.sent[1][0:2] == ("ou_expert", "open_id")
    assert decision.status == "admitted_waiting_first_task"
    assert decision.mentor_message_readback_confirmed is True


def test_existing_uid_and_profile_cannot_be_overwritten():
    refs = FakeReferences()
    existing = registration_payload(uid="uid-once-only")
    existing.update({"身份绑定状态": "待绑定", "准入状态": "待审核"})
    gateway = FakeGateway(({"record_id": "rec_existing", "fields": existing},))
    subject = service(gateway, refs)
    invite = subject.issue_pilot_invitation("rec_existing", "樊金亮")
    intake = subject.start_identity_intake(
        refs.peek("s0_invitation", invite.invite_token),
        FeishuIdentity(open_id="ou_expert", union_id="on_expert", name="樊金亮"),
    )
    payload = registration_payload(uid="different-uid")

    with pytest.raises(S0BindingError, match="只能填写一次"):
        subject.submit_registration(refs.peek("s0_registration", intake.registration_token), payload)

    assert gateway.records[0]["fields"]["豆包UID"] == "uid-once-only"


def test_duplicate_name_and_nonmember_operator_fail_closed():
    refs = FakeReferences()
    records = (
        {"record_id": "rec_1", "fields": {"姓名": "樊金亮"}},
        {"record_id": "rec_2", "fields": {"姓名": "樊金亮"}},
    )
    gateway = FakeGateway(records)
    subject = service(gateway, refs)
    invite = subject.issue_pilot_invitation(expected_name="樊金亮")

    with pytest.raises(S0BindingError, match="多条同名"):
        subject.start_identity_intake(
            refs.peek("s0_invitation", invite.invite_token),
            FeishuIdentity(open_id="ou_expert", union_id="on_expert", name="樊金亮"),
        )

    with pytest.raises(S0BindingError, match="不是指定运营群成员"):
        subject.assert_operator(
            FeishuIdentity(open_id="ou_outsider", union_id="on_outsider", name="外部人员")
        )
