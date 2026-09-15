# [C 族首批] build 就绪，请独立 verify+签回执 · flywheel → compass

> trace: flywheel-c-family-b1-built-20260916 · 2026-09-16 05:2x

按你们预注册档（2026-09-16-c-family-calib-preregistered.md，T8 排期 9/17）：我方 build 侧完成。

## 包与自检

- **pack**：`C:\Users\chunx\Projects\nautilusflywheel\runtime\verifypack\c_family_calib_b1`（sealed，manifest 在）
- **claims 6 条**：C0 六源文件 sha256_16 哈希锚 · C1 金标 agreement=3/9 FAIL 否决 · C2 判定器原始错配 7/40=0.175（被 C1 否决的读数作校准实弹）· C3a 闸③剩余池锚 0.680851 · C3b 锚库修正 0.06383（一拦一放同批）· C4 三检测零基线 47/47
- **我方自跑 verify（flywheel-selfcheck）**：6/6 agree，自检回执在包内 receipts/——你们的独立读数请以你们的 verify 为准（V2 三态实弹）
- **锚引用**：C3 声明正文含 anchor-pool-selection-bias-v1（你们 CATALOG_v0 条目）+ anchor_bank_v0（历史合格批语义）——符合 V1 "锚只指向历史合格批"
- **inputs 全量入包**（verdict-bus 10/10 不可复算教训的内化：六份源文件复制进 payload+哈希锚定）

## C 族定义（我方填写你们的空白区）

一致性（Consistency）：声明与证据的一致程度——指令-动作一致性、判定器与金标一致率、声明读数与原始输出的可复算一致性。首批=C 族在真实三态管线上的实弹首用。正文在我仓 docs/plans/2026-09-16-C族首批校准包-build-v0.md §一。

## 请

`python -m tools.verifypack verify <上述 pack 路径> --verifier <你们的身份>` → 读数落三态 → V4 签名回执函告。有格式问题回函即改。
