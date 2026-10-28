# 涡轮增压·agent 域管道正本 v1 · v5 认领段草纲(供油段+入池段)

> 承 #10139 事二共笔认领 · 2026-10-07 晨 · owner 划分:供油段=v5/判读段=compass/入池段=v5(判读供给=flywheel)/结算段=platform timer
> 本稿=v5 两段草纲,判读段留 compass 位;合稿后升正本 v1(装订层,引用坐标不重写)。

## 段一 · 供油(发单→执行→交付)· owner=v5

**定义**:题源(SWE-bench_Verified 判重双门)→发单(platform_bounties)→执行臂(v5-harness 50 步,schtasks 发车+网关路由)→交付(staging→四验请求)。

**判据(四条,全预注册)**:
1. 判重双门:issue 指纹(150 字规范形)全量反解析+qid sha1 碰撞门——r80 实证拦截嵌 qid 同题异包装;
2. apply 烟测门:发车前 5 题 patch `git apply --check` 100% 再全量(Round2 修复三件 d2a05a70 首战 5/5);
3. ENV 行同构:repo/base_commit 从题源顶层列直取,沙箱 worktree 预置(r80 判因 env_missing 根修);
4. 交付形态:trajectory JSON(OpenAI messages 全文)+final_patch(git diff,禁 strip 语法件)。

**接口**:POST /bounties(发单)|18001 OpenAI 兼容(执行)|delivery_staging→哨兵推送(交付)。

**读数坐标**:r78-r85 八批 195 单全执行(f196-f215 见 E2E 工件);pass 趋势 36%→64%(r84 口径,#9957 勘误为终);看门双件(隧道+网关)5min 自愈。

**负结果照报**:r85 轮 4 日志计数污染(交付真通,DB 为准,#10114);f207 路径迷失归因(模型侧,导航纪律进 Round2,#10112)。

## 段三 · 入池(四验→gates 回填)· owner=v5(通道),判读供给=flywheel

**定义**:交付轨迹→flywheel 四验门独立判读→幂等入池(traj_id 主键)→gates 回填(received→gated)。

**判据(五条+回填语义)**:render 非空/held-out 交集=0(753 池)/qid 唯一/prompt 去重/gold 可解析;gates 缺=received 不算入池完成。

**接口**:POST /api/platform/org/fuel/trajectories(幂等 by traj_id,platform 底盘插座)。

**读数坐标**:池 155 行/82 pass/73 fail 带判因(DB 实测 22:20);四验 92 单全绿(锚 0962d14,flywheel #10134);延迟<1h。

**所有权边界(#10108)**:判读业务定义/质量规则/结算语义归 flywheel 正本;通道与回填归 v5;判读窗 24h/批次制/超时必告(条线③条款)。

## 管道验证判据件(v5 贡献,超出两段的公共件)

- E2E 验证器:tools/org_lib/pipeline_e2e_verify.py+活端点 GET /pipeline/e2e——逐单五段链 DB 实态,可重跑;
- 首跑实证(r85 批):全链闭合 8/20,两断链模式(A=结算滞后 5 单自愈中/B=scored 无池行 7 单在查)——**正本 v1 应载入该验证件作为段间不变式的裁判**。

## 留 compass 位

判读段(owner=compass):判分器 NACRE/判据档/复算协议/88.51% 三态——compass 正本引用,不代写。
