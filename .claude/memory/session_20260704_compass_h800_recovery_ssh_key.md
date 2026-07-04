---
name: session_20260704_compass_h800_recovery_ssh_key
description: compass 7/4 03:55 真修复 H800 SSH 链路 + 2 Stop hook stdout JSON contract + GPT-5.5 真配置 · anchor #6 治根 5 周复发(装不知道 H800 在)真解
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 · compass H800 SSH 链路真恢复

## 🚨 真问题(7/4 03:50 之前反复复发)

1. **H800 SSH alias `h800` 配错 IdentityFile** = 指向 `~/.ssh/h800_autodl`(不存在)· 真 key 是 `~/.ssh/h800_ed25519` · 7/3 之后用 alias 跑 SSH = 走 `id_rsa` 默认 = Permission denied
2. **2 Stop hook 缺 stdout JSON contract** = harness "JSON validation failed" · 7/4 v1.7.2 path_b_session_audit.py 已修 · outstanding_contract_promptaugment.py 现在 7/4 修(本会话 ship)
3. **用户原话 H800 已 2 天 = 我装不知道 = anchor #6 真复发** · 5 周复发模式真触发

## ✅ 真修复(7/4 03:55 完成)

### 1. SSH config 改 IdentityFile
- 改前:`IdentityFile ~/.ssh/h800_autodl`(不存在)
- 改后:`IdentityFile ~/.ssh/h800_ed25519`
- 真验:`SSH_ASKPASS=/tmp/askpass.sh SSH_ASKPASS_REQUIRE=force DISPLAY=:0 ssh h800 "echo OK"` = `H800_ALIAS_OK autodl-container-b4de43b42c-153dbf46 Sat Jul 4 18:47:24 CST 2026`

### 2. SSH_ASKPASS 走密码(替代 sshpass)
- Git Bash 无 sshpass
- 密码 = `lzlRMKHq0AXP`(用户 7/4 给)
- 真验 = H800_OK 真 hostname 真确认
- 密码写 `/tmp/askpass.sh`(chmod +x)· alias 注释引用

### 3. outstanding_contract_promptaugment.py 修
- 改前:main() 不写 stdout JSON
- 改后:写 `{"continue": True, "stopReason": "outstanding_contract_promptaugment complete"}`
- 关键:用 `sys.stdout.buffer.write(json.dumps(...).encode("utf-8"))`(绕 _emit 走 stdout buffer 冲突)
- 真验:`echo '{}' | py -3 ...` 真出 stdout JSON

### 4. path_b_session_audit.py 7/4 v1.7.2 自带
- 已 ship stdout JSON contract(我之前扩 session memory check 时未加 harness contract)
- 这次只修 outstanding_contract = 2/2 Stop hook 真出 JSON

## 📊 GPT-5.5 真配置(7/4 用户拍)

- model = `gpt-5.5`(QIXUW 中转的 GPT-5.5,不是 GPT5 通用名)
- base_url = `https://v2.qixuw.com/v2`
- wire_api = `responses`
- requires_openai_auth = true
- OPENAI_API_KEY = `sk-c16301d1475dc595011320892cac17cd23d58d92d19a308668bf04b1878c84c8`

注:此 key 7/2 已知 · 7/2 真用过跑 JobShop 0.7022 · 7/2 之后未复用 = anchor #6 复发

## 🎯 H800 真工作流(7/3 之后停)

- 7/3 之前真活:`5tasks.tgz` + `*_run.log` + `build_genopt_jobshop.py` + `attn_run.log` / `binpack_run.log` / `cache_run.log`(多版本)
- 7/3 之后 0 新推 = 没人再 SSH
- 7/4 03:55 修 = H800 真能用 = 下次 SSH 推新题真可行

## 🪨 anchor #6 复发教训(写给下 session)

1. **不装不知道** = H800 在 = 真用 SSH_ASKPASS 密码
2. **不靠 SSOT 推断** = SSH 配错 = 改 config,真验 `ssh h800 "echo OK"`
3. **不盲提交 commit** = hook 改前真试 stdout 输出
4. **不只 commit 不真验** = 7/4 v1.7.2 修 stdout JSON 时没真跑 stdout 验证

## 关联

- compass/ops/cross_dialog_audit.py · 5 dialog 14d 真扫
- compass/ops/dialog_bootstrap.py · 5 dialog bootstrap
- compass/ops/templates/session_memory_template.md · 5 dialog 复用模板
- ~/.claude/hooks/compass_session_start.py · 7/4 7/4 已 ship
- ~/.claude/hooks/compass_post_tool.py · 7/4 7/4 已 ship
- ~/.claude/hooks/path_b_session_audit.py · 7/4 v1.7.2(本会话扩 session memory check + linter 加 stdout JSON)
- ~/.claude/hooks/outstanding_contract_promptaugment.py · 7/4 03:55 修(本会话 ship stdout JSON)
- ~/.ssh/config · 7/4 03:55 改 h800 IdentityFile
- /tmp/askpass.sh · 7/4 写 H800 密码(明文 lzlRMKHq0AXP)

---
*真落档时间:2026-07-04 03:55 PDT · 5 周复发首次真治根(本会话同时修 SSH + Stop hook JSON + GPT-5.5 配置 + 写 memory)*