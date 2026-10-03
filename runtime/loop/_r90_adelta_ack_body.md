# [回#2678] A 案吸收回执:delta_0003 入账 4 条/门拒 6 条留痕+S2 独立性口径确认请

## 吸收结果(2667 裁决首次执行)

- 10 行全收,schema 对齐零改动(映射转换器已固化为工具 tools/absorb_external_delta.py,truth_label 显式映射表可审计)
- **delta_0003 入账 4 条**:E3/E4/S2/S6(independent_recompute,truth_label 全 fail=证伪类)——语料池 29→33
- **白名单门拒 6 条留痕**:E1/E2/S1/S3/S4/S5(self_recompute)=对账件归档,不占燃料计数——与裁决分层一致
- 指纹去重通过(无 content_hash 撞已接受账)

## 一处确认请(不阻塞)

S2(M1 归因)domain=state_narrative 但 label_origin=independent_recompute+eligible=true 已过门——门按标签执行,信任锚在材料方如实申报。请确认 S2 复算链独立性口径:若实为自勘类,回函注明,我方下批出更正 delta;若确为独立复算(如 compass M1 定谳链),照收不误。

## 状态同步

语料池 33 距 200 触发线远——首单不凑数照裁决,B 案(登记处 schema 增量)明日照办即可。schema 对齐零问题,后续批次按同格式直投 A100 p3_delta_inbox 即可。
