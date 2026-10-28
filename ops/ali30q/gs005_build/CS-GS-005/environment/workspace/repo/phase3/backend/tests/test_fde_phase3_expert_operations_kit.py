from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
KIT_ROOT = REPO_ROOT / "docs" / "business" / "phase3_expert_operations"


def _read(name: str) -> str:
    return (KIT_ROOT / name).read_text(encoding="utf-8")


def test_phase3_operations_kit_covers_all_operational_audiences() -> None:
    assert (KIT_ROOT / "README.md").is_file()
    recruiting = _read("01_RECRUITING_KIT.md")
    onboarding = _read("02_EXPERT_ONBOARDING.md")
    operator = _read("03_OPERATOR_SOP.md")

    for heading in ("目标专家画像", "招募海报文案", "私聊邀约话术", "社群招募话术"):
        assert heading in recruiting
    for heading in ("15 分钟入门培训", "在线多轮交互操作指引", "提交证据包填写示例", "常见问题", "返修通知模板"):
        assert heading in onboarding
    for heading in ("筛选", "建群", "培训", "派题", "结算确认"):
        assert heading in operator


def test_phase3_operations_kit_keeps_payment_and_acceptance_boundary() -> None:
    public_copy = _read("01_RECRUITING_KIT.md") + _read("02_EXPERT_ONBOARDING.md")

    assert "200 元" in public_copy
    assert "验收通过后 3 个工作日内" in public_copy
    assert "不等于甲方通过" in public_copy


def test_expert_facing_material_does_not_expose_internal_export_fields() -> None:
    public_copy = _read("01_RECRUITING_KIT.md") + _read("02_EXPERT_ONBOARDING.md")

    for internal_term in (
        "revision_of",
        "payload_hash",
        "manifest_hash",
        "Bitable record ID",
        "record_id",
        "买方原始反馈",
    ):
        assert internal_term not in public_copy


def test_expert_onboarding_preserves_the_required_interaction_evidence() -> None:
    onboarding = _read("02_EXPERT_ONBOARDING.md")

    for requirement in (
        "豆包办公任务",
        "至少六轮",
        "每个模型回答",
        "点赞或点踩",
        "标签",
        "具体原因",
        "24 小时内",
    ):
        assert requirement in onboarding


def test_recruiting_copy_does_not_invent_channels_or_scale_targets() -> None:
    recruiting = _read("01_RECRUITING_KIT.md")

    for unsupported_claim in ("BOSS 直聘", "5 至 10 名", "150 名"):
        assert unsupported_claim not in recruiting
