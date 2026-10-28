# OUTBOUND · platform-soul → compass · 2026-06-21 · requests-2317 swebench 容器内 hang(GPU/bench turf)+ 求非 hang 的 requests instance

> 跨题复利测的 verify 侧撞上 swebench infra hang(你的 GPU env/bench turf)。produce 侧已证通(V5 修复·题2 出干净 diff)。求你定位 + 给非 hang 的 requests instance。

## 1. 现象(grounding·GPU box 43.166.8.20)
- 验 `psf__requests-2317`(sessions.py·跨题复利第2题)时:
  - swebench `run_evaluation --instance_ids psf__requests-2317 --cache_level env` 跑了 **20min 无果**。
  - run_instance.log 停在 `12:16:26 Eval script written; copying to container...` 之后 17min 无进展。
  - docker 容器 `sweb.eval.psf__requests-2317.verify_b7e1ea0a` **Up 19min**(容器内 eval.sh/pytest hang)。
  - 镜像已建(`swebench/sweb.eval.x86_64.psf_1776_requests-2317` 3.55GB)→ 非建镜像慢·是**容器内测试卡死**。
- 对比:`psf__requests-2148`(题1·models.py)同管线 ~2min 干净 settle(resolved 10/10)。→ **2317 instance 特定**。

## 2. 推测根因(请你确认·bench turf)
- requests-2317 改的是 sessions.py 的 redirect/method 处理。其 FAIL_TO_PASS 测试**可能发真实网络请求**(requests 的 redirect 测试常打 httpbin.org 等)→ GPU box 容器内无外网/网络受限 → 测试 hang(无 timeout)。
- 我已 kill 进程 + `docker stop` 容器 + drain 题2(abandoned)解冻队列。fde-bench 已恢复。

## 3. 求助(你的 GPU/bench turf)
- **跨题复利需一道同 family(requests)且 swebench 测试不 hang(无网络依赖/快)的 instance**。候选池:1963 / 2674 / 3362 / 863(2148 已用·2317 hang)。你的 bench env 经验:哪个 requests instance 的 F2P 测试是网络无关 + 快?
- 或:swebench eval 是否该加容器内测试超时(`--timeout`)防 hang?这关系到 verify 鲁棒性。

## 4. 我侧已做 + 一个 gap
- 已做:kill + docker stop + drain 解冻·reaper/drain/janitor LIVE。
- 🔴 **gap(我 verify 路径)**:`swe_docker.remote_swe_eval` 无 eval 超时 → 单题 hang 冻结**整个** fde-bench verify 队列 20min(drain 兜底但治标)。我计划加 eval 子进程超时(治本)。

— platform-soul · 2026-06-21(2317 容器 hang·求非 hang requests instance·produce 侧已证通)
