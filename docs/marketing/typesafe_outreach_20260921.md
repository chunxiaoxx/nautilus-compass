# TypeSafe 外联函(草稿 · 待用户过目后发)

> 渠道建议(用户定):①GitHub org TypeSafeAI 任一活跃仓 issue(SDK 仓最合适,
> 可公开可追溯)②网站联系邮箱双投。冷却纪律 72h。
> 核心切入:模仿者已现(imposter 网关)→「calibrated」声明稀释 → 买家无法
> 分辨 → 第三方验证回执=真 Jev 的差异化。姿态:agree 是礼物,不树敌。

---

**Subject: Third-party verification layer for Jev calibration claims — already built, already live on NanoJev**

Hi TypeSafe team —

Congratulations on launching Jev and System One Models. We run **Nautilus Assay**, an
independent verification service for AI-agent performance claims (signed ed25519
receipts, three-state verdicts, open CC-BY protocol, criteria catalog with ratchet-only
revisions).

**Why we're writing — the dilution problem arrived within your launch week:**

Your product narrative is *calibration* (typed decisions with calibrated probabilities,
RLCD). That's exactly right, and it creates a knock-on effect: every downstream product
built on Jev — via your API or gateways like Requesty — will now tell *their* customers
"our decisions are calibrated." We counted three community awesome-jev directories and
an MCP connector within days of launch… and at least one third-party gateway already
advertising itself as an "imposter Jev" that mimics your structured output. When the
word "calibrated" spreads faster than the ability to check it, buyers lose the ability
to distinguish real calibration from mimicry. That dilution lands on your narrative.

**We built the checking layer, and it's already live on your ecosystem:**

- An open criterion for calibration claims (Brier/ECE recomputable on public holdouts —
  calibration claims are safety claims when controllers consume thresholds)
- A `calibration` verification engine (per-sample predictions → independent Brier/ECE
  recompute), shipped this week in our open tooling
- Receipts with subject fingerprints (key/code/config — a changed model is a new
  subject) and 90-day TTL: expired = unverifiable until re-verified

And we've already fired it three times on the Jev ecosystem — the independent nano
replica **NanoJev**: six README claims AGREE, frame-level trajectory replay AGREE, and
last night a **full replay of its calibration benchmark: 15 metrics, max deviation
1.99e-08, across torch versions, OSes, and devices.** Receipts signed and public:
https://github.com/chunxiaoxx/nautilus-compass/tree/main/docs/wall

**Three ways to plug in, lightest first:**

1. **Reference**: link our open protocol from your docs as "how to independently verify
   a calibration claim." Zero cost, zero lock-in — the protocol is CC-BY and the SDK
   (`pip install assay-verify`) is zero-dependency; signatures verify without trusting us.
2. **First-party receipt**: publish an official holdout + predictions file for a Jev
   model; we run the first third-party calibration verification and hand you a signed
   receipt. Free. If it agrees, it's a gift; disagreements come to you privately first
   — we are not in the shame business.
3. **Ecosystem layer**: a "calibration-verified" tier for downstream Jev products —
   the way to make *real* Jev-built systems distinguishable from imposters before the
   word dilutes further.

No relationship assumed, no exclusivity asked. Our teeth are public: misjudgments earn
OVERTURNED verdicts + refunds + challenge costs (protocol §5b).

Happy to demo any of this in 30 minutes, or just send the receipts and let the
signatures talk.

— Nautilus Assay (伊洛科技有限公司 / Yiluo Technology)
   https://compass.nautilus.social/wall.html · github.com/chunxiaoxx/nautilus-compass
