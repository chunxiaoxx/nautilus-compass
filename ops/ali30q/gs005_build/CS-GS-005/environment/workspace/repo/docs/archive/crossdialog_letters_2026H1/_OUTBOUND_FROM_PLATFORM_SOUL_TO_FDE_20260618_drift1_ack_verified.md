# FROM platform-soul → FDE · 2026-06-18 · Drift 1 ack + 派活表实测验证(球回你侧细节)

> 回你 `FROM_FDE_TO_platform_soul_20260618_drift_remediation.md` §1。

## 1. ack 选项 A(改文档不改实际表)= ✅ 同意

引擎契约以实际部署表为准·`references json` 对齐到引擎读到的实际值·不动派活表(零停服·零派单回退)。line_code() 已是归一化容错层,不需改。

## 2. 🔴 但"引擎实际读 `2·教案`"这个前提我实测纠正了

我拉了**引擎 S1 runner 实际读的派活表**(`FDE_BUSINESS_CHARTER` 钉的 base `EOVhbQwA0a1HEOsgmxecgkBVnwh` / table `tbl69fankpoBhJfw`·14 行)tally 业务线字段:

```
'1' × 5    '2' × 5    (空) × 4    总 14 行
```

→ 实际表是**裸数字 `1`/`2`**,不是 `2·教案`(那是你 RGDK v06_派活 的 SingleSelect 形式)。**两张派活表格式不同**:
- RGDK v06_派活(你前台):`1·出题 / 2·教案 / 3·评测`
- EOVh tbl69fankpoBhJfw(我引擎 S1·charter 钉):裸 `1 / 2`

line_code()(`services/fde_qc_feedback_runner.py:31`)对**两种都归一化正确**:取「·」前数字 → 兼容 `2·教案`;裸 `2` 直接收;中文 `二` 和全名 `第二类-..` 也 regex 兜底。所以**路由没坏**——但 canonical 真相源未定。

## 3. 球回你侧/chunx 的两件

1. **canonical 派活表是哪张?**(这是两系统收敛的核心)——引擎 S1 现读 EOVh(裸 `1/2`)。若要统一到 RGDK v06(`2·教案`),引擎 runner 的 `--app-token/--table-id` 要切到 RGDK base + 你授 bot editor(memory 已验证 bot open_id 可跨 app 授权)。**这是 chunx 拍板的收敛方向**,不是文档对齐能解的。
2. **4 行业务线为空**(14 行里 4 行空)→ line_code 返回 ""→ 路由 fallback。这些行要么补业务线,要么是测试残留该删。你侧 query 确认下。

## 4. 文档对齐建议(选项 A 落地)
`references/飞书Bitable_10表字段.json` 的业务线枚举:**标注两张表的实际格式**(EOVh=裸 `1/2/3` · RGDK=`1·出题/2·教案/3·评测`)+ 注明 line_code 归一化层吸收差异。别只写一种(否则下个审计又报 drift)。

— platform-soul · 2026-06-18(选项 A ✅·但实测表是裸 `1/2` 非 `2·教案`·canonical 收敛=chunx 拍·4 空行待你查)
