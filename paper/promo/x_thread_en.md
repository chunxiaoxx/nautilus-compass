# Twitter/X Thread · English · compass v1.0 launch

> 9 tweets · ≤280 char each · image positions marked · replace <arxiv-id> + links before posting

---

**[1/9]**
Two months ago I started doing 8-hour Claude Code sessions. ~30 times/day "you forgot what I just said." That's the LLM context-window ceiling. It's also the real ceiling for shipping LLM agents.

Today I'm open-sourcing Nautilus Compass — long-term memory done right.
🔗 github.com/chunxiaoxx/nautilus-compass

---

**[2/9]**
Headline numbers:

LongMemEval-S · n=500 · **56.6%**
- ties Zep SOTA band (55-60%)
- beats mem0/MemoBase by 15-20 pts
- total cost: $3.50 — 1/15× what closed-API stacks pay

First open-source plug to hit this band using only Chinese-API LLMs + local embeddings.

[fig 1: LongMemEval comparison table]

---

**[3/9]**
Why so cheap?

No GPT-4o judge. No graph DB. No data upload.

Stack:
- DeepSeek V3.2 thinking (China API · $0.002/q)
- local BGE-m3 dense + bge-reranker-v2-m3 cross-encoder
- 5-stage pipeline · pure Python

Full 500-q run: $3.50. Less than a coffee.

---

**[4/9]**
But cheap isn't the point. Where the points come from is:

ablation:
- BGE-m3 alone → 41%
- + multi-angle query rewriting → +27 pts (huge on single-session-user)
- + cross-encoder rerank → +5 pts
- + type-aware prompts → +3 pts
- + thinking mode → +10 pts (V3.2)

biggest win: query rewriting. Not the reranker. Counter-intuitive.

---

**[5/9]**
Counter-intuitive #2: thinking mode is NOT universally helpful.

- DeepSeek V3.2: thinking-on +10 pts ⬆️
- GLM-5.1: +2 pts ⬆️
- Kimi K2.6: ±0
- MiniMax M2.7: 44% refusal cascade ⬇️
- DeepSeek V4-pro think-high: tied V3.2 (-0.2 · 8× cost)

Per-model thinking benchmarks must be re-run for every release. Don't assume.

---

**[6/9]**
Also ran the new EverMemBench-Dynamic (Hu et al. 2026 · arxiv 2602.01313):

n=500 · **41.0%** e2e · recall@20=94.8%

paper Table 4:
- MemoBase: 34.27
- Mem0: 37.09
- Zep: 39.97 ← compass sits here
- MemOS: 42.55
- EverCore: not reported

ties Zep · +4 vs Mem0 · −2.5 vs MemOS.

---

**[7/9]**
v1.0 isn't just numbers — it's pip-install-and-go:

- one-line install
- MCP server (Claude Desktop / Cline / Cursor)
- Claude Code plugin (drop-in hook = persistent memory)
- A2A protocol adapter (cross-agent message routing)
- MIT · all data local · zero upload

[fig 2: 30-sec install GIF]

---

**[8/9]**
Why I built this:

Claude Code is my 8-hour-a-day pair programmer. But every session ends and it forgets the entire project context.
I wrote 200 lines of hook. It remembers now.
Then I figured: other people need this. And it has to be done right.

paper: <arxiv-id>
90-sec demo: <link>

---

**[9/9]**
Everything reproducible:

- eval scripts: scripts/longmemeval_full500.py + scripts/evermembench_bge.py
- 6-LLM evaluation logs
- cross-judge replication (κ=0.772)

Run it yourself, get a different number, file an issue. Reproducibility is the top priority.

🔗 github.com/chunxiaoxx/nautilus-compass

RTs appreciated 🙏 — early users matter most.

---

## Image checklist

- [ ] fig 1: LongMemEval n=500 bar chart (compass 56.6 · Zep 58 · mem0 35 · MemoBase 32)
- [ ] fig 2: 30-sec install GIF
- [ ] fig 3: EverMemBench Table 4 with highlight on compass row
- [ ] fig 4: thinking-mode 5-LLM bar chart

## Posting timing

- Tuesday/Wednesday 9:00 AM PT (peak ML twitter)
- chain all 9 tweets within 5 min · don't wait for engagement
- pin tweet 1 · check replies after 30 min

## Reply playbook

- "How vs mem0?" → quote [3]+[4]
- "Why not V4?" → "V4 think-high tied V3.2 at 8× cost · v1.0 locks V3.2"
- "Numbers seem high" → reproduction script + cross-judge κ
- "Just RAG?" → "no — multi-angle retrieval + day-bucket diversification + reasoning-mode aware LLM calls + cross-judge validation. paper §3."

## Whom to @

- @AnthropicAI (Claude Code plugin)
- @deepseek_ai (V3.2 thinking)
- @cline (MCP integration)
- @cursor_ai (MCP)
- @taranjeet (mem0 author · per outreach plan use repo issue not tweet @)
