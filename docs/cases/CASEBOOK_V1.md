# Nautilus Compass 判例集 v1（CASEBOOK_V1）

> 判分机构公开判例汇编 · 2026-10-03 首装订 · 版本 v1.2 · 状态：公开 demo 版（两线定价之装订线首物，免费）
> 判分机构两线：判读免费（永久，不设付费优先）/ 装订收费（判例集、认证、协议植入）——本文档为装订线第一件公开物。
> 正本坐标：`docs/cases/CASEBOOK_V1.md` · verdict 全件过 schema v2 校验（`tools/verdict_schema_v2.py`）

---

## 卷首 · 判分纪律（适用全部判例）

1. **证据三层标注**（正本 `docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md`）：每条结论性陈述标注 `[实测]`（材料直读/可复算）、`[推断]`（带 upgrade_path）、`[不可验]` 之一。推断不得冒充实测。
2. **判据零放宽**：判读按预注册判据执行，判不动就报"判不动"，不以任何代理顶替冻结语义，不因结果挑判据。
3. **负结果照报**：PARTIAL / U 态 / 否证一律如实出件。判读叙事跟数字走。
4. **非实现者复算**：判读方与材料实现方分离；自报读数须独立复算后才可引用（本机构对己方判读件同样过 schema 校验+复算）。
5. **独立复验入口**：每判例附材料 sha16 锚定与复算命令；外部读者按坐标可独立复验任意判例。

## 判据张力段 · 零放宽 vs 判据演进（如实呈现）

本判例集横跨 pusht 首案的判据 v1 与 v2 两代，张力如实记：

- **案内零放宽**：rollout n=20 案与 n=100 案判据逐字段一致（仅 n: 20→100，用户批准），seed 序列不换，成功率冻结语义（coverage>0.95/300 步）两代同守。n=100 出全零地板时照报"判不动"，未以 coverage 代理顶替主判据。
- **跨案演进走了完整程序**：v1 冻结语义在地板上判不动 → v5 提 v2 草案（#2551：coverage 连续主判+五级刻度）→ 用户批准（宪法十三条①：判据宽松化归用户裁，#2568 留痕）→ compass 技术审定两条修订（#2574：T1 样本锁死全量 100 集/窗，消灭"取前 50 配对"的选择自由度；T2 两法裁决规则主配对 Wilcoxon 辅 MWU，防边界挑显著）→ v2-final 冻结。
- **演进方向实测为"更严"**：v2 的两条修订都是压缩判读自由度（样本选择/统计挑法）；达标门槛 FULL≥0.95 在 v2 下 n=100 仍判"达标性未证实"，冻结语义 0/100 照报。判据演进没有把"未达标"漂白成"达标"——两条结论并存（方向显著有效 + 达标性未证实），详见案 6/案 7。
- **追溯边界**：旧 20 集作废不追溯（#2568 明文），演进只作用于新收材料。

## 两线边界段 · 判读免费 vs 装订收费(如实呈现)

- **判读免费**:verdict 出件永久免费,不设付费优先队列,负结果照报——判读是测量行为,测量线保持中立。
- **装订收费**:判例集、认证、协议植入等"判后事"收费——只做判后事,不做判前影响:装订以已出 verdict 为原料,收费不改变任何一案的判据、判读与结论。
- **张力自纠**:装订物由判读方自装,存在"自装自夸"风险——自纠办法=装订物不豁免任何一条判分纪律(每案附材料 sha16 锚与复算命令,外部读者可独立复验任意判例;勘误照记,见下段)。

## 勘误与判绩账 · 判读方也会错(判绩账双向,如实记档)

判分机构的信用资产不是"从不出错",而是**错了必留痕**:勘误双向记录,不删不改史。

1. **判读方自我证伪(案 2/案 4)**:G1 首轮 ratio~3800 异常,判官先自查分母病(静止段 ‖act−state‖~5e-5)再出旧判定闭合;pusht 配对案"复现注"出注前判官探针先自证伪一轮(24/40 坐标重叠非逐帧复现,median 4dp 相同=分布级巧合),勘误材料方"复现"表述。
2. **材料方勘误获正面记档(案 10)**:step500 事故卷(ckpt 字典序 bug)完整留档未删、如实申报——material_side_honesty 与工件对错正交,过程信用入账。
3. **立规方误诊撤规(R131,判绩账双向第 3 例)**:裁定⑤"秒交/asset null=挂 U 态"基于误诊呈报而立;v5 #3040 勘误(秒交=批量登记常态、asset null=writeback 通道常态)收讫后,我方 31s 内勘误自身裁定档——撤销触发器、修正操作化、撤销 31s OOD 观察项;对称教训同步入档:**采信误诊呈报且未要求产线痕迹对账=未验证即断言,立规方同样会犯**。
4. **判官首算红灯自纠(案 12)**:V4-J2 首算把判别字段(gold 阳性判定)误当通过率(p1=0.92≠0.855)——红灯停,查字段语义按 native==gold 重建联合表,边联合与判官档逐位对上方出数;判别型评测 accuracy=(TP+TN)/n 不是 pass 率,入判读惯例。
5. **归因报告复算勘误(案 13,v1.2)**:RPT-G1-2407 非实现者复算 PASS-with-erratum——15/16 逐位一致,G 臂 ratio 中位数 1.9863→1.9861(判读函两臂中位口径不一致,G 上中位/B 均值;复算人抓出比自查深一层),统一为偶数均值中位,判绩账留痕不改史。

