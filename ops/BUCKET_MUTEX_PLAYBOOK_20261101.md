# 桶操作互斥 playbook(openclaw / compass 并桶单飞锁)

> 产出:P-w3(REVIEW_mac_sessions_20261031 桶副本治理)· 2026-11-01
> 授权口径: compass 侧已执行归档(见 §四);openclaw 侧本 playbook 交付后自决,**compass 不代 openclaw 动手**。
> 适用范围: `~/.claude/projects/` 下任何桶级写操作(归档/清理/迁移/批量改名)。只读探查(ls/du/grep)免锁。

## 一、为什么需要互斥

两框共享同一台 Mac 的 `~/.claude/projects/` 目录树:
- openclaw = Mac 运维顾问,经 NAS 任务单接单,可能被派"清理/归档/体检"类任务;
- compass = 记忆门 M5 宿主,daemon/hook 持续读写正本桶,也可能执行治理任务。

P-w3 实测教训: 同名桶存在多副本(dup/migrated/正本空壳),若两框并发各自动桶(一个在归档、一个在恢复或审计),会出现 mv 竞态→半移状态→审计误读。**桶级写操作必须单飞。**

## 二、单飞锁设计

锁坐标: `~/.claude/projects/.bucket-op.lock/`(目录型锁,mkdir 原子性跨进程成立)

```
拿锁:  mkdir ~/.claude/projects/.bucket-op.lock 2>/dev/null || 拒绝执行(已有持有者)
锁内容: ~/.claude/projects/.bucket-op.lock/owner 文件,写三行:
        frame=<compass|openclaw|other>
        task=<一句话操作描述>
        started=<ISO8601 时间戳>
放锁:  rm -rf ~/.claude/projects/.bucket-op.lock
僵死判定: 锁存在且 started 距今 >30min → 可接管(先 mv 原锁为 .bucket-op.lock.stale-<ts> 留证,再重新 mkdir)
```

纪律:
1. **持锁期间禁止跨框并发**——openclaw 拿到锁时 compass 侧等待,反之亦然;
2. 拿锁成功后向 NAS 任务单/平台信箱发一行 `[kind:touch]` 报备(10/18 触客登记制);
3. 长操作(>10min)每 10min 续写 owner 文件的 heartbeat 行;
4. 锁只护桶级写操作,**`C--Users-chunx-Projects-nautilus-core` 永不归档永不清理**(memory 定谳: 平台框本体)。

## 三、两框操作规程

| 框 | 只读探查 | 桶级写操作 |
|---|---|---|
| compass | 免锁 | 必须 mkdir 拿锁+报备+放锁 |
| openclaw | 免锁 | 同上;接 NAS 单时若任务含桶写,先拿锁再动,拿不到锁回单"等待 compass 释放" |

冲突裁决: 后到者等;僵死锁按 §二接管流程留证后接管。

## 四、已执行事实(2026-11-01,compass 侧)

| 对象 | 处置 | 坐标 |
|---|---|---|
| `C--Users-chunx-Projects-nautilus-compass.dup20261023`(743M) | 归档 mv | `~/.claude/projects-archived-1031/` |
| `C--Users-chunx-Projects-nautilus-compass.migrated`(743M,dup 子集+6 条尾部差异) | 归档 mv | 同上 |
| 正本桶 1289 个 0 字节空壳 jsonl(10/23 00:09:41 迁移批次产物) | 归档 mv | `~/.claude/projects-archived-1031/empty-shell-jsonl-1031/` |
| 正本桶剩余 352 个 jsonl | 未动(全部非空,Mac 期活会话) | 原位 |
| `C--Users-chunx-Projects-nautilus-core` | **未动·永不归档** | 原位 |
| cycle-N*-auto 桶群(~1910 个,216M) | **未动·非 compass 产物** | 原位,frontmatter agent_id=nautilus-prime-001(v5 侧),候 v5 另案 |

回滚: `mv ~/.claude/projects-archived-1031/<桶名> ~/.claude/projects/<桶名>` 即可原样恢复。

## 五、候用户决策 → 执行结果(2026-11-01 用户拍"四件全做",compass 侧执行)

1. **恢复真身** ✅ 已执行: `rsync -a --ignore-existing` dup→正本(2659 文件/527MB);正本终态 1639 jsonl/1100 memory/145 UUID 目录/0 空壳;md5 抽样 20/20 PASS+comm 零缺失。Windows 期全史回归正本。
2. **868 条 session_auto 合并** ✅ 已执行: 同一条 rsync 完成,正本 memory 1072→1100 条,recall 可达。
3. **cycle-1910 桶转 v5** ✅ 已发函: 平台 id 24936(收件框名 registry 定谳=`v5`/9000018),规模复核 1978 桶/221MB,compass 不动,deadline 2026-11-08。v5 若动手须按 §二/§三 拿锁。
4. **C--Users-chunx 归档** ✅ 已执行: symlink 本体+待归档说明 txt → `~/.claude/projects-archived-1031/C--Users-chunx.dup20261023`;目标桶未动。回滚=mv 回原位。
5. **授权外新增亮牌**: `C--Users-chunx.migrated`(同性质 symlink,同指目标桶)未动,候用户决定是否同批归档。
