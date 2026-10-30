# CS-007 V2 深化包 5×4 净场重判 · 判分反馈(收工档)

> 承:`CS007_V2_5x4_PREREG_20261030.md`(预注册档,判据冻结,本文不含预期读数回填)。
> 响应:v5 函 24130(platform-202610301210-compass)委托"净场管道 5×4 重判 + 判分反馈"。
> 纪律:非实现者复算待另起新鲜会话;本档每条结论性陈述标注证据层。
> 回函 trace:platform-202610301210-compass · 2026-10-30 16:5x 收工(R245 值守轮)。

## 一、执行账

- 单批 4 渠道 × 4 轮 = 16 轮串行,13:26 点火,16:4x 收官,总耗时 178.1min [实测](batch_5x4.log 尾 [ALL-DONE])。
- 净场五条继承 CLEANFIELD_RERUN_PREREG §三(冲突标记 0/双 md5 留痕/行为抽验/无 merge 备份件/score 与 ut_vector 双侧一致)[实测·自查通过]。
- k3 按 #21909 暂停,qwen 走百炼直连车道;实际参判 4 渠道。

## 二、16 轮读数 [实测]

| 模型 | run0 | run1 | run2 | run3 | 均分 | 全对轮 | passrate(整题全对率) |
|---|---|---|---|---|---|---|---|
| gpt-6-astra | 0.9722 | 0.9722 | 0.9444 | 0.9444 | 0.9583 | 0/4 | 0.00 |
| opus5.5 | 0.9444 | 0.9444 | 0.9444 | 0.9444 | 0.9444 | 0/4 | 0.00 |
| qwen3.8max | 0.9722 | 0.9722 | 0.9444 | 0.9167 | 0.9514 | 0/4 | 0.00 |
| glm5.3 | 废 | 废 | 废 | 废 | — | — | — |

- glm5.3 四轮全废:run0 raw_len=168142 纯 reasoning 无 files 产出;run1-3 content empty(reasoning_tail 泄漏,补跑仍废)[实测]。有效读数 12/16 轮。
- score 记分口径:36 UT 全量(test_cs007.py 28 + test_cs007_origin.py 8)。

## 三、UT 分层聚合 [实测](12 有效轮)

- **基线层 22 UT:三模型 × 4 轮全部通过(88/88)**——基线层零区分度。
- **深化层 6 UT(坑A×2 + 坑B×3 + 坑C×1)**:
  - 5 条白给(`cache_alias_parallel_killed`/`cache_hardlink_same_class`/`pkg_import_vs_fileload_same`/`mirror_pkg_reference_identity` 三模型全 4/4;坑A 两条同):零区分度 [实测];
  - **1 条恒挂:`test_cache_stale_entry_killed` 三模型 × 4 轮 = 0/12 零通过** [实测]——唯一全模型死卡点;
  - 1 条异质:`test_concurrent_load_identity` gpt 4/4·opus 0/4·qwen 2/4 [实测]——模型差异签名,非题难签名。

## 四、甲方判据五条件对照(净场实读)

| 条件 | 净场实读 | 判 |
|---|---|---|
| ① 五模型各 4 轮 | 有效模型 3/5(glm5.3 全废·k3 停) | ✗ |
| ② 整体全对率 <70% | 0/12 = 0% [实测] | ✓ |
| ③ opus 全过轮 ∈[1,3] | opus 全过轮 = 0(每轮恒挂 2 UT) | ✗ |
| ④ qwen 双低且 ≥1 轮零分 | qwen 均 0.9514,零分轮 0 | ✗ |
| ⑤ qwen passrate ∈{25%,50%} | 0% | ✗ |

四条联合(梯度≥15pp + qwen∈{25,50} + opus∈[1,3] + 整体<70%):梯度 = qwen−opus = +0.7pp <15pp ✗。**五条件仅②单条达标,联合判定不达标。**

## 五、预注册判定门裁定(§三)

- **"过深"条款①**(opus 4 轮全部挂在深化层):字面命中——opus 每轮挂的 2 UT(cache_stale+concurrent)全在深化层,基线 22 条全过 [实测];但括号语义("深化层恒挂=修复面超出 loader 局部重写")仅对 2/6 条成立,深化层 4/6 条 opus 全过——**"过深"语义不成立,题的故障模式是过简+单点死卡,不是过难** [推断,依据分层聚合]。
- **"过深"条款②**(失败签名单一 share≥100%):不命中——深化层失败池 18 UT-轮对中 cache_stale 占 12/18=67%,concurrent 失败异质 [实测]。
- **"可保留"门**(≥1 强模型部分修复深化层 且 四条联合):前半部分面成立(深化 5/6 条被全修),但四条联合全崩(梯度+0.7pp·qwen passrate 0%·opus 全过轮 0·五条件仅②),**不命中** [实测]。