---

## 案 1 · G1 双臂三锚定差分案

- **背景**：flywheel G1 探针（视频注入坏数据 vs 干净数据）双臂训练完成（函 2389），compass 帧级判分。此为判分机构首演。
- **判据**（预注册=flywheel 函 2389 criteria_J 正文；判据档未独立落盘 jsonl——2026-10-04 抽查坐实如实记，此后判据一律独立落盘）：J1 方向一致率 / J2 幅度比 [0.3,3.0] 合格率 / J3 sha 可复算锚定；帧级口径映射已披露非静默（criteria_J 原文为 probe/full 语义）。
- **材料锚**：G 批 manifest_sha `369e1d288468f8e2`；逐臂 rows_sha16 G=`eab63d7fd833d7da` / B=`340eff115ef49e50`（n=40/臂，n_err=0）。
- **判读**：G J1=0.85 / J2=0.925；B J1=0.825 / J2=0.925。差分 ΔJ1=+0.025（G>B，坏数据伤拟合方向符合预期）、ΔJ2=0。材料双臂合格，门槛裁断留预注册语义实验不越权硬判。
- **claims**：[实测] 双臂逐帧读数与差分；[实测] 旧批判定（ratio 数千倍）为分母病——静止段帧 ‖act−state‖~5e-5 致 ratio 发散，修复批 degenerate 0/40，旧判定闭合；[推断] 视频注入未传导到预测（双臂 pred 高度同形态，state 主导），upgrade_path=注入帧 vs 干净帧 pred 逐帧对比。
- **边界**：帧级材料非效度终判；ep0 方向不一致集中现象单列不归因。
- **verdict 正本**：`runtime/loop/_p3_g1_verdict_v2.json`（schema v2 compliant）
- **复算**：`_r54_deploy_judge.py`（A100 判分部署）→ `_r54_pull.py`（材料拉回）→ `python tools/verdict_schema_v2.py validate runtime/loop/_p3_g1_verdict_v2.json`

## 案 2 · G1 假说对撞案（函 2422）

- **背景**：首轮 G1 材料 ratio~3800 异常，flywheel 提"未反归一化"假说并称"方向在均匀缩放下稳健可判"；compass 以实测数据对撞裁决。对立假说以数据裁决的范本判例。
- **判据**：无新判据——实测裁决四条，每条证据分层。
- **材料锚**：G1 首轮 infer_compare 材料；数据集直读 ep0 前 8 帧。
- **判读**（四条）：
  1. [实测] 未反归一化假说否证：pred_head 与 act_head 同量级（1.6581 vs 1.7292，差 ~4%）——若未反归一化应差千倍量纲。
  2. [实测] ratio~3800 真因在分母：静止段帧 ‖act−state‖=3.5e-5~7.4e-5，0.1÷5e-5≈数千倍，非分子异常。
  3. [实测] 材料与自述不符：函称 5 eps×8 帧，实际全部 ep=0——ep_ranges 索引疑义坐实。
  4. [推断] dir_rate=1.0 系判定实现（abs(dot)>0 在近零点积上退化为随机符号），源码 direction 变量（sign 版）算而未用。
- **裁决**：J1/J2 均需修后重出（sign 实现+帧过滤 ‖act−state‖≥1e-3），"方向稳健可判"不成立；U 态维持。
- **边界**：判读分歧以实测裁决，双方过程全留痕；flywheel 如实申报异常的做法判读方明示肯定（过程信用与结论对错分账）。
- **verdict 正本**：函 2422 全文（DB org_mailbox id 2422）+案 1 修复批重判闭合。
- **复算**：数据集直读命令见函 2422（‖act−state‖ 逐帧 norm 计算）。

## 案 3 · pusht 帧级四窗案

- **背景**：pusht 修复效应首判（adapter v2，四窗设计：A1O 存档参照/A1N 干净 orig/A2F 修复 fixed/A2N 同臂双跑）。
- **判据**：帧级辅助读数（dir 率/ratio 带宽/分布），不进层 1 判据本体；效度终判留 rollout（层 1）。
- **材料锚**：四窗 rows_sha16（A1O=`84eb1e39a814c8a0` / A1N=`a50f3e27cd02547f` / A2F=A2N=`afc172f8c4e4a56a`）；噪声底复核：A2F/A2N 推理材料 sha256 全等。
- **判读**：干净对比 A1N vs A2F 样本级显著（Δmedian=+0.24，MWU p=0.03346）；噪声底=0 实测排除 run 噪声；方向支持修复有效（欠幅减轻 0.63 vs 0.39）。
- **claims**：[实测] 样本级显著≠修复归因——帧不配对（各窗各自数据集抽样），抽样混杂未隔离，upgrade_path=配对帧对照（→案 4 执行）；[实测] adapter 变更效应单列（A1O vs A1N p=0.13333 n.s.，时间线混杂实证为代码变更非 run 噪声，A1O 不进数据效应判读——材料方处置正确）；[实测] 全窗 ratio 中位<1=系统性欠幅，模型级现象。
- **边界**：样本级显著与归因级判读分账；pad 占比差异未进判读口径，若入须单列披露。
- **verdict 正本**：`runtime/loop/_p3_pusht_4win_verdict_v2.json`（schema v2 compliant）
- **复算**：`_r61_deploy_pusht_judge.py` → `_r61_pull_pusht.py` → schema 校验同上。

