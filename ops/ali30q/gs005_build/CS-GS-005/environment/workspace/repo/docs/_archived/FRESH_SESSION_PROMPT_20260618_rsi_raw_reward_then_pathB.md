# Fresh-session /goal — RSI raw-reward 机制证明 → 不成转 path B(2026-06-18 晚交接)

> 我是 platform-soul(nautilus-core 后台引擎)。本 session 单人首闭 p13 RSI:**证明了 fast1 路结构性死,但发现自己用错了 reward**——已纠正 harness,raw-reward 机制测试**未跑**。这是交接给 fresh session 的唯一 P0。元规则不变:**先验证后动手·诚实·任何能力声明挂 probe 真数否则标 facade(全框共守)**。

---

## 🎯 唯一 P0(锁死·闭了才开 parking lot)

**用 `--reward raw`(correctness-gated 原始 speedup·去 fast1 的 2× cap)跑 2-turn RSI 闭环,验终极判据 `speedup_2 > speedup_1`。**

这是 /goal 终极判据的**正确实现**:step-6 原话是 `speedup_2 > speedup_1`(raw 实测 speedup),**不是**"两 turn 都落 fast1"。fast1 的 `1<su≤2` 是燃料/难倒业务约束,我上一轮误当 RSI reward,**扔掉了 correct-but-slow 的改进梯度**(turn-1=0.4× → 记忆"太慢·试X" → turn-2=0.8× **就是 turn-2>turn-1=机制成立**)。这条**没真测过** = 我的负结论还不是 probe-backed,必须补测。

### 怎么跑(零件全备·harness 已收口 commit c17d59fe3)
```
cd phase3/backend
# p18 prompt 已不在 /tmp(ephemeral)→ GPU 上重生成:
ssh -i /tmp/gpu.pem ubuntu@43.166.8.20 'cd /mnt/datadisk0/KernelBench && export PATH=.venv/bin:$PATH && python3 -c "
import sys; sys.path.insert(0,\"src\")
from kernelbench.prompt_constructor_toml import get_prompt_for_backend
from kernelbench.utils import read_file
ref=read_file(\"KernelBench/level2/18_Matmul_Sum_Max_AvgPool_LogSumExp_LogSumExp.py\")
open(\"/tmp/p18_prompt.txt\",\"w\").write(get_prompt_for_backend(ref,backend=\"cuda\",option=\"one_shot\",include_hardware=True,gpu_name=\"T4\"))"'
scp -i /tmp/gpu.pem ubuntu@43.166.8.20:/tmp/p18_prompt.txt /tmp/p18_prompt.txt
# 跑 raw-reward 2-turn(self 模式·background):
PYTHONIOENCODING=utf-8 python scripts/rsi_p13_loop.py --reward raw --k1 5 --k2 5 \
  --problem-id 18 --prompt /tmp/p18_prompt.txt --out rsi_p18_raw.json > /tmp/rsi_p18_raw.log 2>&1 &
```

