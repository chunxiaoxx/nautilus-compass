# Nautilus Compass 判分服务 · 流程总览(对外版 v1)

> 2026-10-04 编成(用户拍板"整套流程固化沉淀到平台网站")· 本页为上站底稿
> 坐标:github.com/chunxiaoxx/nautilus-compass · 判例集 `docs/cases/CASEBOOK_V1.md` · 提交协议 PyPI `nautilus-compass`(assay)3.3.0

## 一、我们是做什么的

第三方判分机构:你把 AI 系统的产出材料交来,我们按**事先公开、事先冻结**的标准独立打分,出带证据分层的判定书(verdict);判定可由任何人按公开命令复算;我们判错了公开认错。判卷不为委托方粉饰,负结果照报。

## 二、两线定价(2026-10-03 定)

| 线 | 内容 | 价格 |
|---|---|---|
| **判读** | verdict 出件:按预注册判据判材料,出判定书 | **永久免费**,不设付费优先队列 |
| **装订** | 判后事:判例集、认证背书、协议植入 | 收费(以已出 verdict 为原料,收费不改变任何一案判据与结论) |

判例集当前为公开 demo 版(免费):12 案全录,每案附材料指纹(sha16)与复算命令。

## 三、委托判读流程(五步)

1. **材料投递**:经平台信箱(to=compass)发函,材料落盘并附指纹锚(sha16);函数据与磁盘实物缺一不可。
2. **判据预注册**:判据先于判分冻结(criteria lock,版本+指纹可引);判据只许更严,冻结后不改;判不动照报"判不动",不以代理指标顶替。判据宽松化的裁决权在用户,不在判读方与被判方任何一侧。
3. **判读**:非实现者复算原则——判读方与材料实现方分离;verdict 二值主判,连续分数只作 caveat;每条结论性陈述标注证据层。
4. **回执**:verdict 经信箱回传,附复算命令;惯例响应 <1h(材料落盘即判,判例集附录 B 三次实证)。
5. **复算与装订**:任何人可按公开命令独立复验;判例按判例集程序装订,新案即装。

## 四、证据三层(每条结论必标)

- **[实测]** 材料直读/可复算;
- **[推断]** 带升级路径(upgrade_path),不得冒充实测;
- **[不可验]** 如实标注。
U 态(无法判定)与证据层独立标注;判读叙事跟数字走。

## 五、勘误双向(判官也会错)

判分机构的核心资产不是"从不出错",而是**错了必留痕**:勘误双向记录、追补不改史。判例集设"勘误与判绩账"专段,现有四例在档(含判读方自我证伪两例、立规方误诊撤规一例、判官首算红灯自纠一例)。

## 六、提交协议(机读面)

- **assay**(PyPI `nautilus-compass` 3.3.0):challenge 八件制式(qid/claim/artifacts_ref/original_verdict/reason/cause_tag/label_origin/confidence)+errata 勘误件;schema v2 校验 CLI:`python tools/verdict_schema_v2.py validate <verdict.json>`。
- **判据与白名单门源码公开**:`tools/p3_delta.py`(燃料白名单门)/`tools/verdict_schema_v2.py`。

## 七、反自指护栏(独立性声明)

判官模型自产的标签永久禁入训练燃料(白名单四类:independent_recompute / human_review / official_rule / three_vendor_final);判分机构对己方产品(判例集/assay/判官)同样执行非实现者复算——装订物不豁免任何一条判分纪律。

## 八、服务入口

### 人读首检入口(判据①补齐件 · 10/9 首演前挂)

- **首检邮箱**:`chunxiaoxx+external@gmail.com`(mailto;2026-10-06 用户拍板,与 HF 对外口径一致,公网部署随 platform 晨窗上站)
- 三行首检说明:
  1. 提交必含**被测物坐标 repo@commit**(harness/agent 仓库+精确 commit;私有仓走 HF 材料包+sha16),缺坐标不起判;
  2. **SLA:交付 ≤5 个工作日**,返工 ≤2,判据 sha 预注册(只许更严);
  3. 两档:**免费收录**(判读 verdict 入公开判例库)vs **$199 深度报告**(launch 价:归因链+复算命令+修复建议)。
- 首检模板:`docs/metering/JUDGE_INTAKE_TEMPLATE_V0_20261006.md`——人读件字段与 assay 机读面一一对齐,填完直接进判分流程。

### 机读面与其余入口

- 平台信箱:to=compass(委托/问询)
- 仓库:github.com/chunxiaoxx/nautilus-compass(判例集/判据库/工具源码)
- PyPI:`pip install nautilus-compass`(assay 提交协议 3.3.0)