## 案 4 · pusht 配对帧归因案

- **背景**：案 3 upgrade_path 执行——两 ckpt 同帧集配对对照，隔离抽样混杂。
- **判据**：配对统计两法同报不挑（Wilcoxon 配对符号秩+符号检验）；判据定位不变（帧级辅助，效度终判留层 1）。
- **材料锚**：verdict 正本 `/root/vdd3/pipe_art/pusht_pair_verdict.json`（幂等可重跑）；flywheel 配对汇总自报与 compass 逐帧复算逐项一致零偏差（dir 0.85/0.80、delta 中位 +0.0627 等 40/40 字段自洽）。
- **判读**：Wilcoxon p=0.00986<0.05 显著（符号检验 p=0.11385 n.s.，两法同报）；效应量 +0.0627 远小于未配对 +0.24——**大半系抽样混杂坐实**，案 3 保留被实测证实。
- **claims**：[实测] 归因级方向支持修复有效；[实测] dir 一致性 A2F 0.80<A1N 0.85 如实记（幅度改善同时方向一致性略降）；[实测] 异质性无清晰模式（"改善集中高活动帧"类叙事不成立）；[实测] 材料方"复现注"勘误——未配对窗与配对帧集坐标重叠仅 24/40，等值率 5/24，median 4dp 相同=分布级巧合非逐帧复现（判读方探针先自证伪一轮再出注）。
- **边界**：效度终判仍留层 1 rollout 主判据（→案 5/6）。
- **复算**：`_r63_deploy_pair_judge.py`；判读函 `runtime/loop/_r63_mail_pair_verdict.md`。

## 案 5 · pusht rollout n=20 初判案（PARTIAL-U）

- **背景**：层 1 主判据首判（冻结语义：成功率=coverage>0.95/300 步）。
- **判据**：v1 冻结语义；判据零放宽三不（不改阈值/不延长步数/不以代理顶替）。
- **材料锚**：四窗 ckpt_sha16（A1O=`b9b23d51d273aea4` / A1N=`1968c1c003880bb8` / A2F=`70bfbff386c8ea5c` / A2N=`629583967b49e1bb`），n=20/窗同 seed 配对，env_fingerprint 设计合格。
- **判读**：成功率四窗全 0/20——地板效应差分判不动（0 vs 0），U 态；辅助 coverage 均值 A2F×2.02 vs A1N 但 MWU p≈0.48 不显著（n=20 方差大，均值差由少数高覆盖集驱动）；噪声底=逐集 0.0。
- **claims**：[实测] 地板判不动照报；[实测] coverage 不显著如实报（不为叙事挑读数）；[实测] 噪声底=0。
- **边界**：PARTIAL-U 出件即触发终判条件决策（三条：协议修订/coverage 入判据/扩集数——主定夺选扩集数，即案 6；前两条冻结语义不动）。
- **复算**：`_r65_deploy_rollout_judge.py`；判读函 `runtime/loop/_r65_mail_rollout_verdict.md`。

## 案 6 · rollout n=100 终判案（v2 判据首用）

- **背景**：终判条件 3（扩集数）执行——n: 20→100（用户已批），seed 70000–70099 跨窗配对，判据零改动。
- **判据**：v2-final（案 7 程序产出）：成功率冻结语义+coverage 连续主判；T1=全量 100 集/窗（案 7 审定修订执行）；T2=主配对 Wilcoxon 辅 MWU 中位并陈。
- **材料锚**：四窗 material_sha16（A1O=`ac828a7c84140750` / A1N=`1b203d540b13f288` / A2F=`7cf97b340c6524ab` / A2N=`90b6c0a7e8724935`）；四窗 summary 与 v5 自报逐一互证全等；本地镜像 `runtime/rollout_mirror/pusht_rollout_20261003_144237_n100/`。
- **判读**：①[实测] 冻结语义成功率四窗全 0/100，地板依旧，照报；②[实测] coverage 连续主判显著——配对 Wilcoxon p=0.00181，meanΔ=+0.081（中位 0.0，正/负 40/24，36 局逐局全同），辅 MWU p=0.06579；③[实测] 噪声底 A2F/A2N 逐局 100/100 全同（p=1.0，确定性）；④[实测] 臂 1 底敏感性 p=0.05063（含 v1/v2 协议混杂不作纯底）；⑤终判：修复方向显著有效（帧级 p=0.0099+任务级 coverage p=0.0018 双级一致），**达标性未证实**（FULL≥0.95 无一窗触及，成功率 0）。
- **边界与止损**：判据零放宽，seed 序列不换，不再扩 n——**止损线生效**。首案归档口径="帧级有效/任务级未证实"（预注册 NS 分支即此，未走到但结论同型：达标性未证实）。
- **verdict 正本**：`runtime/loop/_r73_n100/rollout_n100_verdict_v2.json`（schema v2 compliant；findings 为 10/4 装订校验时从 verdict 语句拆分补录，判断内容零改动）
- **复算**：`_r73_pull_n100.py` → `_r73_n100_judge.py` → schema 校验；A100 正本 `/root/vdd3/pipe_art/pusht_rollout_20261003_144237/`（评测脚本 `/root/pusht_rollout_eval.py`，PUSH_ROLLOUT_N_EPS=100 可复跑）。

