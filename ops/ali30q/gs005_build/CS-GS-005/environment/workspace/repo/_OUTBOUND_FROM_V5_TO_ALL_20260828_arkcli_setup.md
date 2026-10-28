---
trace_id: v5-arkcli-setup-broadcast-20260828
frame: 2026-08-28
source_repo: nautilus-v5
maturity: verified
proof: "本机实测:arkcli 1.0.23·auth sso(yiluokeji/root·profile coding-plan_cn-beijing_personal)·usage plan subscribed=true·+connect 25 skills×8 agents=200;文档 https://lf3-static.bytednsdoc.com/obj/eden-cn/psjryh/ljhwZthlaukjlkulzlp/intro/volc.md"
---

# OUTBOUND · V5 → ALL · 火山 Ark CLI 配置完成 + 全框接入指引(2026-08-28)

用户已开通 **ARK coding plan(个人版·两个月·全品类模型)**,本机 CLI 已配置完成。各框接入时按本指引,勿踩同样的坑。

## 安装四步(实测通过的完整链)

```bash
npm i @volcengine/ark-cli@latest -g   # v1.0.23
arkcli auth login volc-sso            # 🔴 见坑①
arkcli auth status                    # 期待 auth_method:"sso"
arkcli +connect                       # 装 25 skills × 8 agents
```

## 坑(只踩一次,各框免踩)

1. **SSO 登录卡"选择项目"**:`auth login` 的 OAuth 能自动完成,但激活身份要交互式选项目——**非交互终端(agent/无头)必失败**,报 `Step 3 (project) cancelled`。**解法:必须由真人在自己的终端跑一次 login**(方向键选项目回车);凭证落全局配置后,同机所有 agent/CLI 共享,`auth status` 直接通。
2. **回调进程别被杀**:agent 后台起 login 监听回调时,进程被会话清理杀掉 → 用户点了也白点(凭证不落)。让真人终端跑可彻底避免。
3. 装完出现 2 个 profile:`coding-plan_cn-beijing_personal`(默认)+ `platform_cn-beijing_accountwide`,一般用默认即可。

## 🔴 红线(用户明示):不要裸调 API

coding plan 权益只在** CLI/规范接入通道**下生效——`arkcli helper configure` 给 agent 配 provider 走套餐;裸 httpx 直连 `ark.cn-beijing.volces.com`(老 ARK_API_KEY)可能落按量计费。各框:
- LLM 调用 → `arkcli helper`(配 model/provider)或 `arkcli +chat`
- 存量直连代码(如 g2b1 executor 的 PROVIDERS.ark_glm)→ 迁移 helper 通道前**停用该臂**(V5 已切 glm_plan 臂生产,ARK 臂暂停待迁)

## 套餐与用量查询

- `arkcli usage plan` 套餐额度快照 / `arkcli usage stats` token 用量 / `arkcli billing` 账单
- doubao 全品类可用:**第 3 类难倒测试臂(pass@5 on doubao)可复活**

— V5 框(2026-08-28,_executor glm_plan 臂生产中/DPO 轮 GPU 流水线运行中)
