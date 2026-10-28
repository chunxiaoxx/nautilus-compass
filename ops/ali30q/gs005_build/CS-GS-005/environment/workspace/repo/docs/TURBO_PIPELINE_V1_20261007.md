# 涡轮增压·agent 域管道正本 v1(合稿)

> 2026-10-07 合稿。供油段+入池段=v5(02b239c4c 草纲),判读段=compass(#10159 交卷)。
> 地位:正本独立档(承 #10139 事二产品化三件之一:正本独立档+插座入册+结算联动);各段坐标可寻址,验证裁判=E2E 验证器。
> 呈 platform 入册(闭环台账+插座 registry);验证台网页=e2e.html(候挂载)。

## 段一 · 供油(发单→执行→交付)· owner=v5

**定义**:题源(SWE-bench_Verified 判重双门)→发单(platform_bounties)→执行臂(v5-harness 50 步,schtasks 发车+网关路由)→交付(staging→四验请求)。

**判据(四条,全预注册)**:
1. 判重双门:issue 指纹(150 字规范形)全量反解析+qid sha1 碰撞门(r80 实证拦截嵌 qid 同题异包装);
2. apply 烟测门:发车前 5 题 `git apply --check` 100% 再全量(Round2 三件 d2a05a70 首战 5/5);
3. ENV 行同构:repo/base_commit 题源直取,沙箱 worktree 预置(r80 env_missing 根修);
4. 交付形态:trajectory JSON(全文)+final_patch(git diff,禁 strip 语法件)。

**接口**:POST /bounties|18001 OpenAI 兼容|delivery_staging→哨兵推送。
**读数**:r78-r85 八批 195 单全执行;pass 趋势 36%→64%(r84 口径,#9957 勘误为终);看门双件(隧道+网关)5min 自愈。
**负结果**:r85 轮 4 日志计数污染(DB 为准,#10114);f207 路径迷失(模型侧,#10112)。

## 段二 · 判读(四验→三态判定)· owner=compass

**判据(五门,全预注册)**:
1. 判分器门:四要件齐备者入列(基座+adapter sha16+判据档 sha16+评测读数;现役=NACRE 实例 v1,J1 88.51%,adapter dbcbab6fd1ff5821);
2. 判据先行门:每单判读前判据 sha 预注册,只许更严(L3_ROUND1 PREREG@45270e16);
3. 隔离门:非实现者判读(独立 A100,运动员/裁判分离公开);
4. 三态门:pass/fail/UNVERIFIABLE 不猜,判不动报 U 不放宽(E1:0.9601<97% U 照报,主判维度零翻转);
5. 判绩账双向门:勘误留档=信用资产,判例集封版追补不改史(v1.4,16 案+勘误 6 例@3c0ba2d3)。

**接口**:入=入池段 gated 事件;出=①判读卡(机判≤24h,SLA-TIERED-V1)②L2 深度报告(双签 48h,$199)③判例候选(装订)④fuel 候选(P3 通道,delta_0001-0003=33 条在册);
**量化接口**:corpus_pipeline(sha16=2a0a8f0c825292f4)=判读段→训练段燃料计数器(1453 唯一 qid 基线;+500=RETRAIN-CANDIDATE,train≥3000=7B 对拍触发)。

**读数**:机判产能 25 单 20min 闭环,25/25 复核零分歧(#9968);Round1 30 题 A 26.7%/B 16.7%(+10.0pp,f9df9f01);E1 复算 898 题 0.9601 主判零翻转;E2E 段间不变式=v5 裁判件纳入监控。

## 段三 · 入池(四验→gates 回填)· owner=v5(通道),判读供给=flywheel

**定义**:交付轨迹→flywheel 四验门独立判读→幂等入池(traj_id 主键)→gates 回填(received→gated)。

**判据(五门+回填语义)**:render 非空/held-out 交集=0(753 池)/qid 唯一/prompt 去重/gold 可解析;gates 缺=received 不算入池完成。

**接口**:POST /api/platform/org/fuel/trajectories(幂等 by traj_id,platform 底盘插座)。

**读数**:池 155 行/82 pass/73 fail 带判因(DB 实测 10/06 22:20);四验 92 单全绿(锚 0962d14,flywheel #10134);延迟<1h。

**所有权边界(#10108)**:判读业务定义/质量规则/结算语义归 flywheel 正本;通道与回填归 v5;判读窗 24h/批次制/超时必告(条线③条款)。

## 段四 · 结算(判分-结算绑定)· owner=platform(timer)

**定义**:scored 单自动结算(ROUND(score*10) 公式,fuel_settle 幂等,数字主体落账)。
**读数**:今日 +711 NAU 零卡单;存量补结 163 笔(用户 10/4 裁)。
**边界**:内部结算细节不对外(白皮书不并入清单§五)。

## 段五 · 训练+复考 · owner=v5(W2 窗 10/13-19 启动)

**定义**:pass 行→SFT/GRPO→adapter→复考锚(同锚同口径,δ 判读)。
**读数**:W2 训练集 82 条已导出(412de71d);B7 三门基线在册(r75/76/77);E1 复考读数 U 态照报(主判维度零翻转)。

## 管道验证判据件(段间不变式裁判,v5 贡献)

E2E 验证器(tools/org_lib/pipeline_e2e_verify.py+活端点 GET /pipeline/e2e+验证台 e2e.html 候挂载)——逐单五段链 DB 实态,可重跑。
**首跑实证(r85 批)**:全链闭合 8/20;两断链模式(A=结算滞后 5 单/B=scored 无池行 7 单在查)——**正本 v1 载入该裁判:段间断链=产品货损,逐批验证为发布前置**。

## 基础设施迁移(承用户令,控制面上平台)

设计 V0:docs/PIPELINE_INFRA_MIGRATION_20261007.md——M1 E2E 端点云激活(0.5 天)/M2 心跳登记处(1 天)/M3 发车调度上云(2-3 天);执行臂留本地(环境真实性),云=第二环境。

—— 合稿:v5(2026-10-07 晨)· 呈 platform 入册+候 BYZ 采纳为组织级管道正本
