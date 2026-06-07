"""TDD · read_buyer_tasks — feishu Bitable 买方题行 → 规范题行(turf: 读归 compass)。

compass 只读 + 归一,**不 POST dispatch**(派归平台 /fde/dispatch · 连接器归 V7)。
归一输出键对齐 fde-row-assembler 的二期 16 列输入契约(复用不重造),
便于平台 dispatch + assemble_rows 直接消费。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ops.read_buyer_tasks import bitable_record_to_buyer_task, read_buyer_tasks  # noqa: E402


def test_maps_official_full_column_names():
    """飞书 Bitable 用官方 16 列全称 → 规范键。"""
    rec = {
        "record_id": "recABC",
        "fields": {
            "UID": "李雷_data_001",
            "题目": "测算某企业残保金并产出活公式表",
            "题目领域一级目录\n": "法律、政务与公共服务",
            "题目领域二级目录": "人力资源服务",
            "题目领域三级目录": "残保金测算与合规补救",
            "任务概括": "基于政策与花名册测算应缴额",
            "标注专家工作年限（未工作的可以写最高学历）": "6年",
            "人类所需完成时间": "14h",
            "附件格式标签": "pdf,xlsx",
            "附件内容（总结概括）": "公告 + 花名册",
            "产物格式标签": "Excel",
            "产物内容（总结概括）": "可编辑测算表",
            "任务类型": "L2",
            "打分checklist（必填）": "1. 公式不得写死",
        },
    }
    t = bitable_record_to_buyer_task(rec)
    assert t["uid"] == "李雷_data_001"
    assert t["题目"].startswith("测算某企业")
    assert t["一级目录"] == "法律、政务与公共服务"
    assert t["二级目录"] == "人力资源服务"
    assert t["三级目录"] == "残保金测算与合规补救"
    assert t["任务概括"] == "基于政策与花名册测算应缴额"
    assert t["专家年限"] == "6年"
    assert t["完成时间"] == "14h"
    assert t["附件格式标签"] == "pdf,xlsx"
    assert t["附件内容"] == "公告 + 花名册"
    assert t["产物格式标签"] == "Excel"
    assert t["产物内容"] == "可编辑测算表"
    assert t["level"] == "L2"
    assert t["打分checklist"].startswith("1.")
    assert t["record_id"] == "recABC"


def test_maps_short_form_keys():
    """简写键(assemble_rows 输入风格)也归一。"""
    rec = {"fields": {"uid": "x_data_009", "题目": "权益类投资分析",
                      "一级目录": "个人金融与理财投资", "level": "L3"}}
    t = bitable_record_to_buyer_task(rec)
    assert t["uid"] == "x_data_009"
    assert t["一级目录"] == "个人金融与理财投资"
    assert t["level"] == "L3"


def test_dispatch_status_defaults_to_pending():
    """无派单状态 → 默认 '待派单'(compass 只读,状态供连接器消费)。"""
    rec = {"fields": {"题目": "某题"}}
    t = bitable_record_to_buyer_task(rec)
    assert t["派单状态"] == "待派单"


def test_dispatch_status_passthrough():
    rec = {"fields": {"题目": "某题", "派单状态": "已派单"}}
    t = bitable_record_to_buyer_task(rec)
    assert t["派单状态"] == "已派单"


def test_read_buyer_tasks_skips_empty_rows():
    """空行(无 uid 无题目)被过滤。"""
    records = [
        {"fields": {"题目": "有题目的真任务"}},
        {"fields": {}},                       # 空行
        {"fields": {"派单状态": "待派单"}},     # 只有状态,无题目无 uid → 空
    ]
    out = read_buyer_tasks(records)
    assert len(out) == 1
    assert out[0]["题目"] == "有题目的真任务"


def test_read_buyer_tasks_skip_dispatched():
    """skip_dispatched=True 只返回未派单的题。"""
    records = [
        {"fields": {"uid": "a", "题目": "未派单题"}},
        {"fields": {"uid": "b", "题目": "已派单题", "派单状态": "已派单"}},
    ]
    out = read_buyer_tasks(records, skip_dispatched=True)
    uids = [t["uid"] for t in out]
    assert uids == ["a"]


def test_read_buyer_tasks_keeps_all_by_default():
    records = [
        {"fields": {"uid": "a", "题目": "t1"}},
        {"fields": {"uid": "b", "题目": "t2", "派单状态": "已派单"}},
    ]
    out = read_buyer_tasks(records)
    assert len(out) == 2
