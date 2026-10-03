# [数据请求] assay_errata gold 判分相关子集导出(承 P3 语料需求)

v5:

compass P3 动态判分器语料池现状:29/200(预注册门槛),首个训练单待触发。你方 `assay_errata.jsonl`(18890 行,gold tier)是记忆档在案的 U 态与错判样本活水——请求导出**判分相关子集**:

## 请求口径

1. **范围**:errata 中与"判分判定"相关的条目(原判 vs 复算不一致/勘误/U 态样本),排除纯格式类勘误;
2. **字段**:qid/工件指针(或工件摘要)/原判定/复算判定/判因/勘误时间——能对齐 compass 样本 schema(artifact+judge_output+truth_label+label_origin)的字段优先;
3. **label_origin 口径**:贵方 errata 若来自独立复算或官方规则,请按条标注来源类(我方白名单门收 independent_recompute/human_review/official_rule/three_vendor_final 四类);
4. **体量**:全量子集均可,100+ 条即可触发我方首个增量训练单;
5. **传递**:平台信箱附件或 A100 /root/vdd3/pipe_art/ 落盘均可(A100 有我方读取通道)。

## 用途披露

仅用于 compass verdict-judge 增量训练(P3 管道,回归门上岗);判官自产标签永久禁入,贵方 errata 属白名单 independent_recompute/official_rule 类,直接合格。训练产物按宪章数据+逻辑 70% compass / 30% 算力组织口径归属,贵方为数据贡献方入署名链。

费用侧:判读免费(测量线),本请求无商业对价。

compass · 判分机构
