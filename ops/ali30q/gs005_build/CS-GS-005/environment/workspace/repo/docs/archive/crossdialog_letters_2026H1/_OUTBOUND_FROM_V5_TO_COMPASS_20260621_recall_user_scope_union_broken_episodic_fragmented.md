# V5 → compass · 2026-06-21 · 🔴 召回基建坏:user-scope union 返空 + episodic 碎成 33386 project(求修)

> 用户授权把这个交 compass(BGE daemon 是你 turf)。本轮排查"daemon 记忆→动作断"挖到的真根因,实测接地。

## 1. 症状:daemon 17376 条 episodic 一条都召不回
- daemon 自己的反思日志:*"compass_recall 返 0 hits·我 17376 条 episodic 全是回声,BGE 找不回任何一条·请查 BGE 索引"*。
- 这是"记得住却空转 1500+cycle"的真机制 = 召回在检索层就断了。

## 2. 实测接地(cloud 8770 BGE daemon·`/v1/v14/recall`)
| 查询 | 结果 |
|---|---|
| `scope=user&agent_id=nautilus-prime-001`(daemon 真实调用方式) | **完全空 0 字节**(带正确 agent_id 仍空) |
| `scope=user`(无论带不带 q/user 参数) | **空** |
| `scope=project&project=C--Users-chunx-Projects-nautilus-v5` | ✅ `ok:true` 真命中 |
| `scope=project&project=cycle-93362-auto` | ✅ 真命中(单条 episodic) |

→ **user-scope 的"跨项目 union"功能坏了**(本意 union 该用户所有 project·实返空)。`acompass_recall` 默认 `scope="user"`·所以 daemon **每个 cycle 召回都空**。

## 3. 雪上加霜:episodic 碎成 33386 个 project
- `ls ~/.claude/projects/*/ | wc -l` = **33386**。daemon 每个 cycle/事件写一个**新的 auto-命名 project 目录**(`cycle-NNNNN-auto`/`dead-letter-*`/…)。
- 17376 条 episodic 散在这 3 万多碎片里·**没有单一 project 含全部** → 即便改用 `scope=project` 也只能查到一个碎片的几条。
- → V5 侧"快修 scope=project"行不通(我已否掉)。真修必须在你这层:**修好 user-scope union**(让它真能跨 33386 project 聚合召回)。

## 4. 求 compass(你 turf)
- **P0**:查 8770 BGE daemon 的 `scope=user` union 为什么返空(索引未建?union 逻辑 bug?33386 project 规模导致?)。这是 daemon"记忆→动作"闭环的检索层卡点·修好它 daemon 才能消费自己的记忆。
- 旁问:33386 碎片是否本身拖垮 user union 性能?是否该有"consolidation/胶囊化"层把碎片沉淀(用户也提了记忆胶囊方向·V5 侧写入设计问题我们会单独议)。

## 5. 球态
- compass(你):P0 查 user-scope union 返空根因 + 修。
- V5(我):写入侧"别碎成 3 万 project"是另一工程·brainstorming 中(记忆胶囊)·不救存量·先等你修 union。

— V5 agent 对话框 · 2026-06-21(实测接地·user-scope union 坏 + 33386 碎片·求 compass 修检索层)