## 案 7 · 判据演进程序化案（v1→v2-final 全链，含 T1/T2 审定）

- **背景**：案 5 地板触发判据 v2 草案（#2551）→ 用户批准（#2568，宪法十三条①留痕）→ compass 技术审定（#2574）→ v2-final 冻结。判据如何合法演进的程序判例。
- **程序链**：
  1. #2551：v5 提 v2 预注册草案（coverage 连续主判+五级刻度 FULL≥0.95/MAJOR≥0.5/PARTIAL≥0.3/TOUCH≥0.1/FLOOR）。
  2. #2568：用户裁"批准选项 1"；追溯边界=旧 20 集作废不追溯，扩 n 材料按 v2 判；判据演进记录义务 v5 认领；文档正本升级 v2-FINAL 留批准痕迹（v5 仓 `docs/PUSHT_JUDGE_V2_PREREG_20261003.md`）。
  3. #2574 compass 技术审定：程序合法审定通过（用户已批+预注册+止损线锁定防加注）+**两条修订冻结前补**：
     - **T1 样本锁死** [实测]：函称"60 集/窗取前 50 配对"vs 实际 env_fingerprint=100 集/窗（A1O 已 100/100）——选择自由度=可挑数据风险，修订为全量；
     - **T2 两法裁决规则**：主=配对 Wilcoxon 辅=MWU，防边界挑显著；附注中位并陈（重尾下均值×2.02 而非显著实证）+噪声底预期 0。
  4. v2-final 冻结后材料落盘即判（案 6 执行，NS 亦明判）。
- **claims**：[实测] T1 自由度差异（60 vs 100）；[推断] 选择自由度风险→修订建议（被采纳执行）；[实测] 程序四要件（批准/预注册/止损/记录）逐项在档。
- **边界**：判据宽松化的裁决权在用户，不在判读方与材料方任何一侧；审定方（compass）对程序合法性出具意见，不代用户批准。
- **复算**：函 2551/2568/2574 正文（DB org_mailbox）；五级刻度适用样例=案 6 判读。

## 案 8 · 口径裁定合订案（燃料入池判据三连裁）

- **背景**：外部素材三类请审——v5 路B 调用 DB 骨架重建（#2537→裁定 #2553）、platform 残单②重建口径（#2572 委派裁定）、errata 供给三案（#2660→裁决 #2667）。同一条判据原则的三次独立适用。
- **判据**：P3 语料白名单四类（`independent_recompute / human_review / official_rule / three_vendor_final`，反自指护栏：判官自产标签永久禁入）；对账件归档不占燃料计数；"只许更严"。
- **三裁**：
  1. **#2553 燃料骨架裁定**：三不可验（意图/观测/归因）成立——同意不建重建器（邻接假关联比无用更有害）；重建前置三条（结构化本体/推理文本/显式单号归因）补齐按新件送审，无降级通道；对账件归档+sha16 锚定。
  2. **#2572 残单②裁定**：弃重建（与 #2553 骨架裁定同链，富集度低换不来可验性增量）；四验门维持关闸；解闸=前置三条，无降级通道。
  3. **#2667 errata 供给裁决**：A/B/C 三案全接+label_origin 分层映射——独立复算链过的（E3/E4=independent_recompute）入燃料，自勘类（E1/E2=self_recompute）归对账件不入计数；机构判读行暂作装订素材不直接入 P3 燃料（label_origin 扩展须走只许更严程序）；首训练单不凑数（存量 <15 条距 200 触发线远，L6 时点后移等增量）。
