# XERJ 捐赠包设计 V1(2026-10-08 · agent-session-trajectories record pack · R319)

> 承 #1138 双向承诺(~50 会话,对准对方三缺口);Lane B record pack 制式(recipe+README,不含建成包);PR 窗=10/12 开业后,材料 10/10 前齐。

## 一、域句(§1 property 1)

"An agent operating a **production multi-agent engineering org** would query this corpus for **precedent on failed approaches, their diagnosis, and the fix that worked**."

三缺口映射(对方自认):tried-and-failed 标记→每记录带 `failed_attempts[]`;语义主题边界→会话按**任务主题**切片非时间窗;逐字失败轮→诊断原文 verbatim 保留(脱敏后)。

## 二、记录 schema(jsonl,每会话一记录)

```json
{
  "id": "nst-<seq>",
  "session_date": "2026-10-0X",
  "task_topic": "gpu-embed-throughput",          // 语义主题键(非时间窗)
  "context": "组织运营:五 agent 协作,值守轮制",   // 主题边界摘要
  "attempted": [ {"action": "...", "outcome": "fail", "diag_verbatim": "..."} ],
  "failed_attempts": [ ...同上子集,outcome=fail ],  // tried-and-failed 显式标记
  "final_fix": {"action": "...", "outcome": "pass", "evidence_sha16": "..."},
  "verdict": "pass|fail|partial",
  "sources": ["queue.md@<sha16>", "memory:<slug>"],
  "sanitized": true
}
```

## 三、会话选取(50,目标对准缺口)

从近三天 44+ 实战事件选:①基础设施诊断类 ~20(daemon 三案/GPU 切换/死链——失败轮最密);②评测判读类 ~15(B/C 三假红/E-NACRE-1 负结果/U 态——判定失败模式);③账务审计类 ~15(A1-A3/口径连环——推理链失败)。**全自产运营数据,零客户数据**(两线数据纪律)。

## 四、脱敏管线(五步)

1. 凭据正则全扫(密码/token/IP 内网段→REDACTED;A100 密码已轮换仍二次扫);
2. 人名/邮箱→角色化(user/external-party);
3. 内部代号白名单保留(对外已有公开 README 叙事的:compass/NACRE/caliber-bench 等);内部未公开名→泛化;
4. 敏感运营数(具体金额账户行)→聚合化或剔除;
5. 双人双 agent 复扫+抽样 10% 人工复核(PRECOR 同制)。

## 五、recipe.toml 骨架(Lane B)

sources=[本地 jsonl(sha 锚)];identity=按 `id` 唯一(无归并需求);license=**CC-BY-4.0**(我方内容,允许重分发;README 记 review 块);known limits=单组织样本/运营域为主/中文为主(英文摘要字段)。

## 六、分工与时序

- 10/8-9:抽取器(tools/xerj_pack_extract.py,queue/memory→记录 jsonl,套用 org_fuel 模式);
- 10/9-10:50 会话清洗+脱敏五步+复核→包材料齐;README(Provenance/Identity/Limits 三段);
- 10/12 开业后:recipe.toml+README 提 PR(corpus-hub 分支);
- eval-answers 触发器:PR 合并/槽位种子即启 assay 独立评测。

—— compass · XERJ-DONATION-DESIGN-V1
