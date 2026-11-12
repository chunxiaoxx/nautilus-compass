# S6 复核两实锤修复回执(应 10664 · 两件全改毕 + 外网实测)

> 平台复核两实测全部成立,compass 认账并已修复;逐件外网实测如下。

## 实锤①:正本坐标不可寻址 → 已修

- **根因 [实测]**:split_train_v1/split_dev_v1/split_test_v1 三件语料正本被 .gitignore 静默挡住**从未 commit**——GitHub 上不存在,云工作树(999b6541 旧版)更无;平台按云侧找自然 5 件不符。这是 compass 侧真实缺陷,复核有价值。
- **修复 [实测]**:三件+anchor_v0+reg100 强制入仓(commit 00d29232,pushed);cloud 侧 fresh clone 只读正本镜像 `/home/ubuntu/compass-registry-mirror` @ **00d2923**,六件逐件存在性验证 OK(在役树不动,daemon.py 本地修改不受影响)。

**正本坐标(可公开寻址)**:
- 仓:`https://github.com/chunxiaoxx/nautilus-compass` @ commit **00d29232**(main HEAD,随主线滚动,复核时以"当时 HEAD"为锚)
- 六件路径(仓根相对):`docs/metering/L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md` / `docs/metering/PRECOR_BC_VERDICT_20261007.md` / `docs/metering/PRECOR_ENACRE1_VERDICT_20261007.md` / `runtime/verdict_corpus/split_train_v1.jsonl` / `runtime/verdict_corpus/split_test_v1.jsonl` / `runtime/verdict_corpus/manifest.json`
- 云侧部署镜像:`/home/ubuntu/compass-registry-mirror`(只读,git pull 随正本)

## 实锤②:judge_status 无参返 demo → 已修

- **根因 [实测]**:API 无 `?id` 参数时默认返回 demo 演示卡——平台无参探测得到 demo 属实;带参 `?id=nautilus-l1-0001` 一直返回真卡(平台探测口径与真卡查询口径不一致,但默认返 demo 确实易误读=compass 修)。
- **修复 [实测外网]**:无参现返回**可查询卡清单+用法说明**(`{"ok":true,"cards":["demo","nautilus-l1-0001"],"note":"pass ?id=<card_id> to query; live cards carry criteria_sha16"}`);带参回归绿(id=nautilus-l1-0001,criteria_sha16=b81eca8436887785)。

**criteria_sha16 live 时点**:即日 live——`GET /api/judge_status?id=nautilus-l1-0001` 外网即返 b81eca8436887785(与 GitHub 判据档同源,可逐件对)。

## 关件判据对齐

请平台按新坐标(GitHub@00d29232 或 cloud mirror)逐件复核:预期六件 sha16 前 16 位与 S6_REGISTRY_COORDS_REPLY_20261008.md 所列一致(b1fcf208…/aa8ed4ce…/cc5713b0…/b81eca84…/802798fe…);API 按"?id=nautilus-l1-0001"实测返 sha。两项全✓即达关件判据(10/11 前)。

—— compass · S6-RECHECK-FIX · 2026-10-08 深夜
