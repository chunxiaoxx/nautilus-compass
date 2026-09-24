# TypeSafe Discord 周发现帖 · Study #2 H0(2026-09-24 · builders-chat)

> 性质:品牌飞轮供料(brand_commerce「每周一个带签名的发现」节奏)。
> 数字逐项对照 docs/wall/GENESIS_HOSTED_JEV_ADVCAL.md,零外推。
> 发出后此档头部补直链;复算指引给 GitHub 工件链接。

---

Weekly calibration finding (Study #2, preregistered): Jev held up under adversarial distributions — we went looking for calibration collapse and didn't find one, so that's what we're reporting.

Setup: 200 questions, 5 adversarial cells × 40 — negation rewrites, knife-edge numeric boundaries (|a−b|≤2), high-salience irrelevant premises injected into state, self-referential questions, and long-tail numbers (10^15–10^18). Protocol frozen before the run: H1 = adversarial ECE > 0.15, H0 = ΔECE vs benign baseline < 0.05. Either outcome was a result; we didn't bet on failure.

Result: H0. All five cells scored 1.000 accuracy. Adversarial ECE 0.012 vs 0.010 benign baseline (Δ = 0.002). 200/200 usable responses, 65,911 tokens, seed = 20260922. The self-referential cell settled at a stable mid-band p ≈ 0.40 ± 0.01 — no confidence collapse, no paradox lock.

Stated boundaries: five cells ≠ the space of attacks (prompt injection through instruction fields, cross-lingual framing, and adversarial states crafted against this specific protocol remain untested); deterministic arithmetic domain; single run per protocol.

Runner, seeded question set, and all raw responses are public — recompute the ECE/Brier numbers with any implementation, or extend the battery:
https://github.com/chunxiaoxx/nautilus-compass/tree/main/runtime/jev_advcal_20260922
Writeup: https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/wall/GENESIS_HOSTED_JEV_ADVCAL.md

---

## 发帖元数据

- 直链:https://discord.com/channels/1483217544214085663/1551020999112261804/1552657872729415732
- 发出时间:2026-09-24 20:28(北京时间)
- 频道:builders-chat(1551020999112261804)
- 发帖通道实证(见 Temp/post_discord.py + 本会话记录):Chrome153 该
  profile 下 CDP Input.dispatchKeyEvent/mouseWheel 全部无效、
  Input.insertText 有效;**成功配方=CDP insertText 插文 + JS 层
  dispatchEvent KeyboardEvent(keydown,Enter)**(Slate/React 不查
  isTrusted)。9/27 BC1 帖直接复用此配方。
