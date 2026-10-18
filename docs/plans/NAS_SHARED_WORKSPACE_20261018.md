# NAS 共享工作盘方案(2026-10-18 · R546)

> 目标:NAS 从"迁移中转站"升级为**组织共享工作盘**(对内多机协同)+ **对外网盘中转层**(对外发布经 cloud,NAS 永不直接暴露公网)。

## 一、定位与安全红线

1. **NAS = 存储中心**(12GB 级大文件的家:数据集/判读包/模型/产物),各电脑是瘦端;
2. **🔴 NAS 永不直接暴露公网**——对外文件一律经 cloud(43.160.239.61)发布(NAS 在内网 192.168.5.25,公网唯一入口=cloud nginx);
3. **三代迁移数据并存不删不改**(NAS_MIGRATION_DATA_MAP 纪律不变),本方案的 `shared/` 是新树,不复用旧目录;
4. 任务单通道继续用(已验证:反向隧道任务单零依赖跑通)。

## 二、目录结构(\\NASNEW\work\shared\,新建)

```
shared/
├── inbox/          # 各机投递中转(谁放谁署名:inbox/<from>-<date>-<desc>)
├── projects/       # 跨机项目工作区(大产物:数据集/judge pack/模型权重/渲染产物)
├── scratch/        # 临时暂存(纪律:30 天后人工清,放前想好命名)
├── outbound/       # 待对外发布(openclaw 推到 cloud 发布目录后移入 outbound/published/)
└── tasks/          # 任务单通道新址(nautilus-migration 通道在途,迁完再并)
```

## 三、各机接入

| 机器 | 方式 | 状态 |
|---|---|---|
| Windows 笔记本 | `D:`(\\NASNEW\work 映射,已有) | ✅ |
| Mac mini(openclaw) | SMB 挂载(任务单已验证可读写) | ✅ |
| 台式机 | SMB 映射:`net use W: \\NASNEW\work /user:admin` | 待用户手动 |
| cloud(公网) | **不挂载**。需文件时经 openclaw 拉/推(任务单或 rsync 定时);未来可选:复用 Mac mini 反向隧道扩 SSHFS | 设计如此,勿开公网 SMB |

## 四、对外网盘(经 cloud 中转)

1. 发布目录:cloud `/home/ubuntu/publish/`(nginx 加路由 `/files/`,X-API-Key 或签名链接鉴权——判读交付物给客户走的正是这条);
2. 流向:NAS `shared/outbound/` → openclaw rsync 推 cloud → 客户拿链接 → openclaw 回写 `outbound/published/`;
3. 大文件驻 NAS,cloud 只放"已发布快照"(防 cloud 磁盘打爆,cloud 无扩容纪律见 S6)。

## 五、真实场景接线(不做空壳)

1. **判读交付**:judge pack/判读卡 → outbound/ → 客户链接(取代临时 scp);
2. **跨机大件**:笔记本↔Mac mini↔台式机 传包一律走 shared/scratch/(取代聊天工具传文件);
3. **openclaw 自备份**:Mac mini 会话/记忆定时增量 tar → NAS `backup-openclaw/`(新目录,待任务单);
4. **cloud 归档**:判读产物定期由 openclaw 拉 NAS 存档。

## 六、实施顺序

- [x] 本方案档 + shared/ 目录树建立(2026-10-18)
- [x] claude-import 任务单已投(TASK_claude_import_20261018.md)
- [ ] openclaw 任务单:rsync outbound→cloud 发布目录 + nginx 路由(下张)
- [ ] openclaw 自备份任务单
- [ ] codex v2 重传(进行中,后台打包)

—— compass · R546 · 2026-10-18
