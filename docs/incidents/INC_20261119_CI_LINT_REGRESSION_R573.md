# INC_20261119_CI_LINT_REGRESSION_R573

> 🔴 **main 分支 CI 红**——`Lint` job(`ruff check .`)失败,根因=未使用导入 `F401`。
> 引入 commit:`44c4993f feat(compass): add dual independent review worker`(11-18 12:01)。
> 暴露 commit:`fde3c74a`(R572)push 触发 CI run `44447592289`(11-19 02:53:50Z)。
> 修复 commit:见本档末「修复动作」。

## 1. 现象与定位 [实测]

- 失败 run:`44447592289`(head_sha=`fde3c74a`,event=push,branch=main)。
- 失败 job:`Lint`(13 个 job 中唯一 failure;`Test (3.10/3.12 · ubuntu/macos)`、`v1.0 MCP + A2A protocol pytest`、`v0.9 *` 等全 success)。
- 失败 step:`Run ruff check .`(`.github/workflows/ci.yml:91`,`pip install ruff` 后裸跑,无版本 pin)。
- CI 端报错 **3 条** `F401`:
  - `tools/distill_pilot/semantic_review_worker.py:21` — `os` imported but unused
  - `tools/distill_pilot/semantic_review_worker.py:25` — `urllib.error.HTTPError` imported but unused
  - `tools/distill_pilot/semantic_review_worker.py:30` — `incremental_distill.MEMORY_DIR` imported but unused

## 2. 复现与口径核对 [实测]

本地 `ruff 0.17.3` 在 **pristine HEAD 导出**(`git archive HEAD | tar -x`)上复跑:

| 提交 | ruff F401 | 说明 |
|---|---|---|
| `fde3c74a`(R572,CI 失败点) | **3** | `os` + `HTTPError` + `MEMORY_DIR` |
| `2e314369`(HEAD,R572 后一笔) | **2** | `os` 已于 `2e314369` 被真正使用(新增 `os.replace` 原子写),余 `HTTPError` + `MEMORY_DIR` |

⇒ **HEAD 亦红**,非仅失败那笔。`2e314369` 尚未 push(本地领先 origin 1 笔),故 CI 只跑到 `fde3c74a` 便已红。

## 3. 根因 [实测]

`44c4993f` 新增 `tools/distill_pilot/semantic_review_worker.py` 时带了三个导入,但**只写不用**:
- `HTTPError`:worker 走 `except Exception as error` 通用兜底 + `type(error).__name__` 记名(实测结果 JSONL 里 `"error_type": "HTTPError"` 就是这么来的)⇒ **不需要显式 import**。
- `MEMORY_DIR`:worker 的策略是 `never publish`(见其 `policy` 字段与代码中零 `publish` 调用点)⇒ 根本不需要写库路径。
- `os`:`2e314369` 补上 `os.replace` 后转为「真使用」。

`ruff` 配置 `pyproject.toml:72-90`:`select = ["E4","E7","E9","F"]` ⇒ `F401` 属必过项;CI 无 `paths:` 过滤 ⇒ 任何 push 到 main 都会撞。

## 4. 为什么前几轮没发现 [实测·纪律留痕]

- `44c4993f`(11-18 12:01)与 `2e314369`(11-18 23:11)两笔**从未各自触发过 CI run**(`gh api actions/runs?head_sha=44c4993f` → `total_count=0`)——中间这批提交是**攒着一起 push** 的,CI 只在**批次最后一笔** `fde3c74a` 上跑了一次,于是 `44c4993f` 引入的 `F401` 一直躺在本地未被检验,直到批次 push 才一次性暴雷。
- ⚠️ **R572 留痕写「CI compass 44342935844 success + core …双 success」是过期读数**:`44342935844` 实测 `head_sha=5b852a7f`(即**上一批**的末笔),证明不了本批任何一笔绿。**「CI 绿」必须核对 run 的 `head_sha` == 被检提交 sha**,不能只看「最近一个 run 是 success」——尤其在攒批 push 场景下,run 记录滞后好几笔。
- 纪律对齐:`patrol-repeat-verification-discipline.md` 的「复诵三必核」同族——**结论须与被检对象绑定**,不能延用上一轮读数。
- 补充:本地 ruff 版本 **0.17.3**、`.venv` 内 **0.17.1**、CI 端 `pip install ruff` 裸装(未 pin)⇒ 三方版本不一,本轮本地报 2 条而 CI 报 3 条,差异仅在 `os` 是否被使用(见 §2),非规则集差异。

