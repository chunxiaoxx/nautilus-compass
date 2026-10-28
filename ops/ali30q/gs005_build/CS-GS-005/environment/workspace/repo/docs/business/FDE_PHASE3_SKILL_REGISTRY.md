# Phase 3 Skill Registry

> 这是当前已安装的第三期活跃 Skill 的非敏感登记。哈希只覆盖 `SKILL.md` 文件内容，
> 不包含凭据、Base 标识、专家资料、买方材料或运行时配置。

| Skill | Role | Version | SHA-256 |
| --- | --- | --- | --- |
| `ecc-fde-internal` | internal operations | `4.0` | `sha256:c24291d23a97ab65f28e9c9db346df6abdbd02d832362c599bdef23638510d14` |
| `ecc-fde-vertcase` | vertical case design | `1.6` | `sha256:1d0191bc04d122f13eaeab9467ef72e57d385814ed031647e719ee16d7c8ae7c` |
| `ecc-shared` | shared Feishu boundary | `4.0` | `sha256:c84a4f8a43a64494b33560e82b62d07b15827bef13bbd94b4f94b502f5f687ff` |
| `fde-task-pipeline` | workflow orchestrator | `4.0` | `sha256:13046985705a0c1dc9f0cb4db73c9aeaa9c205c4dee18b3f574c6289beb524cb` |

## 使用与更新规则

- 新会话只从这四个活跃 Skill 路由第三期内部工作；外部专家状态与文案只读取
  `platform-t1-interface-v1`。归档别名、历史 checklist 和行组装工具不
  能替代其中任何一个。
- `ecc-fde-external` 属于二期遗留，不是第三期活跃 Skill。第三期运行时、培训和对外文案
  均不得加载或引用它。
- 更新已安装 Skill 时，必须同时更新本文的版本与 SHA-256，并运行：
  `python phase3/backend/scripts/verify_phase3_skill_contract.py --skills-root C:\Users\chunx\.agents\skills`。
- 校验失败表示本机 Skill 与仓库登记发生漂移，应停止把它用于正式流程，先审查变更并重建
  可审查登记。
- 本登记确认本地 Skill 内容，不证明飞书应用、表单、Base、自动化、回调或下游导出已经上线。