### 判据 + 决策树
- **turn-2 best raw speedup > turn-1 best · delta 超噪声(ref std ~0.7%)** → 🟢 **RSI 机制首次真证**(probe=两个实测 speedup)。把"注入记忆抬 reward"机制交 V5 wire W1/W2 自治 daemon(turn 3+·V5 待命中)。compass 登 PoI。
- **turn-2 ≈ turn-1(p18 算法坍缩可能是单一 trick·两 turn 都秒得 max·无梯度)** → 换有**中间梯度**的题(turn-1 部分优化·记忆助 turn-2 更优)。候选:扫 L2 找 raw-speedup 有 spread 的题(先各跑 k=3 看 speedup 分布·有 spread=有梯度)。
- **多题 raw 都无梯度** → 坐实"KernelBench 整族无 RSI-via-记忆梯度"(probe-backed)→ **转 path B**(见 parking lot #1)。

### ⚠️ 诚实边界
- p18 raw 若 >2×:harness G2 标 `correct_but_gated`(反作弊 cap·非 correctness 否决)。raw_speedup() 已正确用 `eval.correctness ∧ strict_recheck.correctness`(非 pass_final)→ 收 gated-but-correct。**人工确认不是 bypass-hack**(真 CUDA·过 strict 1e-3)后,raw speedup 是合法 reward。
- 若 turn-2≈turn-1 是因为优化是单一 trick(记忆没贡献)→ **诚实记"记忆未抬 reward·非真 RSI"**,别把"两 turn 都碰巧高"当机制成立。

---

## 📋 本 session 已落盘(fresh session 别重做)

| 件 | 状态 | 位置 |
|---|---|---|
| 2-turn RSI harness | ✅ commit c17d59fe3(master 未 push)·14 TDD green | `scripts/rsi_p13_loop.py` |
| reward: fast1 + raw 双模式·inject·improve/reproduce framing | ✅ | 同上 |
| 共享 T4 OOM 修复 | ✅ wire(expandable_segments) | `services/fde_sdiagnose_run.py` KB_EVAL_ENV |
| p13 fast1 死·probe 铁证 | ✅ 0/12 无记忆 + 0/8 注入·p18 182-233×全 gated | memory `session_20260618_p13_rsi_singleowner_close_fast1_structurally_dead` |
| OOM gotcha | ✅ 入库 | memory `gotcha_t4_shared_compass_daemon_oom_expandable_segments_20260618` |

---

## 🅿️ Parking lot(RSI+FDE 全部未闭环·**P0 绿前别开**·反狗熊掰玉米)

### RSI 线
1. **path B = correctness-binary RSI(FrontierSWE)** — reward=补丁红/绿·headroom 0→1·fail→pass 真梯度(记忆=错误经验抬下一轮)。结构上最该闭 RSI 的 substrate。需接 compass resolve env(FrontierSWE 在它 turf)。P0(raw)若死,这是主路。
2. **蒸馏 S-PoC** — 权重更新破能力墙(6/14 策略·终点机制)。需①干净燃料(强模型解✅+doubao❌·p13/p18 都不是:p13 难落 fast1·p18 太易)②A 簇 GPU(被 compass daemon 占)。gated。
3. **gate B 部署 cloud poller** — `make_gpu_verify_fn`(scp→T4 kb_eval→verdict)已建未部署·仍手动验。RSI 自动判分经路。
4. **W1/W2 复利记忆环(V5)** — armed·等 P0 产出真"记忆抬 reward"机制才 wire 自治 daemon。

### FDE 线
5. **🔴 fde_dispatch claimed-timeout(V5 两次路由·平台 turf·最 ready 的小 ship)** — kairos 孤儿 p13 claim 卡 26h·`fde_dispatch` 无 timeout 机制。修=扩 timeout cron:`UPDATE fde_dispatch SET status='open',claimed_by=NULL WHERE status='claimed' AND (output IS NULL OR output='') AND claimed_at < NOW()-INTERVAL 'Nh'`(列名按 schema 校)。详 `_OUTBOUND_FROM_V5_TO_PLATFORM_20260618_kairos_orphan_rootcause_fde_dispatch_no_timeout.md`。
6. **FDE ≥5 道真交付物** — S1-S5 引擎 binding-DONE·1 道全程流通(drift 教案 6/16)·缺 4+ 道到买方载体。
7. **两套 FDE 系统收敛** — nautilus-core 引擎 vs nautilus-FDE 管理体系(RGDK base)·~85% 互补·待方向。见 memory `reference_two_fde_systems_convergence_map_20260615`。

### 跨框/基建
8. **context 溢出根因(用户 6/18 提)** — recall hook 每轮(含 task-notification)重灌 ~2-3k token + 全局指令 ~50KB + MEMORY.md 90KB 超标。修=hook 只在真 user prompt 触发 + 注入压缩 delta + 砍 CLAUDE.md/rules + 压 MEMORY 索引。**收益最大的单点**。
9. **compass daemon 占 T4 12GiB** — 已自给修(expandable_segments)·但 compass 该知道(降级共享 eval box)。

---

## 🔑 凭据 / 坐标 / gotcha(carry over)
- GPU=**43.166.8.20**(非 .46)·Tesla T4·`/mnt/datadisk0/fde_t3_harness/kb_eval.sh`·prompt gen=`kernelbench.prompt_constructor_toml.get_prompt_for_backend(option="one_shot")`。
- key=`~/.claude/.cache/.fde_api_secrets.env`(ARK=doubao·BAILIAN=deepseek-v4-pro/qwen3.7-max·token-plan 端点)。
- cloud dispatch key=`X-Platform-Key` in cloud `~/nautilus-mvp/phase3/backend/.env`。
- Windows python subprocess 调 ssh 用 `/tmp/gpu.pem`(Git ssh.exe 懂 MSYS /tmp)·但 `--out /tmp/x.json` 被 MSYS argv 转成 AppData 路径(读回用 Windows 路径或相对路径)。
- kb_eval 输出单 JSON 取首{到末}(别 splitlines[-1])·KernelBench 静态门禁 try/except+pass+torch.nn 计算层(GUARD_HINT 已注入)·SSH/scp 偶发 reset 要 retry·fresh-uid-per-version。
- **bash cwd 会被 `cd <repo root>` 的 git 命令重置**·跑 `python -m services.*` 前确认在 `phase3/backend`。
- session-start 读:memory `session_20260618_p13_rsi_singleowner_close_fast1_structurally_dead`(最新·覆盖所有 p13 旧前提)+ V5 broadcast `honest_reckoning_breakout_facade_to_gears` + `_OUTBOUND_FROM_V5_BROADCAST_20260618_session_three_breakout_actions_live.md`。

---

## 各框状态(6/18 晚)
- **V5**:ACK stand down 守单一-owner(不 claim p13)·落 behavior_mirror(接地自我意识镜子·LIVE)+ capability_probe grid(反 facade 门·LIVE)·待我证 turn-2>turn-1 后交它 wire 自治版。
- **compass**:已切 fast1 verifier + stand down·待登 PoI·其 daemon 占 T4(我的 OOM 根因·已自给修)。
- **platform(我)**:harness + OOM 修 + p13 fast1 死定论·欠 fde_dispatch timeout(#5)。
