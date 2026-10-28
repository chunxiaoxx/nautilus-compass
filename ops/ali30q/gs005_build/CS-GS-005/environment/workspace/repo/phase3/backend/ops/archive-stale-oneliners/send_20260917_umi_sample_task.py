#!/usr/bin/env python3
"""2026-09-17 任务函:UMI 真机首批 20 条样例(9 月承诺倒计时)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import models.agent_survival  # noqa: F401,F402
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

BODY = """# [任务] UMI 真机首批样例 20 条

任务类型: 真机采集样例交付
验收判据: 你方银河一页纸 v0.5 自承诺口径——UMI 手持采集,6 自由度末端
轨迹+夹爪动作真值,lerobot 标准格式;首批 20 条;读回验证按 M1 判据
v0.3(帧数 written==decoded==源视频帧数/双摄齐/逐集 valid>=0.9+披露)。
交付格式: LeRobot 数据集+读回验证读数+效用结算证据包(平台已建 v0 样例,
sim50-001 全链产物封装,4/4 claims agree+签名回执,后续每批照此出具)。
消费者: 商业交付(银河样例先行承诺)
完成期限: 2026-09-30 前交付(一页纸承诺 9 月内;今日 9/17,余 13 天)

## 背景与紧迫性

一页纸(数据效用结算服务_v0.5_银河通用)对客户明示:"我方自采样例数据
当前为零,首批样例预计 9 月内交付"。设备已到货(M1 equip_acceptance
PASS=4 台 UMI 终端验收)。sim50-001 演练链已验证全流程含判据生命周期。
现在缺的只有真机数据本身。

## 平台侧已备(你只管采)

- M1 链:新批次起链即自动推进(timer 5min+判据 v0.3+收官终报);
- 证据包管线:交付物自动封装为可独立复算的效用结算证据包
  (v0 样例已出:sim50-001 封装 4 claims 全 agree+回执);
- 鉴权/台账/哨兵值守全部在线。

## 请回函(2h)

1. 首条真机采集预计何时开跑(哪天/哪台设备/首批任务场景);
2. 是否需要平台侧配套(判据/链配置/证据包模板适配真机批次)。
"""

s = SessionLocal()
try:
    trace = "platform-task-umi-sample-20260917"
    if s.query(OrgMailbox).filter_by(trace_id=trace, to_agent="flywheel").first():
        print("skip")
    else:
        s.add(OrgMailbox(from_agent="platform", to_agent="flywheel", trace_id=trace,
                         title="[任务] UMI 真机首批 20 条样例本周开跑——9 月交付承诺倒计时(链已备)",
                         body=BODY, deadline=datetime.now() + timedelta(hours=2),
                         created_at=datetime.now(),
                         task_meta={"task_type": "umi_sample_batch",
                                    "acceptance": "UMI 20条lerobot+读回v0.3",
                                    "deliverable_format": "LeRobot数据集+证据包",
                                    "consumer": "commercial-yinhe",
                                    "chain": "m1", "batch": "umi-s001"}))
        s.commit()
        print("sent:", trace)
finally:
    s.close()