**两门均不干净命中 → 按预注册"给 v5 一句话结论+证据"如实报第三态,裁定权归 v5。**

## 六、一句话结论(给 v5)

**CS-007 V2 深化包净场终判:题仍过简(基线+深化 11/12 UT 白给,前沿模型均分 0.94-0.96),唯一硬度来自 `test_cache_stale_entry_killed` 单点(三模型 12 轮零通过,疑 UT 自身缺陷或真死坑,未定谳),甲方判据五条件仅②达标——深化方向无效,建议该 UT 单点复核后重设计深化层,坑版不必回撤(回撤会更过简)。** [实测+推断混合:读数实测,"过简"判定实测,"UT 缺陷疑因"推断]

## 七、upgrade_path

- `cache_stale_entry_killed` 0/12 恒挂成因:compass 侧未做 UT 有效性复核(ut_runner 退化 1UT 陷阱既有教训,ali-codesense-contamination-20261029)——建议 v5 或下一轮人工审该 UT 断言是否可达;[推断,升级动作:行为级复跑+断言审读]
- glm5.3 content empty 成因:reasoning 尾巴吞 content,渠道层问题非题问题,候渠道表处置;
- 本判分为单会话产出,非实现者复算(新鲜会话,只信判据与自测)未执行——U 态:本档在"复算未做"维度为 U,读数本身为 [实测]。

—— compass 判分值守 R245 · 2026-10-30 16:5x

## 八、v5 复核定谳回执(2026-10-30 · 函 24216 · trace compass-202610301330-v5-cachestale-verdict)

§六/§七 upgrade_path 第一条已闭环——v5 三框架复核走完,定谳如下(此处仅录正本,compass 无异议):

- **①断言自洽性 ✓**:金标 V2.2(inode+mtime_ns 键·21fd0bc2)自身全绿,存在可过的合法实现,非绝对不可过;
- **②UT 越权实锤**:task.toml boundary 行 82 明示"缓存键选型(路径/规范名/content hash)不考察(等价门覆盖)",cache_stale 判定差异恰落在该明示放弃的维度上;且 task.toml badpattern 名单(行45-52)不含该三条缓存 UT(名单外考题);
- **③零通过可推导**:模型遵从 boundary 声明→自然不实现选型敏感键→撞 cache_stale 必挂。

**定谳:cache_stale = UT 自身缺陷(越权考题),非真死坑。处置候裁二选一(剔 UT 或 boundary 解除声明+重写 UT+重跑),属题目侧调档,归 v5/bait-loop,compass 判分岗不越位。**

**连带定谳:CS-007 V2 剔 cache_stale 后 27/27 全绿 = 过简出局,与 v1 同判(§五"仍过简"结论成立)。007 深化方向无路,重造=回素材原点换载体配方,候 v5 定。**

**compass 判分口径注记(即刻生效):后续任何 CS-007 系卷面复判/再判,cache_stale UT 一律按"越权考题剔除"口径处理,不再计为死坑证据;本档 §五/§六 结论不变。**[实测:定谳原文见函 24216;注记为 compass 执行口径]

—— compass 判分值守 R248 · 2026-10-30 19:0x

## 九、cache_stale 处置定谳更新:选 B 正名,§八剔UT注记废止(2026-10-31 · 函 24229 · trace compass-202610310350-v5-cachestale-b)

v5 裁决:**解除 boundary 第 3 条声明·cache_stale 键选型纳入考察(非剔除)**——判据只许更严,合规。四理由:①cache_stale 测题核心语义,剔=自废武功;②B11V2 七刀教训:加刀不如正名(policy/boundary/UT 三位一体合法化);③净场纪律"只许更严";④007 平行类证据链已抓到(sys.modules 双键同文件,sensors._loaded.camera 缓存键与官方规范名键同源冲突,证据 _diag_parallel.py 在 v5 仓)——正名后修 loader 即闭环。

**§八"越权考题剔除"判分口径注记自本节起废止。新口径:cache_stale UT 恢复计入,按正名后 boundary V3 处理。§五/§六"过简出局"结论不受影响。**

compass 已办(函 24229 请办两件):
- ①boundary V3 修订版采信并同步:两份正本 task.toml(构建 `runtime/scratch_cs007v2/task.toml` + 判分 `runtime/scratch_cs007v2_judge/codesense/items/CS-007/task.toml`)第 3 条已换为 V3 修订版,两份 md5 一致(1bf2820f4ae1732ee670c332a4072993),gate0 复跑 PASS;
- ②cache_stale 重判**候 v5 loader 修**(扫描循环优先序/_loaded 注册时机,v5 明晨 fresh 调试)——loader 修毕即触发净场重判,本档届时追 §十。

—— compass 判分值守 R249 · 2026-10-31
