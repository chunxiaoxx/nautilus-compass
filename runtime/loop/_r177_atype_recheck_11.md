# A 型 11 条截断修复复验 · 验收档(2026-10-05,R177)

> 判据(预注册 `_r168_bothwrong_audit.md` 建议一,只许更严未动):A 型 11 条(both_wrong 截断型)同 id 用 v1 语料(response 全文)复评,**≥7/11 转对**为过门;不回升=截断非主因,照报负结果。
> 复评执行:A100 223.109.239.30,champion 现役 1.7B(Qwen3-1.7B bf16 + champion_17b_lora),判读管线与 U5 对拍逐字节同源(import `train_judge14b_upgrade.py` 的 PROMPT_TMPL/sample_text/evaluate,该文件有 `__main__` guard)。

## 结论:**FAIL(1/11 转对,门 7/11)** [实测]

- 逐条读数:`atype_recheck_result.json`(A100 /root/vdd2/judge14b_upgrade/,本地镜像 `runtime/loop/_r177_l3smoke/atype_recheck_result.json`)
- 方向:9/11 pred=fail gold=pass(拒答型陷阱题仍被判未回答),1/11 pred=pass gold=fail(4b0c5275,反向),1/11 转对(191184f3,conf 0.707)
- 置信分布:错判 10 条中 7 条 conf≥0.95,最低 0.73——**高置信一致错,非信息不足的犹豫**

## 归因修正(对 R168 复核档)

1. [实测] 截断缺陷坐实且已修复:v1 语料 11 条 response 全文 226-501 字符(v0 一律 200);但**修复不足以转对**——"截断主因"假说被本组读数证伪。
2. [实测] 探针自证伪:sample_text 的 `[:400]` 字段截断仅触及 1 条(501 字符),其余 10 条输入完整;管线与 U5 同源,U5 时该 11 条同为 both_wrong(0/11→1/11,变化微小,管线自洽)。
3. [推断] 现行主因假设升格:**判读框架对"正确拒答/指出不存在"类(lme 陷阱题族)的系统性偏置**——PROMPT_TMPL 语义("submitted artifact vs official reference, decide whether correct")+训练分布使"拒答式回复→fail"成为强先验;截断是该偏置的放大器,非根因。gold 侧可信度:R168 已人工复核 gold 语义(官方 harness 判定,"环境里不存在 X,正确行为=指出不存在"),维持。

## 影响修正(如实)

- v1 语料重导出(空题面 52→0+截断修复)仍是净收益:信息对称达成,判读输入不再缺结论段;
- 但"语料修复后判读读数整体上修"的预期对 lme 陷阱题族**不成立**;14B"待语料增长再评"若只增同类语料,预期无差;
- 上修需判读框架层修复(见 upgrade_path)。

## upgrade_path

1. 判读器侧:对"正确拒答"类做小规模校正 SFT(判分器微调,走反自指护栏:自训只限小判分器+外部 gold);
2. gold 侧:A 型族抽样二盲评(第二判读通道交叉),排除 gold 系统偏移(当前证据不支持,留门);
3. 语料侧:陷阱题族打 `refusal_correct=true` 类别标注,供判读侧与训练侧分别消费。

## 边界

- 本档不改动 v1 语料、champion 判读与任何已出 verdict;复评执行者=compass 会话(实现者复评,非独立第三方——独立复算可按本档坐标在新鲜会话重跑);
- sample_text `[:400]/[:1500]` 截断为现役管线既定行为,复评未放宽判据。
