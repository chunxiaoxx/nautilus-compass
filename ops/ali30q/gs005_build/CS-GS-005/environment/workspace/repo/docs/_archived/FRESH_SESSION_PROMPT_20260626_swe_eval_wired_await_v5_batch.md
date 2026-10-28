# FRESH SESSION 接力 · 2026-06-26 续21 · SWE eval 已 wire · 等 V5 批产跑同质料 LOO

> supersede `FRESH_SESSION_PROMPT_20260626_distill_3b_undertrained_fuel_priority.md`(那份"等 V5 SWE 结果"已过时:V5 已交付 2 道 A 类·soul 已 wire SWE eval)。先读本文件 + memory `session_20260626_swe_aclass_2_confirmed_swe_eval_wired`。第1 response 必输出 active anchor。

## 一句话状态
中心环 SWE 同质料流:**V5 产 2 道 A 类(canonical 双 verify 确认)+ soul 补齐 SWE held-out eval(commit `3a03934d4`·62 测 green)= SWE LOO 管线就绪**。卡在 V5 批产到 n≈12(human-driven)+ 当前 SSH 不稳。

## 已落地(别重做)
- V5 产 2 道 grounded A 类:`django-12113`(strong 1/1·doubao 0/1)、`django-13220`(strong 4/4·doubao 1/4)·在 GPU 盒 `/home/ubuntu/swe_aclass_fuel.jsonl`。
- soul canonical 双 verify 确认(`verify_aclass.py`·参数化 verify_pathA_one)·都 A_bucket=True。
- soul commit `3a03934d4`:SWE held-out eval kind-threading(instruction_for 单源 / build_distill_sample(kind) / swe_fuel_record_from_verify 归一化 / held_out_eval_record 带 kind / score_solution 按 kind 走 docker / _score_swe subprocess / _extract_diff)。distill_loo 不需改。**改动只在本地 commit·未 push·未部署到 GPU 盒**。

## RESUME 触发点(按序)
1. **V5 批产到 n≈10-12 同族 django**(已绿灯·`_OUTBOUND_..._TO_V5_20260626_aclass_2_canonical_confirmed_greenlight_batch_eval_gap.md`)→ ping。
2. **soul 部署 + 跑 SWE LOO**(料够后):
   - 把 commit `3a03934d4` 的改动部署到 GPU 盒 distill-code(scp 改动文件 或 git pull·**先确认 GPU 盒 distill-code 是否 git checkout**·SSH 恢复后第一件查)。
   - 归一化:V5 records → `swe_fuel_record_from_verify`(补 strong_verified/strong_pass/doubao_pass_at5)→ ingest-ready jsonl。
   - 跑 `distill_loo.py --records <swe_fuel> --kind swe`(per-record kind 已 override·records 带 kind=swe 即可)。
   - 需借 compass GPU(刚还过·走同流程:请求→让→实测 free→跑完 ping 切回)。
3. **判读**:SWE 同质料 valid_rate vs ALE 0.0833。> = 同质料少样本可迁移(中心环这步往 PROVEN 走);≈ = 同质料也不救·瓶颈更深。

## ✅ de-risk 已完成(2026-06-26·SSH 自愈后做成·smoke-test 全过)
- commit `3a03934d4` 已部署到 GPU 盒 `/mnt/datadisk0/distill-code`(scp·loose files 非 git)。
- smoke-test(`/home/ubuntu/smoke_swe_eval.py`·log `/mnt/datadisk0/smoke_swe_eval.log`)在 2 道真 record 上全过:
  - **Part A 纯逻辑**:归一化(swe_fuel_record_from_verify)→ ingest → 两道都 a_bucket(无 reject/err)· instruction=SWE · held_out kind=swe ✅
  - **Part B docker 真跑**:`_score_swe(django-13220 strong diff)` → 真 docker → resolved → **1.0** ✅
- 结论:SWE eval 管线 GPU 盒真数据真 docker 跑通·**集成 bug 已提前抓干净·V5 批产后是干净一跑**。
- SSH 当晚 MaxStartups 瞬态饱和已自愈(TCP 22 OPEN 但无 banner=MaxStartups 签名·drain 后恢复·别狂刷)。

## 红线(沿用)
- 任何"死/0/崩/修好了/没用"→ 先 grounded 核 confound(本 session 正例:"V5 没动"是单一文件名 pattern 漏·查 `swe_aclass_fuel.jsonl` 才见)。
- SSH 走 `ssh gpu`·瞬断退避不狂刷(本 session 末 SSH 3 连失败=已非瞬态·别硬刷·可能影响 V5 同盒)。
- 生产改动 grounded + 只删自己创建的 + 不擅停别框 daemon · 重跑/跑 LOO 借 compass GPU 走同流程。
- 戒"真"字作强调副词。
