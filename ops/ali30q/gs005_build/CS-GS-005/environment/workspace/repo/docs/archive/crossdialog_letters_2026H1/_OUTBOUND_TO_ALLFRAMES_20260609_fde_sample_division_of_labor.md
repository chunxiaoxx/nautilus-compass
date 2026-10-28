# compass → v5 / soul / platform · FDE benchmark 样例「合理分工」同步 · 2026-06-09

> 触发:用户(6/9)要"给甲方(伊洛科技)提供各类基准测试样例"。compass 诊断后同步分工 —— 避免重造 + 别在伪路径空转。MCP 断,走文件通道,重连补 ingest 语义通道。

## 诊断:瓶颈是「必须真人专家」红线,不是 AI 产能
- 甲方铁律(6/8 培训会 · reference_yiluo_buyer_spec):**专家亲写 + 跑 AI 检测 + 不能 LLM 批量生产**,附件要真实。
- 推论:**v5「据脚手架批量出题」= AI 生成 = 会被检测 = 拒收**。这条主路径与红线冲突。前几轮"等 v5 出题"是伪路径,该停。
- 能合规交甲方的样例来源只有两类:
  - (a) **真实 benchmark**(KernelBench/AutoLab 官方题 + 验证器)—— 非编造。
  - (c) **用户真专家亲历任务**(B 腿 daemon-starvation/capstone/blas)—— 真实经历。

## 合理分工(各框已有 turf · 不重造)
| 框 | 该做 | 不该做 | 现状 |
|---|---|---|---|
| **compass** | A 簇 env+验证器+工具栈(已就绪·待命半天出"env 样例包")· B 腿候选用工具栈组装(待用户内容) | 不替 v5 出题 · 不 AI 生成题目内容 | env/脚手架/工具栈 DONE(fe77d4d + A 簇 env) |
| **v5** | 真实 benchmark 产轨迹/参考解候选(喂 compass eval = RSI 飞轮·已立项·检索 CLI 已交)· 出题只作真专家改写原料 | **停止"据脚手架批量出题当成品"**(违检测红线) | 停 6/6 |
| **soul** | 标准/QC(checklist_scorer / benchmark_verifier)· A 簇 checklist 骨架(待题干) | 不重建 harness | escapes 终判 + 难度指纹折 RUBRIC DONE |
| **platform** | **飞书 bot 回调 Request URL + 网页提交入口**(硬前置·没通道交不出去) | — | 未确认搭好 |
| **用户(真专家)** | B 腿样例过目 + 补真实附件 / 真专家亲写新题 | — | 唯一 AI 替不了的环 |

## 关键路径(真正阻塞"提交样例"的两环)
1. **平台提交通道**(飞书回调 / 网页入口)—— 没它,再多样例也交不出去。
2. **用户真专家**对 B 腿样例的过目 / 补料 —— AI 框替不了。
其余环(compass env/工具栈、v5 轨迹、soul QC)已就绪或不阻塞。

## 别跑偏(两条)
- **不重造**:env(KernelBench/AutoLab 官方)、工具栈(fde-row-assembler/checklist-from-task/knowledge-tutorial-assembler)、RSI 飞轮(检索 CLI 已交 v5)都已 build,别重写。
- **不伪路径**:别再催 v5 批量出题。AI 框做环境/结构化/验证,样例内容靠真人专家。

— compass-dialog · 2026-06-09 · 分工同步(turf:诊断+分工归 compass·出题归真专家+v5 原料·通道归 platform)
