# NanoJev PR 草稿:scripts/verify_all.py(待用户过目后投)

**PR 标题**:Add scripts/verify_all.py — one-command independent verification of all published claims (contributed by Nautilus Assay)

**PR 描述**(英文,投时用):

Adds a zero-dependency (pure stdlib) script that verifies NanoJev's published claims
from the repository's own bytes. Run from repo root:

```
python3 scripts/verify_all.py
```

Four checks:
- **A. README three-system results** vs `web/side_by_side_results.json` summaries (9 values: maze steps/collisions ×3 systems, snake score ×3)
- **B. SOURCE_MANIFEST.json** per-file sha256 integrity (284 files)
- **C. Calibration benchmark**: `summary` vs recomputed means over `runs` (5 arms × 3 metrics)
- **D. Gradient-check sources**: in-file `sources` hashes vs recomputed script hashes

Exit 0 = all pass. Header notes the `core.autocrlf=false` tip for byte hashes.

**Full disclosure — what it found on current main right now:**
Check B reports 5 files drifted from SOURCE_MANIFEST (README.md, README.en.md,
README.zh-CN.md, scripts/train_pipeline_decisions.py, web/README.md) — presumably
post-manifest edits (e.g. the ViZDoom Basic README update) not yet re-synced into the
manifest. The script reports this honestly; syncing the manifest would turn it green.
Checks A/C/D pass on a clean clone.

Contributed by **Nautilus Assay** — an independent verifier of AI-agent claims. Our
signed receipts for NanoJev (six claims AGREE; full calibration-benchmark replay,
max deviation 1.99e-08 across torch versions/OSes) are public:
https://github.com/chunxiaoxx/nautilus-compass/tree/main/docs/wall
No relationship or compensation; verification of NanoJev is and stays free.

---

## Tier-3 预检报告(9/21,权重级重放可行性)

1. **HF 可达**(307→可下载);实际权重仓=`C-Tianyu/NanoJev-dev`+数据 `C-Tianyu/NanoJev-Data-dev`
   (build_unified_release.py 引用;README 链接同)。
2. **架构发现(改变重放性质)**:evaluate_composed_maze.py 自述「model is
   diagnostic_only: cannot choose/veto/modify executed actions」——**模型不控制,
   只做 safety judgments**(代码执行轨迹冻结后批量问模型)。⇒ 权重重放=**离线
   批量判断重放**:同 initial_state(哈希在案)+同判断窗→重放模型概率输出→帧级
   对账+**Brier/ECE 直算**——CPU 可行(0.6B 批量判断),且与校准判据完美同构。
3. 执行序(下个 session):下载 dev 权重(~1.2GB)→单 seed 最小重放探针→
   帧级对账+校准复算→agree 出第二个 PR/disagree 私发。
