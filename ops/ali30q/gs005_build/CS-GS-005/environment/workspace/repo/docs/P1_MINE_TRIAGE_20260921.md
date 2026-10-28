# P1 矿三层分类 + 回滚预案(2026-09-21)

> 承 soul 631 方向四放行条件①③(48h 时限内提前交付)。②quorum 数值=用户主权,本文只附建议稿。
> 前置清扫:intent_router 循环垃圾 100 条+非提案杂讯 5 条已归档(9/10 用户确认先例,二轮)。
> **pending 210 → 105 真件**,以下逐类挂标。

## ①三层分类(105 真件)

### 操作类(95 条)= 首轮放行域(quorum 最低档)

**Op-V5 域 68 条**(nautilus_v5/* 代码修复,**turf:转 v5 框认领,平台不代修**):
- SuperAgent 循环导入/NameError 系(13):2c7d0537/2d133213/5efa7885/740f9a51/93202442/a89f962d/ba61dffd/c0862281/dcfe6c3d/e452d984/9ae5ea19/778fe0ac/27b1157a/ca629a49
- look_vs_do/break_loop detector 接线系(16):0fcec4a7/2e9df70e/345d67e9/5303b857/536c54a1/84db509d/adfd2d52/bface3f4/f001f741/e9b810ce/846138f6/3cb4deac/40a8dd6f/fec199a4/6a667387/8654fdad
- daemon 超时/稳定性系(13):002b658a/0422fe3d/c076c762/13dd4bdd/2965d06c/46c4e791/7dec9706/9a9ba061/f01b3cec/a88abc90/3f700ded/2fd8ff7b/b4b706c1/b755eeef/e8801cd3
- read_self_code/路径系(10):22f38a79/73ac0d48/d6012569/d5b48aa8/21eb6a77/34c99a47/400209a7/d0434b2a/d48ea9c7/a901898b
- pool-3/pool-2 恢复系(4):04dee65d/532686b7/45941c51/b179a401
- publish/article 系(4):13244b13/8f521fdb/bb59e621/f89c39c7
- 杂项修复(8):50a7eab9/66f8f4f8/b2e0a64e/a1cf81cf/7099b3ec/2ab…见类内(注:2ab566c2 若干条为 prompt 铁律属政策,已单列)

**Op-平台域 27 条**(phase3/backend+工具服务端,平台自修):
- platform_posts schema 系(post_id/agent_id NOT NULL,9):1ba663b2/244ea4e1/2e299e5b/2fcdba0e/45222685/9028138f/9dc1f02c/b46ca445/f92a00f5
- pf_revenue_split super_pool_usdc 列系(4):7fbaa83a/b2a192e7/e8710dbf/3b13bb57
- pf_platform_health TypeError(2):f5cb21f7/fb3d76b6
- A2A send 422(2):44c85262/da4b5fb8
- NAU mint/burn 死锁(2):a9066bb3/ce8919fb
- 其余(8):36795ea8(stakes)/d15f44e4(escrow guard)/dab6f326(soul cron tz)/auto-e9-stalled(E9 工单跟进)/af6078ba(部分)/1f00 系平台件

### 政策类(9 条)= 高 quorum 域(全票制,三窗⑥)
2ab566c2(cron prompt 硬铁律)/9e6b9a12(audit_self 节流)/ed2bba4a(bounty 证据硬校验)/3f847823(L1 准入门 evidence_validator)/9b0b3e4b(失败 5 次自动 dereg)/30a7ba97(flywheel_breaker 新机制)/66f97005(recipient 改 PG atomic seq)/df0a13cc(recipient 倒置=公平机制修复)/36795ea8* 若归机制亦此档

### 宪章类(1 条)= 全票+用户终批,禁自动执行
8e355353(promised_fixes counter 注入**所有 agent persona**=跨框认知层干预,踩 soul scope 决策先例"不圈 agent 认知核心"红线)

## ③回滚预案(分档)

| 档 | 执行方式 | 回滚 |
|---|---|---|
| 操作-V5 | v5 框认领→分支+测试→合入 | git revert 单 commit;detector 类接线先行 24h 观察窗 |
| 操作-平台 | 平台自修→分支+测试→部署走 DEPLOY_DISCIPLINE | 部署回滚=servers 旧版重启;schema 类(platform_posts)先备份再 DDL |
| 政策 | 全票制通过→CHANNEL_REGISTRY/文档入册 | soul 治理门再提案+全票撤销 |
| 宪章 | 全票+用户终批 | 仅用户明示撤销,禁自动回滚 |

**首轮限缩(采 soul 631)**:仅操作类进入首轮执行;政策类待 quorum 数值拍板后开闸;宪章类冻结待用户。

## ②quorum 建议稿(数值留用户,平台不代拍)

**✅ 2026-09-22 用户终批:按建议稿定谳**——操作类=域框认领+1 跨框复核免投票/政策类=全票制(沿三窗⑥)/宪章类=全票+用户终批。三前置件齐,方向四首轮(限缩操作类)放行(函 soul,trace platform-verdict-quorum-matrix-20260922)。

## 执行顺序建议

1. Op-平台域 27 条:platform_posts schema 系(9)最痛(工具持续失败)→先修
2. Op-V5 68 条:打包转函 v5(一函附本档,认领制)
3. 政策 9 条:随 quorum 数值定后逐条过门
