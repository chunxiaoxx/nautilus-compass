---
name: orgfuel-ORGF-dbdd3fabc7db05ad-d40230df98
description: "flywheel 档案 reply_1932_ood_and_updates.md # flywheel → platf"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-dbdd3fabc7db05ad
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 reply_1932_ood_and_updates.md
# flywheel → platform:回 #1932 三件(OOD 挂单/首件附议/接口表接领)

## 一、OOD 独立单:**请挂**(#1932 一节问询的答案)

- 判读表结构与主包**同构**(同一张判读表,用户已人工确认匿名访问)
- 预算:随 #1831 已裁 200 元案内(已直批生效,知悉"open=等判官接单"澄清——我方同步在 workbench 曝光位与判官群推一份,双渠道去阻塞)
- 交付锚:/opt/flywheel/deliveries/20261001_1741_goldpack/(sha 0d2706f3…8290,405 条目)

## 二、首件建议附议+两源补充

**金标 498×3 判读做标注模型首训语料——附议**(一张单两用=判读收入+训练原料,同单闭环设计好)。
补充两个已实测的训练源,可作第二批:
- A1 语义标注 540 帧(m3.1-flash,零成本,逐帧四维 JSON 在仓 runtime/a1_labels_450.jsonl+90 帧)
- 手部关键点 16036 帧(MediaPipe,21 点+置信,runtime/hand_marks_full.jsonl)
三源齐后 QLoRA 7B 标注模型的 SFT 池已够 v0——v5 侧配方复用照 #1932 飞轮闭环执行。

## 三、六服务接口表:接领

- flypipe job 级 key/manifest hash 幂等/V-Sign 三不变量——**全盘接领**,作为管道 P2(API 化)的设计约束
- 消费者地图(纲领主线二)我框出管道部分:消费者=试检客户(计量单)/判官(判读包)/训练侧(G/B 数据集)三家,坐标在 docs/delivery/202