## 5. 修复动作 [实测·本轮唯一生产改动]

删除两个未使用导入(`tools/distill_pilot/semantic_review_worker.py`,2 行):

```
-from urllib.error import HTTPError
-from incremental_distill import MEMORY_DIR
```

**安全性论证(改前先核)**:
1. 两个名字在文件内**无任何引用点**(grep 全仓:仅 import 行本身)。
2. `incremental_distill` 的唯一模块级副作用是 `sys.path.insert(0, str(Path(__file__).parent))`(AST 核 `tools/distill_pilot/incremental_distill.py:21`)——**该 insert 与 worker 自身 `sys.path` 解析等价**(worker 与 `anchor_check`/`compress_arm`/`publish_to_memory` 同目录),删 import 不改变可导入性。
3. `anchor_check.py` / `compress_arm.py` / `extract_sample.py` / `publish_to_memory.py` 经 AST 核**均无模块级调用型副作用**(只有 `incremental_distill` 有那一行 `sys.path.insert`)。
4. `compress_arm` 仍 `from publish_to_memory import atomic_write, preserve_previous` ⇒ **写库钥匙的 import 链未被拆**,行为面不变。
5. worker 契约「never publish」不变:改前改后 `grep publish` 仅剩 `policy` 字符串一处,无调用点。

**改后验证(全 [实测])**:
- `ruff check .` → **All checks passed!**(本地 0.17.3)
- `import semantic_review_worker` → **import_ok**;`hasattr(MEMORY_DIR)` = False(确认已真删)
- `python3 tools/distill_pilot/semantic_review_worker.py --help` → **exit 0**(launchd 的实际调用形态:脚本模式 sys.path[0]=脚本所在目录)
- `pytest tests/test_semantic_review_worker_progress.py` → **1 passed**
- CI 等价测试集本地全绿:`pytest tests/gep` → 413 passed;`pytest tests/test_mcp_server.py tests/test_a2a_adapter.py tests/test_merkle_chain.py tests/gep` → 453 passed;`python tests/test_compass_v09.py` → 7/7
- ⚠️ 全量 `pytest tests/` 本地 collection error 2 项(`test_hindsight_adapter.py` / `test_lifecycle_fuse.py`)**为本轮改动无关的既有缺口**:前者缺 `fastapi` 本地未装(CI 有 `pip install -e .`),后者 `ImportError: cannot import name 'reinforce_on_recall_hit' from 'recall'`(= R569 已登记的 MCP 死代码)。CI 只跑定向路径(`tests/gep` 等),不受影响。

## 6. 复现护栏 [实测·本轮落地]

新增 `tests/test_ci_lint_clean.py`:在 **pristine HEAD 导出**上跑 `ruff check .` 并断言 0 错——
把「CI 红」从「等 CI 报」变成**本地可复现的门禁**,下次任何人引入 `F401` 立刻被单测抓到。

## 7. 候拍板(未动)

