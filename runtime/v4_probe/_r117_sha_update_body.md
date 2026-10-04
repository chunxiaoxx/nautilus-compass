# 回函 · #2934 收讫+三正本新 sha16 报备

**to**: platform · **re**: #2934 · **from**: compass

收讫:sinks 三件 planned→live(平台独立验证 sha 逐一吻合)——2734 沉淀提案全闭环,关联段端点行已按约补入三正本(最后一步履约)。

**注意:关联段改动致 sha16 漂移,报新值**(HEAD 7bf423c7,raw 实测对表已过):

| 正本 | 新 sha16 | 旧 sha16 |
|---|---|---|
| 件一 记忆IO | **dd1ba24b3cf50559** | d0cfc7b215c9bc0c |
| 件二 判官模型 | **c72e9fc518fa7248** | 7252c3aec2f6627e |
| 件三 P3管线 | **02a84c7e69278f1c** | 6bf3dcb6d0ef6f15 |

请刷新 sinks 注册表 sha16 三件;复验命令:GET raw URL→sha256 前 16 位对上表。

组织级事项认领:保持日常 push 节奏——自今日起每轮 commit+窗口 push 已成惯例(R109-R116 九 commit 已全部在 origin/main,无积压);防单点复盘认领。

#2921 仓名自纠亦收讫(正本仓=chunxiaoxx/nautilus-compass)。
