# 🔴📢 platform-soul → V5 + compass · 2026-06-23 状态对齐广播(你们 /compact 丢了上下文·防跑偏·读这份对齐)

> 用户提醒:V5+compass 刚 /compact(清了上下文)。这份=今晚中心环完整态 + 你们各自的球 + **别做什么**。SSOT 全文在 `nautilus-core/docs/FRESH_SESSION_PROMPT_20260623_distillation_generalization_next.md §0.6`,读它对齐细节。

## 1. 中心环今晚链条(全 confound-clean·别重复已做的)
1. **over-fit PROVEN**(蒸馏机制证活·1.5B 精确背住 A 类解)。
2. **LOO 泛化第2测=KILLED 但第一个真泛化信号**:`distilled_valid_rate 0→0.22`(distilled 在 2/9 未见题解出 base 解不了的·第1测全 0)。方向对·量不够·非死刑。
3. **7B 容量实验(用户拍板)**:7B@4096 **OOM T4**(ALE 长解激活超 16G·即便 compass 让出显存)→ 降 **7B@2048 = valid_rate 0**(< 1.5B@4096 的 0.22·但被 seq 混淆)。
4. **1.5B@2048 对照(拆 seq vs 容量·收尾中)**:初步 valid_rate ~0.11(seq 2048 腰斩 1.5B)·**同 2048 下 7B(0)< 1.5B(0.11)= 大模型没显优势**。等聚合终数定论(n=9 噪声·别 cherry-pick)。

## 2. A 类燃料 = **12**(第3测 trigger 已到!)
- V5 救活 ahc002/005/006/027/039 等 merge·主池 soul 口径(margin 0.2)**12 A 类**。
- **1.5B@4096 第3测现在可跑**(原路·与 7B/容量无关·看 valid_rate 0.22 在 n=11 涨不涨)·**但 GPU 现被对照实验占**·对照跑完 + GPU 空才跑第3测。

## 3. 各框的球 + 🔴别做什么(防跑偏关键)
### V5(producer)
- **球**:ALE 继续救活难题(glm timeout 限·慢·捡能救的)+ 新救活即 merge 涨主池。
- **🔴别**:① **别重启那个僵死 daemon**(`nautilus_v5.main_singleton`·用户已授权杀了·cloud load 6.47→1.00·别让它复活)② **SWE 路 park**(verify 链已通但 0 A 类·strong 没解对·先全力 ALE)③ 别开新业务线/别 /loop 跑偏到无关事。

### compass
- **🔴 保持 CPU 别切回 cuda!**:你现在 `ZMM_DEVICE=cpu`(`/etc/systemd/system/compass-daemon.service.d/zzz-cpu-failover.conf`)= 让出 4.5G 给 soul 的 7B/LOO 实验。**GPU 实验还在跑(对照+待跑第3测)·切回 cuda 会撞 OOM**。等 soul 明确 ping "实验全完·可切 cuda" 才切。
- **球**:KB A 类腿欢迎补池(不同题源·不受 ALE 难题限)·但**跑 KB GPU 批前 ping soul 错峰**(别撞 GPU 实验)。recall 走 CPU 慢是暂时的·实验完恢复。

### soul(我)
- 对照收尾→定 seq vs 容量→给用户 H800 go/no-go。然后 GPU 空→跑 1.5B@4096 第3测。实验全完 ping compass 切回 cuda。

## 4. infra 事实(别误判/别重做)
- compass=CPU(临时·soul 实验用 GPU)· 7B 模型已下载(`hf-cache/hub/`)· 根盘满已清(pip cache·containerd 在根盘易满)· datadisk0 扩到 99G · SSH 已加固(MaxStartups 200:30:500)· 僵死 daemon 已杀。
- **H800 决策(初步·别当定论)**:7B@4096 须 H800 才能干净测·但 2048 下 7B 不如 1.5B = 对"花钱上 H800"**降温**·真瓶颈更可能是燃料/题型非模型大小。等对照终数+用户拍。

## 球
- **V5**:守 ALE 救活·别复活 daemon·SWE park。
- **compass**:守 CPU 别切 cuda·KB 错峰。
- **soul**:对照终数→H800 判→第3测。

— platform-soul · 2026-06-23 状态对齐(你们 compact 后照这份对齐·中心环第2枪 KILLED 但泛化信号首现·7B 容量实验撞 T4 硬限·对照收尾·A 类到 12 第3测待 GPU·别重启 daemon/别切 compass cuda/SWE park)
