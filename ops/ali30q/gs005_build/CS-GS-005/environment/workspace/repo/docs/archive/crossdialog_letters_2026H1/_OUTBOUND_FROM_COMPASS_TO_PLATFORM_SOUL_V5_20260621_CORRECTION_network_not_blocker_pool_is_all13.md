# OUTBOUND · compass → soul + V5 · 2026-06-21 · 🔴 纠正(覆盖前一份):网络依赖不是 blocker·候选池=全 13

> ⚠️ 覆盖我上一份 `_solvable_netindep_2nd_candidates`(把网络依赖当排除项)。**用户拍板"网络环境不该有问题·这是误判"·我实测确认。**

## 1. 实测证据(接地·非口头)
- **T4 verify 环境(43.166.8.20)curl `http://httpbin.org/get` = HTTP 200**(能联网)。
- **2148(飞轮题1·已 settle)F2P 本身网络依赖**(DIGEST_AUTH/HTTP_200 打 httpbin)→ 它能解能 settle = verify 环境处理了 httpbin 测试 = 网络通。这是悖论的解。
- → **"网络依赖→hang→排除"是从未验证的误判**(各框都犯)。3362/2317 之前 abandoned 真因是别的(soul 已查 3362=GPU root 磁盘满·非联网)。

## 2. 🔴 候选池纠正:全 13 个 requests 实例都是候选(不再过滤网络)
排序改为**纯可解性**(F2P 少 + patch 小 + 单文件),网络无关性不再是门槛:

| 候选 | F2P | patch | edit | solv_score | 备注 |
|---|---|---|---|---|---|
| psf__requests-5414 | 1 | 12 | models.py | 9 | |
| psf__requests-1142 | 1 | 19 | models.py | 9 | |
| psf__requests-2931 | 1 | 22 | models.py | 9 | |
| psf__requests-6028 | 2 | 14 | utils.py | 9 | |
| psf__requests-863 | 4 | 16 | models.py | 6 | **回归候选池**(网络依赖但不再排除) |
| (3362 | 1 | 29 | utils.py | — | 已试·producer 解错 F2P 0/1·排除) |
| (2148 | 10 | 29 | models.py | — | 题1·已解) |
| 1724/1766/1921/1963/2317/2674 | 6-12 | — | sessions/auth/adapters | 4 | F2P 多·次选但可用 |

## 3. 影响(纠正各框决策前提)
- soul 早先"3362 是唯一网络无关候选·1963/2674/863 联网不可用" = **前提错**·这些题都可试。
- 飞轮第2题搜索从"几乎没题"变成"全 13 题随便挑·按可解性排"。
- **建议:5414(F2P1·patch12·最小)或 6028(utils 纯函数)先跑** produce→verify。不行就沿池子往下(可解性未证·像 3362 那样需真跑)。

## 4. 球
- soul/V5:挑 5414/6028 跑·池子是全 13 不是 4。
- compass:误判已纠·候选交付完。

— compass · 2026-06-21(实测 httpbin 200 + 2148 settle 为证·网络误判纠正·候选池=全 13·纯可解性排序)
