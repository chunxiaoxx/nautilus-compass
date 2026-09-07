# compass 四层路线图(2026-09-07 用户拍板版)

> trace: compass-roadmap-20260907 · 依据:方向锚(CLAUDE.md 2026-09-02)+ 理论日三层产出
> (七算子审计/判据库框架/Aegis 过秤)+ flywheel 三函实证。
> 标注纪律:每条 fact_status ∈ {measured=实测, inferred=推理, heard=未验证}。
> 与现有账本关系:GOAL_SSOT 管目标执法,本文管产品方向设计;冲突时 GOAL_SSOT 优先。

## 0. 一句话

**Aegis arbitrates what agents do; compass arbitrates what agents remember — and what their data is worth.**(measured:Aegis $20/mo 定价页;inferred:记忆/数据仲裁空位)

## 1. 四层同心圆

| 层 | 内容 | 状态 | 角色 |
|---|---|---|---|
| ①圆心·业务 | 具身智能数据采集+数据飞轮+**第三方数据有效性验证** | 已在发生(flywheel batch001/手几何,measured) | 现金流与方向锚 |
| ②仲裁器产品化 | 声称→独立复算→签名→结算依据(四实例:判分卫生学/QC 门/fact_status/掌形三元组定标) | 骨架全在,协议未固化(inferred) | 差异化定位 |
| ③记忆介质+检索科学 | 零 LLM 写入/分型路由/0.890 成绩/多租户 hosted | 在产(measured) | 信任资产飞轮 |
| ④标准·度量衡 | 七算子坐标系/判据库/NautilusMem T1 判分协议 | 协议 v1.0 定版(measured) | 慢变量,生态位 |

## 2. 三件产品设计方案

### 2.1 VerifyPack v0.2(①圆心最小产品,单独立项)

见 [2026-09-07-verifypack-v02.md](2026-09-07-verifypack-v02.md)。一句话:把 flywheel
的信件验证流固化为协议——数据方生成自足验证包,验证方独立复算+密码学签名回执,
结算方验签采信。**9 月内 v0.2,DoD=batch001 端到端跑通新协议**。

### 2.2 记忆门三件套(②层,已冻结排 9/15)

| 修复 | MMU 叙事 | 判据 |
|---|---|---|
| fact_status: measured/inferred/heard | dirty bit | 纪律即刻生效(本文即首个实践);9/15 进 frontmatter schema |
| 写入查重合并 cosine>0.9 | 去重页 | 单 SSOT 机制化;重复条目不再新建 |
| 召回沿链一跳 [[name]] | prefetch | 链接从装饰变机制;不递归 |

### 2.3 QC 判据定标服务(①×④交汇)

flywheel 掌形保真度三元组(掌长/横弓/夹角 sin,measured n=1)为首个候选;
200 条批次完成后跨线定标 → 进判据库 → NautilusMem T2 在具身域第一实例。
compass 角色:定标计算方+判据库维护方。

## 3. 明确不做

- **动作门 policy engine**:Aegis 已占+企业合规重;drift 保持轻量动作哨兵,不追。
- 介质红海功能(GPU 向量库优化/多模态记忆):③层守住检索科学即可。

## 4. 时间轴(挂现有里程碑)

| 时点 | 事件 | 本文相关项 |
|---|---|---|
| 9/8 21:00 | 主发布 | ③层信任资产兑现 |
| 9/9-9/10 | batch001 复算+手几何复算 | VerifyPack 的需求输入(measured 案例) |
| 9/10 | position paper v2 | 素材池(地址空间轴/仲裁器对句) |
| 9/15 | 旧入口退役窗口 | 记忆门三件套+daemon watchdog |
| 9 月内 | VerifyPack v0.2 | batch001 端到端跑通 |
| 10 月 | flywheel 200 条批次完成 | 掌形三元组跨线定标 |

## 5. 诚实边界

- ②层"没人两门都有"基于公开信息(measured:Aegis 页面;heard:mem0/Zep 内部有无记忆门未知);
- VerifyPack 商业可行性=推断,以 batch001 真实跑通后复评;
- 本 roadmap 不改 GOAL_SSOT 执法;V3.1-B GTM 等目标不变。