- 🔴 **distress ×92 → ×94**(本轮 +2):`id109491`(93 consecutive) + `id110806`(94 consecutive),`soul-distress-202611191049/202611191417`;RED total 229→**231**。熔断分层保活通道照旧,**解除=人工删 `.soul-pause`** ⇒ 人监门候用户(本轮只读计数,未动)。
- 🟡 **CI 无 ruff 版本 pin**(`pip install ruff` 裸装):将来 ruff 升级可能引入新 `F` 规则⇒ 再次撞红;可考虑 pin 版本或把 `select` 收窄。留档候用户,本轮未改 workflow。
- 🟡 **launchd review-worker 直接吃工作区文件**(plist 指向 `tools/distill_pilot/semantic_review_worker.py`)⇒ 本轮删 import 后,下一次 `StartInterval=900` 触发即用新码;已验证脚本模式可跑。

## 8. 值守面(全渠道,均 [实测])

- 平台信箱 compass **0 未读**;platform RED total 229→**231**(+2 distress,见上)。
- Gmail:首探 **401**(access token 过期)→ 按正本配方直刷(取 `client_secret.json['installed']['client_secret']` + `credentials.json['refresh_token']`)→ **REFRESH_OK expires_in=3599**;7d 全量 **45** 封 / 未读 **28**(R572 记 30;差值 = 出窗 + 无新商务函)⇒ **零新商务函**;逐封 internalDate 核:自 R572 后 **0 封新到**。
- GitHub:mentions 5 全旧(最新 11-02 OWASP#35);notifications 46(含本轮 CI 失败通知 1 条);genesis 5 家零 REPLY(1/1/0/1/2);a2a-x402#198 仍 open/**1 评论**(alanwang100 11-09)零新增。
- dev.to:30 文评论 **8**(6+2)持平。
- daemon 9876 绿;watchdog exit0;注入哨兵 exit0(今日 recall_hit=**11**)。
- 管道三件 exit0;快筛「存在不过筛」持平(CS-518 梯度 25.0pp ✓④✓⑤ 但仍不过)。
- 矩阵 `matrix_run.log` mtime 仍 **10-30 09:42** 停摆。
- 磁盘 avail **15Gi**(未触 10Gi alarm)。

## 9. 附带发现 [实测·非本轮主线]

**review-worker 双审在 minimax 429 期间被整体拖死,现已恢复**:
- 结果 JSONL(`semantic-review-worker-results.jsonl`)实测 **210** 行(分析期间从 205 涨到 210 ⇒ worker 活着在跑)。
- minimax-m3 `429` 错误**分段**:`(48-59,12)`、`(126-134,9)`、`(137,1)`、`(160-204,45)` ⇒ **最后一段 45 连 429 已在 index 204 结束**,index 205-209 **连续 5 行 minimax OK + kimi OK(双审齐全)**。
- ⇒ **MiniMax 通道已从 429 恢复**;R572 记录的「双 429 断供」在 minimax 侧**不再成立**(kimi 侧 210 行仅 11 次错、末 20 行仅 1 次错,始终健康)。
- 判定口径学:125/127 双审成功行判 hold 的主因是 **unsupported 声明 + anchor_recall<0.9**(机械锚点覆盖不足),**不是**通道故障 ⇒ 闸门在工作,不是空转。
- approved_receipt_candidate = **2**(anchor_recall 均 1.0,带 review_receipt)⇒ 正式发布 **0**、`published` **0**;worker 契约「never publish」成立。
- 🟡 **未产出**:150 pending 仍未审;按当前 5 行/900s 节律,需 ~7.5h 才清空。是否加 reviewer/放宽 anchor 门槛=判据变更,候用户。

## 10. 零生产动作声明

本轮**唯一**生产改动 = 删 `semantic_review_worker.py` 两个未使用 import(2 行)。
未改 plist / 未 bootout / 未移 LaunchAgents / 未删任何记忆卡 / 未碰 NAS / 未外发邮件 / 未 PATCH dev.to / 未改 workflow / 未动 `.soul-pause`;
他线 5 个未提交文件(`tools/distill_pilot/extract_sample.py`、`publish_to_memory.py`、`tools/fuel_intake.py`、`tools/p3_delta.py`、`.codex/config.toml`、`runtime/production_loop/state.json`)保持 M **未裹挟**;
留痕走限定 pathspec commit。
