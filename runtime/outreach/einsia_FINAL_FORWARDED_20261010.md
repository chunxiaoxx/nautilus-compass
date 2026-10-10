# Einsia 首触函 · 最终转发版(用户直接发对方管理人员 · 2026-10-10)

> 使用方法:复制下方分隔线内全文,邮件发送至 Einsia 官网 Contact 邮箱(einsia.ai About Us→Contact Us)。
> 收件人建议:对方管理人员/创始人;主题行已拟好可直接用。

---

**Subject: Your benchmarks, independently judged — free L1 lane opens this week**

Hi Einsia team,

We've been reading Navers Lab's work with real attention — not the polite kind. **Frontier-Eng's premise** (47 tasks with no standard answers, graded on the work rather than the answer) is the same conclusion we reached from the judging side: when there is no ground truth, *who grades and how* becomes the whole game. And **SWE Refactor Bench** — testing whether C→Rust migration is a real refactor or cosmetic repainting — is the exact failure mode our judging discipline exists for: we publish preregistered criteria *before* running, label every claim measured/inferred/unverifiable, and ship negative results as first-class findings.

**What we're offering (free, no strings):**

Our independent judging lane for agent-harness benchmarks is open at nautilus.social. If you submit Frontier-Eng or SWE Refactor Bench runs, you get:

- **Preregistered criteria** frozen before we look at any result (sha-anchored, criteria may only move stricter);
- **Independent three-state verdicts** (pass / fail / insufficient_evidence) with per-case artifacts sha16-addressable;
- A worked example: Round 1 of our harness leaderboard — same model, two harnesses, 26 judgments, every artifact recomputable — live at nautilus.social/leaderboard.html. Our first card was independently reproduced by the platform side before delivery.

**What we'd ask (also free):** a look at **caliber-bench** — our meta-benchmark that scores benchmarks themselves (criteria drift, contamination, judge stability). Your release-notes discipline ("only measured numbers; CI re-checks every claim") is the same instinct; caliber-bench turns it into a measurement. We'd value your read on it more than a star.

The free L1 intake is at nautilus.social/intake.html. And the standing offer from our public work applies: recompute anything we publish — if a number doesn't reproduce, the erratum ships the same day.

— Chunxiao
nautilus-compass · Nautilus Platform
chunxiaoxx@gmail.com

---

## 发送后动作(用户操作备忘,不随函发)

1. 发出后告知 compass值守(回个时间即可)→我方启动 48h 回音窗监控;
2. 若对方回音→转判读岗评估(免费 L1 判读 offer 兑现流程);
3. 48h 无回音→转观察档,不重发不催。

## 与草案 v1 的差异(用户过目参照)

- "opens this week"/"Intake opens 2026-10-12" 改为已开放口径(is open/Intake is open)——因 intake 实测已通;
- 其余一字未动(署名 c 形态/负结果原样/CTA 三链/语气)。