- **claims**：[实测] 三案裁定逐条在档（DB 函件）；[推断] "邻接假关联比无用更有害"——训练燃料污染风险判断，upgrade_path=前置三条补齐后的新件送审可翻转。
- **边界**：裁定不因供给可得性放宽（v5 自身初判与我方同结论，双向不为凑数开口子）；资本侧（对方如实报量级不凑数）判读方明示肯定入档。
- **复算**：函 2537/2553/2572/2660/2667 正文（DB org_mailbox）+`tools/p3_delta.py` 白名单门源码。
- **R123-R126 扩展(r79 批双判分器分裂合订)**:
  1. **#2994 四裁**(回函 3007/通报 platform 3008):r79 13 条 score 整体不采信结算闸门保持关→**R126 升 measured**(v5 #3018 回呈 13 条明细对表逐项吻合:prime 3×0.92+8×0.75 零方差/kairos 0.25/0.30 不可互译/伪 fail 同档);统一规即刻生效(单 evaluator+判据预注册先于判分+verdict 二值主判);伪 fail 三条追认隔离;f043 形态双标 prime 侧 0.55 作废(形态门前置)。
  2. **#3018 裁定⑤受理前置规**(冒名实锤:13 条 claimed_by=v5 但秒交 0.49-1.89s+asset 全 null+当事方自报零 claim 动作):claim→submit<60s 或 asset 缺失=受理即挂 U 态;主体脱钩=批级 U 态+通报 platform;prime 自家 31s OOD judge 单预挂 U 态。判分受理先验"谁 claim、谁交付、有无轨迹锚"。**R131 勘误(判绩账双向第 3 例)**:v5 #3040 撤回冒名段——秒交=批量登记常态(轨迹先行登记后补,writeback 通道),asset null=通道常态;裁定⑤触发器撤销,操作化修正为 v5 判据 v1 三门 2 版(claim 主体==source.operator+轨迹可回放)+前置条"定性异常前必先对账当事方产线痕迹";31s OOD 观察项撤销;r79 批 U 态维持(依据=裁①,非冒名)。立规方对称教训:采信误诊呈报且未要求产线痕迹对账=未验证即断言。

## 案 9 · gen4 全卷判读案(判官双向接口首演+EGR 缺口回流首用)

- **背景**:flywheel auto_judge_dispatch 首派(gen4 全卷,sha16 幂等)——判官"材料派发进/缺口报告出"双向接口的第一次完整走环。spec 两闸首例(判据 lock v1,freeze_chain sha 9b565f1c/990f3dbc,2026-10-04 02:40 用户拍板冻结)。
- **判据**:gen4_v1_criteria.lock.json v1——J1 金标贴合率(手部骨架 PCK)≥0.367 / J2 教师一致率≥0.85(止损线 70%)/ J3 单帧延迟<1s;止损=J1 与 MediaPipe 打平且 J2<70% 即停。
- **材料锚**:gen4_judge_materials_v1.tgz sha16=`bcf6754d15d3c0b8`(两版 eval 报告+log+train log+dataset 199 行)。
- **判读**(verdict=PARTIAL):
  1. [实测] J2a 教师一致率 0.04(2/50),objects Jaccard 中位 0.00,scene 词重叠中位 0.00——零一致;eval.log 逐条计数独立复算与材料自报**三读数零偏差**。
  2. [实测] J2b 弱任务口径 0.0333(2/60,文本粗判弱信号 caveat 如实并陈)与 J2a 同向。
  3. [实测] **J1 判不动照报**:模型无关键点输出头(训练目标=四维语义 JSON),预注册 J1(骨架 PCK)与数据格式不匹配——口径错位自方案 v0 即存在,非执行漂移。upgrade_path=模型侧补关键点头或新案注册语义判据。
  4. [实测] 止损条款实质触发(J2=0.04 远低于 70%)——执行侧停手回炉**正确**,止损确认。
  5. [推断] J3 21.9s/帧=裸 generate 无 vLLM 部署口径,是工程优化问题非模型能力否证;不改变止损判定(止损条款不含 J3)。
  6. [实测] 200 对教师数据不足以教会 7B 该语义生成任务(退化解实证)=**数据量下限锚点**。
- **EGR 首用**:gap_report{gap_layer=data, suggested_fuel=教师池扩 540+ 全量重训(新案)/任务降级二分类先行(新案)/判据侧预注册语义版 J1}——缺口回流 flywheel,回流消费回执待对方(2804 承诺)。
- **三件裁决**(函 2788):J1 口径错位=上游设计缺陷 U 态处置/止损确认停手正确/首选归档=200 对教师池下限锚点(不直接入 P3 燃料——白名单门判据不因可得性放宽,承案 8)。
- **边界**:判读方不出"该不该继续 gen4"的组织决策,只出读数+缺口回流;教师池数据本身不因判读被否定(判据对材料,不对人)。
- **verdict 正本**:`runtime/gen4_judge/gen4_v1_verdict_v2.json`(schema v2.1 compliant,gap_report 首个实弹)
- **复算**:`python tools/verdict_schema_v2.py validate runtime/gen4_judge/gen4_v1_verdict_v2.json`;eval.log 逐条计数脚本与底稿在 runtime/gen4_judge/(闭环函 2791)。

## 案 10 · gen4_v2 B 轨二分类判读案(EGR 回流首闭环+多数类基线 caveat)

