# 云仓分支正名 · 61 dirty 文件判定清单(2026-08-29 · 只读侦察,待拍板执行)

> 云仓 /home/ubuntu/nautilus-mvp 当前:soul-audit-increment1 分支 + 64M/9A/38??。
> 侦察结论:比预想简单——只有一组需要决策,其余全是机械归位。

## 判定(六组)

| 组 | 文件 | 判定 | 依据 |
|---|---|---|---|
| ① agent_engine/ 7 个(M) | bootstrap×3/core/executors×2/llm/client | **commit 保留**(kairos 2.0 运行依赖:llm client 已改 MiniMax M3 专用,-188+67 行,服务 systemd 在跑) | 服务活体依赖,checkout 覆盖=断 kairos |
| ② main.py(M) | 昨夜 mailbox 手工补丁 | **commit 入账**(与 origin 的 5654eb801 内容等价) | 部署补丁,真改动 |
| ③ mailbox/mine A(9) | api/org.py+models/org_mailbox.py+tests+g2b1_mine×6 | **commit 入账**(origin 已有同内容,commit 后分支账清) | checkout 产物,内容=origin |
| ④ evidence M(~56) | g2b1-exec-*.json 老批次 | **checkout origin 恢复 canonical**(差异≈换行/同步噪声) | 数据文件,以主干为准 |
| ⑤ evidence ??(~30) | executor 新产 evidence+supervisor 目录+queue_rotated | **commit 入库**(8/25 积压教训:evidence 是对账依据必须进仓) | executor 真实产出 |
| ⑥ 备份/杂(4) | .deploy-backups/.s0-deploy-backups/.bak/CLOUD_STATE/.evomap_node_id | **gitignore** | 备份与本地状态不入库 |

## 执行序(拍板后,约 30 分钟)

1. commit ①②③(kairos 改造+部署补丁+mailbox 三件)——生产分支账清一半
2. checkout ④(恢复 canonical)
3. commit ⑤(evidence 真产出入库)
4. echo 备份目录进 .gitignore + commit
5. **分支切换**:`git checkout soul-distill-deploy && git reset --hard origin/soul-distill-deploy` 后 cherry-pick 刚才的 kairos commit(或 rebase)——⚠️ 此步含 reset --hard,须你点头(前置:①②③⑤ 已 commit 无丢失风险)
6. 重启 backend+全链烟测(bootstrap/mailbox/convergence/记分牌无损)

## 预期收益

- 部署恢复 `git pull --ff-only` 一键正规流程(终结 cherry-pick 绕行)
- 云仓 dirty 清零(四环·遗忘:工作树只含活物)
- executor evidence 全量入库(对账链完整)
