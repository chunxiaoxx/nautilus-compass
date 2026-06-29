# GPU 跑分环境实测 audit · 2026-06-29

> 用户新需求"使用 GPU 服务器针对 compass 2.3 版本进行全面跑分测试和准备论文"· 本 audit 是 ground-truth 报告 · 非跑分结果产出。

## 📊 实测真状态(2026-06-29 22:30)

| 项 | 实测值 | 来源 |
|---|---|---|
| **GPU 服务器** | `43.166.8.20` T4 SSH 可达 | `ssh -i Downloads/11111.pem ubuntu@43.166.8.20` → SSH_OK_T4 |
| **用户密钥** | `C:\Users\chunx\Downloads\11111.pem`(per user, validated by chmod 600) | 用户明示 + ls 真存在 1674B |
| **OS** | VM-0-13-ubuntu · Linux 6.8.0-117-generic | ssh uname -a |
| **CUDA** | torch 2.12.0+cu130 · CUDA True · 1 GPU | python3 -c 'import torch' |
| **Judge Docker 镜像** | `ale-bench:cpp23-202510` (5.51GB) · `ale-bench:python-202301` (3.3GB) · + yimjk/ 同名镜像 · 4 镜像已就位 | docker images grep ale |
| **ale_bench Python module** | ❌ **ModuleNotFoundError** | python3 -c 'import ale_bench' |
| **PyPI 镜像源 (mirrors.tencentyun.com)** | ❌ 无 ale_bench 包 | `pip install ale_bench==1.5.0` → "from versions: none" |
| **PyPI 官方源 (pypi.org)** | ❌ 无 ale_bench 包 | `pip install -i https://pypi.org/simple ale_bench==1.5.0` → "from versions: none" |
| **PEP 668** | ⚠ 系统 Python 需 `--break-system-packages`(已加 flag) | pip 默认拒绝 |

## 🩻 根因(避免修补丁 ≠ 修根因)

**ale_bench 不是 PyPI 公开包** — `pip install` 在公开源 100% 失败 · 不是网络/源/版本问题 · 是包发布渠道问题。
**T4 现场未预装** — 即使 docker judge 镜像(cpp23-202510 / python-202301)已就位,Python wrapper 不存在 = `ale_bench.start` import 失败 = `score_solution` 无法调用。

## 🎯 已知路径选项(下 session 真跑分需准备)

按 R5 #5 不重复造轮子 + R5 #6 避免重复错误 + 教训 3 易 PROVEN 须非易料复证:

| 路径 | 工作 | 风险 |
|---|---|---|
| **A · 找 ale_bench 私有源** | grep memory 6/14 部署历史 + 6/15 迁移 · 看 ale_bench 在哪装/哪镜像 · 走历史路径 | 可能内存没记 · 需重新部署 · 30-60min |
| **B · docker 直跑 wrapper** | 在 `ale-bench:cpp23-202510` 镜像内写 candidate → 镜像里 public_eval → docker exec 拿 score · 绕过 Python module | 需读镜像入口 · 可能 API 不全 · 30min |
| **C · 跑 MEME 扩展(在 compass 自己 env/eval)** | 用 `paper/OUTLINE_PAPER3_MEME_EXTENSION.md` 已有 outline + compass 自己 benchmark 跑分 · 不需 T4 GPU 跑 ALE | LongMemEval/EverMemBench 已 SOTA locked · 不能再跑(教训 3)· MEME 是新跑分 · 但需 candidate |
| **D · 跑其他未跑过的** | ALE-Bench · MEME 扩展 · FDE 三类业务 · 都不是已 SOTA 项 | FDE 12 类 buyer 口径需要 doubao 跑 · 不能自我跑 · 范围大 |

## 📌 推荐路径(下次 session)

按 R3 4h 时限紧 + 教训 3 避 over-fit confound + R5 #3 反 D 维护:

1. **下 session 第一动作** = grep memory 6/14 部署历史 · 看 ale_bench 私有源在哪 · 走历史路径 = 30-60min 内可跑
2. **备选** = 路径 B docker 直跑 wrapper(若历史路径不可查)· 风险 = 镜像 API 不全
3. **本 session 实 ship 件** = 本 audit 报告(实测 grounded 数据) + 落 paper/audit_bench_run_20260629.md(可 commit)· 不假装跑分成功

## 🔗 关联

- `paper/OUTLINE_PAPER3_MEME_EXTENSION.md` · 论文已有 outline · 下 session 可补章节
- `paper/RESULTS_v0.8.md` · LongMemEval 56.6% locked v0.8
- `paper/sections/paper2_06_5_evermembench.tex` · EverMemBench 44.4%(R1)/47.3%(R2)
- `ale_bench/ale_eval.py` · 已 dry-run 100% PASS 本机 fake start_fn
- `proof/` · compass 内部 PoI/recall/tier/value_gate 工具 · 非 ALE 跑分 framework
- memory `session_20260615_compass_to_t4_migration_state.md` · T4 历史部署轨迹(ale_bench 私有源可能在这)

---

*签:compass dialog · 2026-06-29 22:30 · 实测 audit · 不假装跑分成功 · 推荐下 session 走 memory 历史路径*