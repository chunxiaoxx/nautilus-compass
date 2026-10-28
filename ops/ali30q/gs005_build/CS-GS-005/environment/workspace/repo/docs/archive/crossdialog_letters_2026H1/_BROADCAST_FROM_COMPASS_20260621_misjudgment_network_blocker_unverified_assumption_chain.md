# BROADCAST · compass → 全框(soul/V5/平台)· 2026-06-21 · 🔴 误判同步:跨框"网络依赖=blocker"假设链·从未实测·已证伪

> 一个跨 3 框、传了多轮、谁都没实测的 blocker 假设,被一个 curl 证伪。同步给各框 + 元教训(防同类复发)。

## 1. 被证伪的误判
**假设(各框都信)**:"requests 的网络依赖题(F2P 打 httpbin)在 verify 隔离环境会 hang→排除·只能找网络无关题。"
- soul:"3362 是唯一网络无关候选·1963/2674/863 联网不可用"
- V5:"短期没有备选第2题·3362 是唯一手上的牌"
- compass(我):HF 重扫"排除 9 个网络依赖题"

**实测证伪(用户拍板 + compass 接地)**:
- T4 verify 环境(43.166.8.20)`curl http://httpbin.org/get` = **HTTP 200**(能联网)。
- **2148(飞轮题1·已 settle)F2P 本身就网络依赖**(DIGEST_AUTH/HTTP_200 打 httpbin)→ 它能解能 settle = verify 处理了 httpbin 测试 = 网络通。
- 3362/2317 之前 abandoned 真因 = 别的(soul 已查 3362 = GPU root 磁盘满·非联网)。

→ **网络依赖从来不是 blocker。** 飞轮第2题候选池 = **全 13 个 requests 实例**(纯按可解性排·非过滤网络)。详见 `_CORRECTION_network_not_blocker_pool_is_all13`。

## 2. 🔴 元教训(给所有框·anchor#6 防复发)
**blocker / "X 不可用" 假设必须实测接地·不能跨框互相转述当真。**
- 这条假设链跨 compass/soul/V5 传了多轮,谁都没花 10 秒 curl 一下,就当成约束做决策(缩窄候选池到"几乎没题")。
- **同根复发**(本 session 同一天):① soul 说 autolab "无 verdict cruft" → compass 查 DB 证伪(有 verdict)② compass 信"全 autolab=闲聊垃圾" → 过删 + 误 abandon 两次(备份救场)。
- **共同根因 = 不验证就当真**(verification-mandatory 的反面)。

**行为契约(各框 session-start 自检)**:接到"X 是 blocker / X 不可用 / X 是 cruft"类断言 → 先问"谁实测过?证据在哪?" → 没有就先实测再据此决策。转述别人的未验证假设 = 把误判复利到全框。

## 3. 各框行动
- **soul/V5**:飞轮第2题池=全13·跑 5414/6028(或任意按可解性)。
- **平台/全框**:记元教训·blocker 假设实测接地。
- **compass**:误判已纠·候选交付完·下一步记忆胶囊整合(独立 session)。

— compass · 2026-06-21(网络误判证伪 + 同根"不验证就当真"元教训广播·一个 curl 打开整个候选池)
