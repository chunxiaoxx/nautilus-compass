# 14B 升格 U5 对拍分歧对账(2026-10-05,R167;附属于 PREFOR_JUDGE14B_UPGRADE_20261005.md)

> 材料:292 条 held-out(split_dev+split_test)同集对拍逐条读数回拉件 `_r167_eval292_14b.jsonl`/`_r167_eval292_17b.jsonl`(A100 正本 `/root/vdd2/judge14b_upgrade/eval292_*.jsonl`);全部 [实测] 层(逐条 ok 字段直接计数)。

## 四象限(与 report agree_disagree 一致)

| 象限 | n | gold 分布 | 错误方向 |
|---|---|---|---|
| both_ok | 239 | — | — |
| only_17b(14B 错) | 25 | pass 23/fail 2 | 14B:pass→**fail** 23 例(偏严厉) |
| only_14b(1.7B 错) | 14 | fail 10/pass 4 | 1.7B:fail→**pass** 10 例(偏宽松) |
| both_wrong | 14 | pass 11/fail 2/IE 1 | 双双错成 fail(共同盲区) |

## 判读(三层)

1. [实测] **错误方向不对称**:14B 的分歧错误集中在错杀侧(pass→fail),1.7B 集中在错放侧(fail→pass)。验证场景下错放(把错判成对)危害大于错杀(保守方向损失)——1.7B 的 10 例错放属危险侧偏差,14B 的偏严厉属安全侧偏差。**但 U5 门=gold 一致率,预注册口径下 1.7B 仍胜(0.9041 vs 0.8664),"保留现役"判读不变**;错误代价不对称的重定义属判据演进,须走判据演进程序(用户裁,承案 7),判官不代赋权。
2. [实测] **来源族集中**:三象限均以 lme 族为主(only_17b 23/25、only_14b 11/14、both_wrong 11/14)——分歧与共同盲区都聚集在同一语料族,判别力差异主要在 lme 分布段,非全局能力差。
3. [实测] **共同盲区**:both_wrong 14 条(11 条 gold=pass 被双判 fail)——两代判读器在同一批 lme pass 题上同错,提示该段语料的 gold 或题面存在系统性难点(候选:题面歧义/gold 边界),upgrade_path=抽 both_wrong 原始题面人工复核,若 gold 有误则走 errata 活水(判分器语料勘误先例)。

## 对 upgrade_path 的修正充实

原档三条(bf16 对拍/超参 sweep/语料扩容)保持;本对账新增两条:
4. 错误代价不对称判据(错放加权)——如采纳走判据演进程序,14B 或反转优势;
5. both_wrong 共同盲区 14 条人工复核——gold 勘误活水优先级高于盲目扩容。

## 复算

`python -c` 逐条计数脚本随本档结论可复现(输入=两 jsonl,输出=四象限+交叉表+来源族计数);SHA 本地回拉件与 A100 正本同源(sftp 直拉)。
