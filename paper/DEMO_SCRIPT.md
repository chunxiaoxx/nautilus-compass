# Compass v0.9.0 — 5-Minute Demo Screencast Script

**Target**: Announcement video for HN / X / Reddit launch
**Duration**: 5:00 (300s)
**Format**: Screen recording + voiceover (bilingual EN/中文)
**Hero shot**: Cross-agent memory federation (Claude Desktop ↔ Cursor)

---

## Section 1 — The Problem (0:00–0:30, 30s)

### Screen
- Split screen, two terminals side by side:
  - **Left**: Claude Desktop chat — user types `"please be concise"` → assistant: "Got it, I'll keep replies short."
  - **Right**: Cursor chat — same user asks "summarize this PR" → Cursor replies with verbose 8-paragraph wall of text.
- Overlay text: `claude-mem stores Claude's memory. Cursor doesn't see it. ❌`
- Cut to a diagram: 5 boxes (Claude Desktop · Cursor · ChatGPT · Cline · Codex) each with a private 🔒 silo, no arrows between them.

### Voiceover
- **EN**: "You taught Claude Desktop you prefer concise answers. But the moment you switch to Cursor, that lesson is gone. Every agent is a silo. That's the memory problem nobody's solved — until now."
- **中**: "你告诉 Claude Desktop 你偏好简洁回复。一切到 Cursor 全部归零。每个 agent 都是孤岛。这是没人解决的记忆问题——直到现在。"

### Visual cues
- Red ❌ pulse on the silo diagram (1.5s).
- Title card fade-in at 0:25: **"Compass — cross-agent memory federation"** (white on black, lowercase).

---

## Section 2 — Setup Claude Desktop (0:30–1:30, 60s)

### Screen
1. Open `~/Library/Application Support/Claude/claude_desktop_config.json` in VS Code.
2. Paste the MCP block (highlight the new lines):
   ```json
   {
     "mcpServers": {
       "compass": {
         "command": "npx",
         "args": ["-y", "@nautilus/compass-mcp"],
         "env": { "COMPASS_USER_ID": "alice@example.com" }
       }
     }
   }
   ```
3. Restart Claude Desktop.
4. In Claude Desktop chat, type:
   > "Remember: I prefer concise replies. No filler. Use compass.write to save this."
5. Claude calls `@compass.write` — show the tool call panel expanding with the JSON payload `{ "text": "user prefers concise replies, no filler", "tags": ["preference", "style"] }`.
6. Response: `✓ stored · id=mem_8af3 · scope=user:alice@example.com`.

### Voiceover
- **EN**: "Step one: drop the Compass MCP server into Claude Desktop's config. One block, six lines. The `COMPASS_USER_ID` is your federation key — anything sharing this ID sees the same memory. Now I tell Claude my preference, and it writes it to Compass. Done."
- **中**: "第一步:把 Compass MCP 加到 Claude Desktop 配置里。六行。`COMPASS_USER_ID` 是联邦的钥匙——同 ID 的客户端共享同一份记忆。然后告诉 Claude 偏好,它写入 Compass。结束。"

### Visual cues
- Yellow highlight box around the `compass` MCP block as it's pasted (hold 3s).
- Green ✓ flash on `mem_8af3` when the write succeeds (zoom 110%).
- Lower-third caption at 1:15: `1 user_id = N agents · same memory`.

---

## Section 3 — Recall in Cursor (THE MONEY SHOT) (1:30–2:30, 60s)

### Screen
1. Switch to Cursor. Open `~/.cursor/mcp.json`. Paste the **same** `compass` MCP block, **same** `COMPASS_USER_ID=alice@example.com`.
2. Restart Cursor.
3. New Cursor chat. Type:
   > "What style does this user prefer? Use compass.recall."
4. Cursor calls `@compass.recall` with query `"user style preference"`. Tool panel expands.
5. Result returns:
   ```
   ✓ 1 hit (similarity 0.91)
   id=mem_8af3 · "user prefers concise replies, no filler"
   source=claude-desktop · written 47s ago
   ```
6. Cursor's reply: "You prefer concise replies — no filler. Got it."
7. Cut back to Claude Desktop briefly, recall the same memory there too: same `mem_8af3` returned. Federation confirmed.

### Voiceover
- **EN**: "Step two — and this is the whole point. I open Cursor. Same MCP block. Same user ID. I ask: what does this user prefer? Cursor calls `compass.recall` — and pulls back the memory I wrote in **Claude Desktop** thirty seconds ago. Different agent. Different vendor. Same brain. This is cross-agent federation, working live."
- **中**: "第二步——重点来了。打开 Cursor。同样的 MCP 块。同样的 user ID。问它:用户偏好啥?Cursor 调 `compass.recall`——召回我刚才在 **Claude Desktop** 写的那条。不同 agent。不同厂商。同一份记忆。这就是跨 agent 联邦,实时运行。"

### Visual cues
- 🔥 BIG callout at 1:55 when the recall returns: red box around `source=claude-desktop`, hold 4s.
- Slow-mo / zoom on the similarity score `0.91` (zoom 130%).
- Side-by-side at 2:20: Claude Desktop and Cursor both showing `mem_8af3` — connect with an animated arrow labeled "shared memory".
- Lower-third: `Cross-agent federation · LIVE`.

---

## Section 4 — Drift History (2:30–3:30, 60s)

### Screen
1. Stay in Cursor. Type:
   > "@compass.drift_history days=30"
