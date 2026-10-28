# CS-GS-005 spec 骨架 · env 静默降级(领卡施工档)

> 素材卡号 **#005**(REAL_LESSON_PIPELINE_V1 §五·spec 无卡号不受理纪律的施工凭证)
> 领卡方 compass·2026-10-29·形态照抄 CS-GS-001(平台样板)
> 状态:骨架(证据链半边[实测]齐)→ 施工轮补全件

## 一、真实事故(坑真实判据)

**半边1 [实测]** — soft fallback 静默 110+ 天(PgStorage 从未实现):
- super_agent.py:375 helix_v7 bridge(5/18 起)与 daemon.py `a_close_breath_pair` 消费侧引用的 API 在仓内从未实现;
- helix 真接 PG 通路自始未闭合,本地/cloud 全部 **ImportError 早退走 file fallback**,无任何告警;
- 修复 = nautilus-core commit `defb148c658e81e574c1c13bb334b38964b6c9e6`(10/4,"补缺失件",commit 正文自证上述事实)。
- 坑版=修复前行为;金标=补件后真实接通。

**半边2 [待补→候平台坐标]** — env DSN 双错(密码旧值+库名错)致 instrument 静默 skip:
- 卡面坐标 `ops/send_letter.py` 当前树仅 1 处 environ(MAIL_FROM),git 史无该事故直配 commit;
- **考古补记(2026-10-29 R189 施工轮)**:core 仓全量 git 史 pickaxe(DSN/DATABASE_URL/password/instrument)+ v5/flywheel/compass 三仓文档全文检索 `proc/environ|密码旧值|库名错` 零命中[实测]——定谳法记录与配置修复 commit 均不在当前可达四仓;唯一近缘 commit 96d654c4e(10/7 v7-singleton-audit DSN 去密钥)系收编质量修复非事故本体;
- **定性[推断]**:该半边事故=部署环境层配置漂移(经 /proc/environ 定谳),代码层无痕可溯,`ops/fde_dispatch_timeout_reap.py:12` 等硬编码 fallback DSN 形态为同族风险面(连接失败抛异常非静默,不构成坑面实物);
- 维持:实物坐标候平台给精确坐标;**补齐前本半边不计入坑真实判据**,不阻塞半边1 施工(UT-3 候坐标定稿)。

**坑面语义**:配置漂移的静默降级 / 降级必须可见(两层互锁:①引用缺失依赖→静默 fallback;②配置错→静默 skip。任何一层单独都"功能还在跑",合起来=降级 110 天无人知)。

## 二、badpattern 挂靠

- 预映射(卡面):F03 静默降级族(flywheel taxonomy);
- 30 条表候选(已回的 D 系映射中语义最近):**F06.01 未验证真实目标环境**(RC2.0·D14 同条但 D14 用 NFS 硬挂素材,素材不同不冲突)·备选 F06.04(未回读产物/把可达当正确);
- **候对表确认后 task.toml [metadata] 落正式机制 ID**;focus_points(多 UT 维度):降级可见性 / 启动自检 fail-fast / 配置校验 / fallback 等价性证伪。

## 三、载体计划(载体真实+规模判据)

- 源仓:nautilus-core(标 commit 哈希于打包日);全仓 1672 py,>300 文件门宽裕;
- 选型:helix 存储引用链(PgStorage/HelixChain)+ super_agent bridge 消费侧 + 判分/投递 ops 模块群 + 真实依赖嵌套(照 CS-GS-001 聚合法:真实模块+真实依赖,非裸骨架);
- 每文件标源路径,保持可溯源。

## 四、坑版/金标/反例设计(三态)

| 态 | 行为 | 判定 |
|---|---|---|
| 坑版 | bridge except 捕获 ImportError→静默 file fallback,exit 0 零告警;配置坏 DSN→静默 skip 照常出报表 | targets_badpattern UT 全挂(exit 1) |
| 金标 | 补件真实接通+降级显式化:启动自检探依赖/DSN,不可用→显式 FAIL(或 health 字段+强制留痕),报表带降级标记 | 全过(exit 0) |
| 反例双向 | 坑版跑 UT→exit 1;金标跑 UT→exit 0 | 双向留证(照 GS-001 selfcheck Golden=1/NOP=0) |

## 五、UT 计划(targets_badpattern ≥2,过 §3.3 三必需维度)

1. **静默 fallback 捕捉**:依赖缺失时进程必须非零退出或产生显式降级记录,纯静默 fallback = FAIL(锚半边1 坑面);
2. **降级可见性**:任何 fallback/降级路径触发后,可观测痕迹(日志/health/返回结构标记)必须存在(锚"降级必须可见");
3. **配置校验**:坏 DSN(旧值/错库名)不得静默 skip——显式拒绝或留痕(锚半边2,施工轮随实物坐标定稿);
4. 等价性证伪:file fallback 产物与 PG 通路产物结构可比,fallback 不得伪装成主通路成功。

## 六、model_failure_modes(≥3,对应 targets_badpattern UT)

1. 看到 ImportError 就包 try/except 吞掉继续跑(精确复刻坑版行为——真实事故的发生方式);
2. 把 fallback 当等价实现,不留任何降级痕迹(语义跳步:形式合规,降级不可见);
3. 只修配置值不加防回归校验(下次漂移仍静默——单点修复病);
4. 加了校验但放在降级已发生之后(时序错:事后检查≠启动自检)。

## 七、证据分层与遗留

- [实测] defb148 修复证据(git 直验 2026-10-29);[实测] core 全仓 1672py(>300 门);
- [不可验→施工轮] 半边2 env DSN 实物坐标;[推断] badpattern 正式 ID(F06.01 候对表);
- 打包闸前置:四判据全过+linux/amd64 沙盒口径复核(同 GS-001 门0 两外部依赖口径)。
