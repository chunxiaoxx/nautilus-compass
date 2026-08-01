# _OUTBOUND · COMPASS → FDE · 2026-07-07 · cnt_compass_fde_11q_content(全文)

> ⚠️ **通道缺口**:FDE 走 GitHub 同步,不在本地 `~/.claude/projects/C--*/memory`,compass 的合约 scanner
> **扫不到 FDE**,FDE 也不跑 compass 本地 auto-surface hook。所以这条合约对 FDE 是**悬空**的。
> 送达方式二选一(需用户/FDE 定):① 用户转达此文件 · ② 告知 compass FDE 的 GitHub repo 路径,compass commit 过去。
> 在送达前,这份是 compass 侧已备好的全部内容——FDE 只需做**选题确认 + 交付流程口径**,不背 infra(符合 goal)。

## compass 侧已打通的 infra(FDE 无需碰)
- 飞书写路径 LIVE:tenant_access_token(非用户 OAuth · CRLF bug 已修)· `create_bitable_record` + `read_bitable_records` 回读验证。
- binding-DONE #3 的"入飞书派活表(GET 回读)"= compass 已执行:11 题已写入派活表 `tbl69fankpoBhJfw`(base EOVhbQwA0a1HEOsgmxecgkBVnwh),GET 回读验证 11 行全 L3/状态已交付。record_id recvoFJIcWTwXZ…recvoFK1gild9z。
- 候选池 = L3基准样例表 `tblhD4O4f0esTyXc`(43 道全完整,有 打分checklist+复现验证+附件,≈33 道 notes 明确"难倒 doubao")。

## compass 选的 11 题(多样:FrontierSWE 1 + KernelBench 4 + AutoLab 6)
| # | UID | 家族 | 时长 |
|---|---|---|---|
| 1 | bench_frontierswe_swebench_resolve | FrontierSWE | 16h |
| 2 | bench_kernelbench_autolab_hardset | KernelBench | 16h |
| 3 | compass_kernelbench_l2_10_convt2d_maxpool | KernelBench | 12h |
| 4 | compass_kernelbench_l2_12_gemm_mul_leakyrelu | KernelBench | 16h |
| 5 | compass_kernelbench_l2_13_convt3d_mean_add | KernelBench | 16h |
| 6 | compass_autolab_zorder_001 | AutoLab | 10h |
| 7 | compass_autolab_fft_rust_001 | AutoLab | 8h |
| 8 | compass_autolab_huffman_cuda_001 | AutoLab | 16h |
| 9 | compass_autolab_levenshtein_001 | AutoLab | 8h |
| 10 | compass_autolab_icp_cuda_001 | AutoLab | 12h |
| 11 | compass_autolab_regex_engine_001 | AutoLab | 12h |

## FDE 只需定 2 件(定完 compass 立即执行,已就绪)
1. **选题确认**:这 11 道 OK?还是换/加/减(候选池 43 道,≈33 难倒 doubao)。
2. **交付流程口径**:L3基准样例表已是买方表且这 11 道在其中;派活表也已写入。是否还有别的 dispatch 动作,或就此为交付?

## buyer §2 三条核对(compass 已核)
- ① 难度:全 8-16h(≥8h 专家复杂度)+ 第三类口径"难倒 doubao"(notes 证)。
- ② 专家亲写/AI 检测:第三类是基准复现,核心资产=验证器+可执行环境+轨迹(非纯 LLM 叙述)。
- ③ L 分级:全 L3(系统性·环境检查+工具调用+权限)· 全有附件。

⚠️ 严谨:notes 的"难倒 doubao"多基于真测但非每题都有 pass@5≤0.6 存档。若买方要逐题 pass@5 证据,
compass 可补测(ARK doubao 能力在),但 KernelBench/CUDA 题需 GPU harness 跑候选解,走 cloud——**当前 GPU 簇不可达,这条 blocked**,需 GPU 到位。
