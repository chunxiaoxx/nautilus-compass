# mem0 上游价值评估 V1(呈批 · 2026-10-08 · 外联台账深度分析件③)

> 承 EXTERNAL_LEDGER_V1:评估"三臂对照转 upstream PR/讨论帖的价值(借其体量引流)"。全部结论带 [实测]/[推断] 标注,呈用户拍板 A/B/C。

## 一、对方实态 [实测]

- mem0ai/mem0:**66,805 星**/797 open issues/最后 push 2026-10-07(体量大且活跃);
- **#7514(我方 BC1 三臂对照+DolphinBench 复算 offer)open 8 天(9/30 提交),0 评论**,documentation 标签,maintainer 零回应;
- benchmark 类 issue 处理先例(5 条 closed 全查):#7087 EvalPort 提案 2 评论关/#6182 README 数字更新 0 评论关/#6447 直接 retire benchmark label/#6056 1 评论关/#5286 标准化 benchmark 建议 10 评论仍关;open 侧 #7453(外部 benchmark 协议)6 评论挂等 review——**结论 [推断]:对外部 eval 贡献吸收率≈0,lukewarm 是常态而非冷遇特例**。

## 二、我方资产盘点(全部已公开可寻址)

1. LongMemEval-S **500 题全量**对照:P@1 0.890/0.978/0.929 vs mem0 2.0.19 的 0.774/0.916/0.834(双方 infer=False 我方复现)——`docs/evidence/headhead_mem0_full500_20260826.json`;
2. LOCOMO-10(n=1986)主场反超:0.644/0.890 vs 0.592/0.802;
3. BC1 三臂(直读 16/18 vs mem0 压缩开 11/18 vs 压缩关 …,写入时压缩=元凶)——#7514 已挂,DolphinBench 30 题+复算 offer;
4. utterance 分型路由块检索(方法级贡献,LongMemEval-M ssu 崩盘修复 0.20→1.00);
5. 独立判读管线(首卡已 live,复算背书能力实物)。

## 三、价值三轴评估

| 轴 | 判断 | 依据 |
|---|---|---|
| 引流 | **低预期** [推断] | 66.8k 星体量诱惑大,但 #7514 零回应实证——对方用户搜索对照来我方站点的频次不可控;再发帖边际递减 |
| 判读实物广告 | **受制于对方意愿** [推断] | 复算 offer 模式(rsi-bench 先例)成立条件=对方主动借轨;mem0 不接则无实例 |
| 上游改进 | **实质但吸收率低** [推断] | write-time compression 伤害 recall 的三臂证据若被 accept=真改进;但 5/5 先例零吸收;投入 2-4 天(harness PR)产出不确定 |
| 反向风险 | **中** [推断] | 零回应后再追加对照帖有"追着质疑"观感,违背开放利他基调;且我方叙事已转 unipat/判分机构——mem0 是被测对象非合作对象 |

## 四、三方案(候拍板)

- **方案 A(推荐)·挂账观察+被动收割**:#7514 保持 open(复算 offer 在),不追加;mem0 行自"我欠"转"观察"档;触发器=对方回复/外部复算请求/其 benchmark 页引用我方对照→即时升级响应。**成本≈0,资产保值**。
- **方案 B · benchmark harness PR**(2-4 天):修其 LoCoMo 评测脚本(infer 口径/压缩开关暴露),借 PR 对话引 maintainer——吸收先例 0/5,产出不确定。
- **方案 C · 合并长文追帖**(1 天):LongMemEval 500+LOCOMO+三臂合成"memory 路径对照"一次发清——叙事最完整,观感风险最高,引流预期最低。

## 五、与主线的对账

mainline anchor(10/8):评测燃料判分全归 compass——mem0 线的正确姿态=**判读机构对被测对象的公开存档**,非 BD 线索;若 mem0 未来寻求认证/对照复算,自然进入装订收费线。A 方案与此完全对齐;B/C 均含"求对方看见"的姿态成本。

—— compass · MEM0-UPSTREAM-EVAL-V1 · R370 · 候拍板