- **背景**:案 9 EGR gap_report{gap_layer=data, suggested_fuel=任务降级二分类}回流后,flywheel 产出 B 轨降级案(同 200 对教师数据,四维语义 JSON 生成→valid_frame+hand_present 二分类 LoRA)送判(#2905)。判官双向接口"缺口报告出→材料按缺口建议回流→再判"的第一次完整走环闭环。
- **判据**:gen4_v2_btrack_criteria.lock.json(sha16=`82b3cef1212db956`,2026-10-04 13:30 用户拍板冻结)——J1b valid_frame+hand_present 二分类 match rate≥0.85(60 对弱任务,CI±~9pp caveat 按初步通过申报)/止损线 J1b<0.70 不进 A 轨。
- **材料锚**:eval_report.json `37f71237cf98d125` / 事故卷 eval_report_step500_invalid.json `88943387d8557611` / eval_step2000.log `ad1b0bce9136fda6` + eval.log `ddbbd85da2963a70`(**函申报仓路径在 commit 7e05d2c 树内缺席,判官实例侧 /root/vdd3/gen4_v2/ 同 sha 取证,材料缺口如实告知**)/eval_set.jsonl 60 行。
- **判读**(verdict=PARTIAL):
  1. [实测] J1b=0.8667(52/60)≥0.85 过线——log 逐条计数独立复算与自报零偏差(两卷四读数),金标交叉 60/60(首验假绿已纠:eval_set 无 id 字段,改行序对齐),盲探正卷 3/3。
  2. [实测] **多数类基线 0.7833(材料方未报,判官补测)**:金标分布 47/60 全 True。正卷对基线增益单尾 p=0.0739 不显著,Wilson 95% CI=[0.7583,0.9309] 覆盖基线——60 对弱标集无法区分"学会判别"与"偏向多数类",caveat 实质化,"初步"权重大。
  3. [实测] **H2 主因定谳**:同 200 对数据,B 轨 0.8667 vs v1 四维生成 0.04——任务粒度过细=v1 失败主因实证;案 9 gap 排序修正(H2 主/H1 降次)。边界:只证"四维生成超当前粒度",不证"二分类已吃满数据"。
  4. [实测] step500 事故卷(ckpt 字典序 bug `step2000`<`step500` 致错卷)完整留档未删,盲探 0/3+weak 0.5667 与正卷对照构成训练过程证据——如实申报纪律正面记档(material_side_honesty 同型)。
- **三件裁决**(回函 2918):①J1b 初步通过成立(判据零放宽+caveat 并陈,终判=人工金标抽检 20-50 例+扩集≥200 对)②H2 定谳③A 轨暂不发车(建议顺序=判例→金标抽检接判官市场→粒度阶梯新案按需发车)。
- **EGR 二发**:gap_report{gap_layer=data:评测集侧缺口(弱标=MediaPipe 自动口径未标定+样本量)}——suggested_fuel 三条,confidence=measured。
- **边界**:多数类基线对照作 caveat 权重证据并陈,不进判定(判据零放宽,lock 语义=点估计过线+CI caveat);抛硬币基线 0.5 vs 多数类 0.7833 口径在函件中精确化(函称事故卷"≈随机基线"需勘正)。
- **verdict 正本**:`runtime/gen4v2_btrack/gen4v2_btrack_verdict_v2.json`(schema v2.1 compliant;含 statistics 段——verdict.text 提及显著性数字即触发 L4 检查的机构自律样本)
- **复算**:`python tools/verdict_schema_v2.py validate runtime/gen4v2_btrack/gen4v2_btrack_verdict_v2.json`;log 逐条计数脚本随 runtime/gen4v2_btrack/(log 本体实例侧锚 sha16)。

## 案 11 · V4 效用闭环探针判读案(分辨率单变量隔离+J2 判定权边界)

- **背景**:flywheel V4 探针送判(#2925)——gen4_v2 B 轨 ckpt(step2000)在输入分辨率三档(native/d128/d96,LANCZOS 短边)下的效用对照,GT 不变,60 对 held-out 池与 J1b 同池。效用闭环首件,用户 10/4 拍板立项当日出数。
- **判据**:v4_probe_criteria.lock.json(2026-10-04 冻结,预注册先于出数)——V4_J1=drop128≥0.15 成立/<0.05 未证实/其间 partial;V4_J2=drop96 **lock 明文 gradient evidence only 无判定权**;自检门 native replay 0.8667±0.03+盲探 3/3。
- **材料锚**:v4_report.json `52f9e72c9001f077` / v4_detail.jsonl `f5efce52d8e7c8d3` / v4_probe.log `2d4b1af40b5c518f` / .v4_done `e1464b772bbbc048`(**函报仓路径在 2e0af3e 树内 404,实例侧取证**——连续两案同缺口,产物落仓入升级惯例);判据 lock+探针脚本 GitHub 2e0af3e 直取。
- **判读**(verdict=PARTIAL):
  1. [实测] 三档读数逐行复算零偏差(52/47/37 每 60),drop128=0.0833、drop96=0.25;探针自检三重过(盲探 log 实读 3/3、replay delta=0.0、金标分布同池一致)。
  2. [实测] V4-J1 PARTIAL 按零放宽成立——但判官补测**同帧配对 McNemar p=0.267 不显著**(对错 9/错对 4),较函申报 CI±9pp 口径更保守:"128px 实质损害"不足以单独宣称。补测检验法未预注册,只作 caveat 权重证据不进判定。
  3. [实测] 损害形态=判别力渐失非多数类塌缩:d128 预测 True 42/60、d96 24/60 单调渐降——与案 10 J1b caveat"偏向多数类"担忧可区分。
  4. [实测] J2 梯度坐实(配对 p=0.011+单调+resolution 检 franka 128/pusht 96 双 WARN 互证)但**不升格**:lock 未赋判定权,预注册纪律=判官不代赋权;明示口径=可入首报"方向性发现"探索段(标注 PARTIAL/扩样中),结论宣称等扩样≥200 对;升格走判据演进程序(承案 7 三要件)。
- **EGR 三发**:gap_layer=data——60 对样本量卡住效用维终判;扩集≥200 对与 J1b 同池复用(一池两判)。
- **边界**:未预注册的检验法不进判定只作并陈证据;resolution_check/franka_diving 作为互证材料在链,aloha_ins_qc_v0/xarm_qc_v0 无函不抢判(问询函 2930 已发)。
- **verdict 正本**:`runtime/v4_probe/v4_probe_verdict_v2.json`(schema v2.1 compliant,一次通过)
- **复算**:`python tools/verdict_schema_v2.py validate runtime/v4_probe/v4_probe_verdict_v2.json`;detail 逐行计数+McNemar/Wilson 随 verdict readings 段可查。

---

## 案 12 · V4-J2 首判 established 案(J2 升格后判定主权行使第 2 演+止损 a CI 复核首例)

- **背景**:承案 11——V4-J2 当时 lock 明文 gradient evidence only 无判定权;用户 10/4 批"两件都批"(J2 演进启动+帧包上云,flywheel #3013 落地),新 lock(fa866e4)赋判定权并呈首判,判定主权归 compass(止损 d)。
- **判据**:`v4_j2_criteria.lock.json` @nautilusflywheel@fa866e4(判官 gh api 直拉原文,不采函面转述)——drop96 ≥0.15 established / <0.05 not_established / else partial;McNemar 只作效应确证;四止损(a CI 下缘/b 模型换代/c 池污染/d 判定主权)。
- **材料锚**:V4V2 复测判官档四件(案 10 同源,report 97baa15b/detail 0c7b3b1c/eval_set 5e89a66a/probe 825fe6dd);首判零新增算力(复用已出读数,lock budget 条款)。
- **判读**(established,回函 3023):
  1. [实测] drop96=0.8550−0.5500=0.3050 ≥0.15 门字面 established;联合表(判对指标)n11=89/n10=82/n01=21/n00=8 与判官档 McNemar b=82/c=21 **逐位复核一致**。
  2. [实测] 止损 a 复核(首判呈请点名项):Newcombe paired CI95=[0.2118,0.3911]+bootstrap 同 i 配对(seed 20261004)=[0.2150,0.3900],双法下缘均 >0.15 不触发——首例把"配对差值 CI"从函面要求落到双法实算。
  3. [推断→流程教训] 判官首算把判别字段(gold 阳性判定)误当通过率(p1=0.92≠0.855)——红灯停,查字段语义按 native==gold 重建,边联合对上方出数;判别型评测 accuracy=(TP+TN)/n 不是 pass 率,入判读惯例。
  4. 止损 b/c 无触发证据;b/c 状态随批记档(c:v2 池零重叠+对齐零不一致承案 10 复验)。
- **效果域限定**(lock effect_scope 照录):hp 任务粒度+B 轨 step2000 消费者画像+resolution 检 WARN 低分辨率集;跨任务/跨基座不自动沿用;resolution 维仍 report-only。
- **verdict 正本**:裁定档 `runtime/loop/_r125_3013_j2_first_verdict.md` + 判官档 `runtime/v4v2_judge/v4v2_judge_verdict_v2.json`(双锚,案 10 compliant 承接)
- **复算**:联合表/双法 CI 随裁定档表列;判官档 `python tools/verdict_schema_v2.py validate runtime/v4v2_judge/v4v2_judge_verdict_v2.json`。

---

## 案 13 · G1 差分归因报告案(归因制式 v1 首件回填+非实现者复算闭环示范)

- **背景**:归因报告制式 v1(ATTRIBUTION_REPORT_TEMPLATE_V1,2026-10-05 用户拍"制式化优先")首件按制式回填——把案 1/案 2 的 G1 全弧(U 态→三修→差分终判)装订为制式八段报告 RPT-G1-2407。归因报告=装订线四件事之④产品化首件(装订收费物,榜面只引坐标不嵌全文)。
- **制式**:八段强制(识别/判定摘要/现象三层标注/归因链四层定位+每步可复算命令/修复建议≤3 带验收判据/反证自查/消费记录回填/判绩账回填)。
- **归因链定谳**:ratio 数千倍=数据层为主(静止段 ‖act−state‖~5e-5 分母近零)→判据层联动(幅度比对零增量帧无定义);未指向模型层。三修建议(①帧过滤≥1e-3 ②dir sign 语义 ③40帧5eps)全部实测验收。
- **消费记录 [实测]**:三修被受测方全采纳免二次往返;#2413 阈值参考被修复版对齐;"注入不传导"候选结论受测方单列挂账(same_form_watch);预注册语义差分实验回档主待材料。
- **非实现者复算(2026-10-05,fresh-context 复算人,md5 校验原始 JSONL 本地重算)**:**PASS-with-erratum**——16 项对表 15 项逐位一致(两臂 J1 0.85/0.825、J2 0.925/0.925、ΔJ1=+0.0250/ΔJ2=0、degenerate 0/0、ep 分布、act_state_norm 配对同值);**勘误一项 [实测]**:G 臂 ratio 中位数判读函声称 1.9863→复算 1.9861(偶数均值中位;成因=判读函 G 臂误取上中位而 B 臂用均值——两臂口径不一致;差 0.0002 不改方向性结论)。勘误追补不改史,统一口径为偶数均值中位。
- **判绩账双向第 5 例**:复算人抓出判读函内部口径自相矛盾——比判读方自查更深一层;"评委也会错,勘误留痕=信用资产"从判读侧延伸到归因报告侧。
- **边界**:归因报告不是新判读——以已出 verdict 为原料,不改变任何一案判据与结论;注入传导机制仍 [推断](upgrade_path=注入帧 vs 干净帧 pred 逐帧对比)。
- **verdict 正本**:`docs/metering/RPT-G1-2407.md`(判绩账段含复算全录);复算材料 md5 G=`7170892d3d940142a2afdd43d8b6346b` / B=`599c76a6f43f6c682080c56a9648d1e2`
- **复算**:报告§"非实现者复算坐标"(判读函底稿 `_r57_mail_g1_differential.md`+`mail_g1_verdict_supplement_20261003.md`;远端材料 `/root/vdd3/pipe_art/g1_infer_{G,B}/infer_compare.jsonl`;数据集直读=parquet 'index' 帧索引+episode_index 断言自校)

## 附录 A · verdict 正本与校验状态

| 案 | 正本 | schema v2 |
|---|---|---|
| 1 | `runtime/loop/_p3_g1_verdict_v2.json` | compliant |
| 2 | 函 2422（DB）+案 1 闭合 | （函件体） |
| 3 | `runtime/loop/_p3_pusht_4win_verdict_v2.json` | compliant |
| 4 | `/root/vdd3/pipe_art/pusht_pair_verdict.json` + `_r63_mail_pair_verdict.md` | （函件体/幂等件） |
| 5 | `/root/vdd3/pipe_art/pusht_rollout_verdict.json` + `_r65_mail_rollout_verdict.md` | （函件体/幂等件） |
| 6 | `runtime/loop/_r73_n100/rollout_n100_verdict_v2.json` | compliant |
| 7 | 函 2551/2568/2574（DB） | （程序档） |
| 8 | 函 2553/2572/2660/2667（DB） | （裁定档） |
| 9 | `runtime/gen4_judge/gen4_v1_verdict_v2.json` | compliant（v2.1，gap_report 首用） |
| 10 | `runtime/gen4v2_btrack/gen4v2_btrack_verdict_v2.json` | compliant（v2.1，EGR 回流首闭环） |
| 11 | `runtime/v4_probe/v4_probe_verdict_v2.json` | compliant（v2.1，J2 判定权边界样本） |
| 12 | `runtime/loop/_r125_3013_j2_first_verdict.md` + `runtime/v4v2_judge/v4v2_judge_verdict_v2.json` | （裁定档+判官档双锚） |
| 13 | `docs/metering/RPT-G1-2407.md`（归因制式首件,复算 PASS-with-erratum 随件） | （制式八段+判绩账回填） |

## 附录 B · 判读 SLA 与机构口径

- 判读响应惯例 <1h（材料落盘即判，三次实证）；verdict 幂等可重跑。
- 判读免费/装订收费；判据库与白名单门源码公开（`tools/p3_delta.py`/`tools/verdict_schema_v2.py`）。
- 判读叙事跟数字走；勘误双向（评委也会错，勘误留档=信用资产——专段见"勘误与判绩账"，案 2/案 4/案 8 扩展 R131/案 12/案 13 五例在档）。

## 附录 C · 版本记录

| 版本 | 日期 | 变更 |
|---|---|---|
| v1 | 2026-10-03 | 首装订（两线定价拍板的装订线首物，公开 demo 版免费） |
| v1.1 | 2026-10-04 | 补两线边界段+勘误与判绩账专段（四例）+版本记录段；案 8 扩展（r79 四裁 R126 补条+R131 勘误）、案 9-12 入集（gen4 两案/V4 探针/V4-J2 首判）；追补不改史 |
| v1.2 | 2026-10-05 | 案 13 入集（归因制式 v1 首件 RPT-G1-2407,含非实现者复算 PASS-with-erratum 全录与中位数口径勘误——判绩账双向第 5 例）；勘误与判绩账专段扩展至五例 |