2. Tool returns ASCII timeline (monospace, full width):
   ```
   compass · drift_history · user=alice@example.com · last 30 days

   apr 06 ▁▁▁▁▁▁▁▁  green   stake 0.42 · 12 writes · 0 contradictions
   apr 13 ▁▁▂▁▁▁▁▁  green   stake 0.45 · 18 writes · 1 minor edit
   apr 20 ▁▂▃▂▁▁▁▁  yellow  stake 0.51 · 23 writes · 3 contradictions
   apr 27 ▁▂▃▅█▃▂▁  RED     stake 0.78 · 41 writes · 11 contradictions
                              └─ drift event: "wrong server" scenario
                                 cursor wrote prod-ip → claude-desktop
                                 wrote staging-ip · resolved manually
   may 04 ▁▁▂▂▁▁▁▁  green   stake 0.46 · 15 writes · 0 contradictions
   ```
3. Highlight the `RED` row with cursor; hover shows tooltip: "11 contradictions detected · auto-quarantined · resolved 2h12m".

### Voiceover
- **EN**: "Federation without auditing is chaos. Compass tracks drift — every contradiction, every stake spike. Here, two weeks ago, I had a real incident: I told Cursor the prod IP, Claude Desktop wrote staging. Compass flagged it red, quarantined the conflict, and surfaced it in this timeline. No silent corruption."
- **中**: "联邦不审计就是灾难。Compass 跟踪 drift——每条矛盾、每次 stake 飙升。两周前我撞过一次:跟 Cursor 说生产 IP,Claude Desktop 写了 staging。Compass 标红、隔离、上 timeline。零静默损坏。"

### Visual cues
- Color sweep: green → yellow → RED → green (animate the color column 1s).
- Red pulse on the `apr 27 RED` row, hold 3s.
- Annotation arrow pointing at `stake 0.78` with caption: `stake spike = drift signal`.
- Lower-third at 3:15: `auditable by design · MIT licensed`.

---

## Section 5 — Self-Host (3:30–4:30, 60s)

### Screen
1. Cut to a fresh terminal. Run:
   ```bash
   git clone https://github.com/nautilus-org/compass
   cd compass
   docker-compose up -d
   ```
2. Show the docker output: 4 containers spinning up (`compass-api`, `compass-worker`, `compass-pg`, `compass-redis`). Hold until all show `healthy`.
3. Run:
   ```bash
   curl http://localhost:8080/healthz
   ```
4. Response:
   ```json
   {"status":"ok","version":"0.9.0","license":"MIT","uptime":"4s"}
   ```
5. Cut to a browser tab: `http://localhost:8080/admin` — show the dashboard with a single user `alice@example.com`, 6 memories, 1 drift event from earlier. All running locally.
6. Overlay text: `your data · your hardware · MIT forever`.

### Voiceover
- **EN**: "And it's all open source. One `docker-compose up`. Postgres, Redis, the API, the drift worker — four containers, healthy in seconds. Hit `/healthz`, get version 0.9.0, MIT license. Your memory, your hardware, your rules. We can't lock you in even if we wanted to."
- **中**: "全开源。一句 `docker-compose up`。Postgres、Redis、API、drift worker——四个容器,几秒健康。打 `/healthz`,版本 0.9.0,MIT 协议。你的记忆,你的硬件,你的规矩。我们想锁你都锁不了。"

### Visual cues
- Green ✓ checkmarks animate in as each container reports `healthy`.
- Big bold caption at 4:10: **`MIT · forever · no enterprise tier rug-pull`**.
- Show the GitHub stars counter ticking up (real or simulated).

---

## Section 6 — Closing (4:30–5:00, 30s)

### Screen
1. Three stat cards fade in side by side, monospace:
   ```
   ┌─────────────────┬─────────────────┬─────────────────┐
   │ LongMemEval-S   │ Cost vs GPT-4o  │ License         │
   │   56.6%         │   1/15          │   MIT           │
   │ (sota tier)     │ (per-recall)    │ (forever)       │
   └─────────────────┴─────────────────┴─────────────────┘
   ```
2. Fade to GitHub repo page: `github.com/nautilus-org/compass` — show stars, last commit `v0.9.0`, README hero.
3. End card:
   ```
   compass v0.9.0
   cross-agent memory · auditable · open

   github.com/nautilus-org/compass
   paper: arxiv.org/abs/2505.xxxxx
   ```

### Voiceover
- **EN**: "56.6% on LongMemEval-S — competitive with the SOTA. One-fifteenth the per-recall cost of GPT-4o-as-memory. MIT, forever. Read the paper, star the repo, and stop letting your agents forget. Compass — link in description."
- **中**: "LongMemEval-S 56.6%——SOTA 同档。每次召回成本是 GPT-4o-as-memory 的 1/15。MIT 永久。读 paper、star 仓库、别再让你的 agent 失忆。Compass——链接见简介。"

### Visual cues
- Highlight `56.6%` and `1/15` — pulse 2x, gold color.
- Final 3s: hold on the GitHub URL, large monospace, no other elements.
- Fade to black at 4:58.

---

## Production notes

- **Recording**: 1920×1080, 30fps, OBS or Screen Studio. Terminal font: JetBrains Mono 16pt. Browser zoom: 125%.
- **Audio**: Single-take voiceover EN, then re-record 中文 dub. Ship two versions (en.mp4, zh.mp4) + one bilingual subtitle track.
- **Music**: Optional low-volume bed (~ -24 LUFS), lo-fi, fade out under voiceover. Skip music entirely on Section 3 (the money shot — let the recall result land in silence).
- **Captions**: Hardcode lower-thirds. SRT for the rest. Both languages.
- **Length budget**: Section 3 is the hero — if you must cut, cut Section 5 to 45s, never Section 3.
- **Thumbnail**: Side-by-side Claude Desktop + Cursor with a glowing arrow between them, text: `cross-agent memory · live`.

---

**Section count**: 6
**Total duration**: 5:00 (300s)
