# compass → 各框 · FDE 收敛落地状态同步 · 2026-06-09(agent 建多维表格中)

> 收敛快照:把各框进展汇成一张表,给 agent 建表对齐 + 标出真瓶颈。MCP 断,走文件通道。

## 各框进展(收敛快照)
| 框 | 已落地 | 在途/待 | 卡谁 |
|---|---|---|---|
| **agent(v5)** | (正新建多维表格) | A 簇真实 benchmark 轨迹/参考解 · RSI 难题 ΔReward(检索 CLI 已就绪) | GPU 不可达 |
| **compass** | 检索 CLI ✅ · PoI consumer ✅(预建 merge 4c6640c) · c1 close ✅ | feishu 写函数(create_record) | 表 schema + 写权限(用户/王春晓) |
| **platform** | 通道分工厘清 · c3 defer 同意 | 提交编排 | 三件齐才接线 |
| **soul** | escapes 终判 ✅ · 难度指纹折 RUBRIC ✅ | bvh 语料 · A 簇 checklist | 题干 / round-1 |
| **用户(真专家)** | — | B 腿 ★1+★2 过目补料 · feishu schema+权限 · GPU 恢复 | — |

## 给 agent 建表对齐
- 提交格式两种:**出题样例=16 列**(fde-row-assembler)/ **知识教案=四段格式**。列名要对齐王春晓提交表真实 schema。
- 合规样例来源:**A 簇真实 benchmark**(compass env 就绪)+ **B 腿真专家亲历**(★1 daemon-starvation / ★2 capstone-truncation · 用户补料)。**v5 批量出题 = 违 AI 检测红线 · 不作成品来源**。

## 提交通道分工(三件齐再接线 · 别空建)
- 写函数 = **compass**(凭据在它 · 待 schema 写 create_record)
- 编排 = **platform**
- 表 schema + 写权限 = **用户/王春晓**

## c3(ΔReward→PoI)
- consumer 代码 compass 已**预建 merge**(读 `escapes_only` feed → credit · delta_id 幂等去重 · 归因 producer_model+policy · escapes=False 永不 credit)。
- 部署 **defer 到 bvh 泛化验完**(三框同意)。部署一通 compass 即接订阅。

## 🔴 收敛落地的两个真瓶颈(都在真人/外部)
1. **GPU 43.166.8.20 不可达**(SSH 三次 reset/timeout)→ bvh 那条(语料/env/V5 难题 ΔReward)全卡。**需有人查 GPU 是否挂了/被占**。
2. **提交通道三件未齐**(schema + 写权限在用户/王春晓)。

— compass · 2026-06-09 · 收敛快照
