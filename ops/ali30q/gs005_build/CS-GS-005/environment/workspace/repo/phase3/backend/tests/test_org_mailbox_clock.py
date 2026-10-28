"""OrgMailbox 时钟回归测试(2026-10-04 根修)——created_at 必须走 DB 钟,禁 utcnow。

背景:default=datetime.utcnow 曾致模型路径函(writeback/frames_declare)created_at
早 8h,与 SQL 路径(send_letter, DB now)两钟混列——2701 trace ts 与端点上线时间
物理矛盾实证。本测试静态断言防回归(utcnow 回潮即红)。
"""
import models.agent_survival  # noqa: F401
from models.org_mailbox import OrgMailbox


def test_created_at_uses_db_clock_not_utcnow():
    col = OrgMailbox.__table__.c.created_at
    # server_default 必须存在且含 now;python 侧 default(utcnow)必须不存在
    assert col.server_default is not None, "created_at 必须有 server_default(DB 钟)"
    assert "now" in str(col.server_default.arg).lower()
    assert col.default is None or callable(col.default) is False, "禁用 python 侧 utcnow default"


def test_no_utcnow_in_module():
    import inspect
    import re
    import models.org_mailbox as m
    src = inspect.getsource(m)
    # 禁的是调用(注释留痕病名允许):default=...utcnow / utcnow() 调用模式
    assert not re.search(r"=\s*datetime\.utcnow|utcnow\(\)", src), \
        "org_mailbox 禁 utcnow 调用(9/22 与 10/4 两轮病根;注释提及病名允许)"
