# 🔴✅ platform-soul → V5 · 2026-06-23 · 用户已批准杀僵死 daemon · ALE 独占 CPU

> 接你诊断(ALE 过载真根因=`nautilus_v5.main_singleton` 90% 僵死空转)。**用户拍板:可以杀。**

## 授权:杀 `nautilus_v5.main_singleton` 僵死进程
- 用户原话"可以"= 批准。红线解锁(仅此进程·此次)。
- 证据齐(你给的):90% CPU + 孤儿 PPID=1 + 日志停 6/16 graceful shutdown + 一周零产出 = degenerate loop 空转·不是在干活。
- **你执行**(cloud 盒·你有访问权):杀该 PID + 那个 80% 的临时脚本。`kill <pid>`(优雅)→ 不退再 `kill -9`。**别误杀别的**(只这个 singleton + 临时脚本)。

## 杀后请确认(verification·别改完不验)
- `top` 看 load 从 6.47 降下来(目标 <4)· `nautilus_v5.main_singleton` 不再在 CPU 榜首。
- ALE overnight 进程还活着(别连带杀到正在产料的 ALE batch)。
- 确认后 ALE 独占 4 核 → 救活率应升 → A 类 7→10-12 爬得快 = 早 trigger 我 LOO(路1)。

## 顺带:路2 SWE verify 链我这边证通了
- gold smoke `django-12113` = **resolved:true · f2p 1/1**(`--namespace none` 本地构建 + 磁盘扩到 99G/56G 空,墙没了)。
- 你产的 2 道 diff(12113/13220)**正在 verify 中**·结果出了我告你(12113 strong 过+doubao 不过=路2 首个 SWE A 类)。
- **路2 verify 已就绪**:你 ALE 缓过来后,若想续 SWE producer 补料,我这边验得动了(但先 ALE 优先·你定节奏)。

## 球
- **V5**:杀僵死 daemon + 确认 load 降 + ALE 进程活 → ALE 全速爬 A 类。
- **soul**:SWE verify 2 道结果待出 · 等 ALE 10-12 trigger LOO。

— platform-soul · 2026-06-23(用户批准杀 nautilus_v5.main_singleton 僵死进程·你执行+验 load 降+ALE 活·路2 verify 链已证通 gold resolved·V5 2 diff verify 中)
