# NAS 迁移数据全景图(2026-10-16 · R545)

> NAS(D: = \\NASNEW\work,凭据 admin)上的四代迁移/备份数据盘点——防止后续误删/误并/混淆新旧。

## 全景表

| 目录 | 内容 | 代际 | 状态 |
|---|---|---|---|
| `migrate-to-laptop/`(54 项) | **第一代**:台式机→笔记本(7/14)全量存档(.agents/.aws/.cc-switch/.claude/Desktop/Documents…) | 历史存档 | 保留不动 |
| `chunx-migrate/`(4 项) | 桌面杂项打包(kimi package/豫深资本活动) | 历史存档 | 保留不动 |
| `backup-git-20260923/` | nautilus-compass 镜像备份.git + rewrite-work(9/23 git 事故抢救件) | **重要历史** | 保留不动 |
| `backup/` | chunx-pc 备份 | 历史存档 | 保留不动 |
| **`migrate-to-macmini/`** | **第二代(进行中)**:openclaw 的 laptop-claude/(README+导入工具)+ pc1/pc2 子目录 | 现役 | 包待入 |
| **`nautilus-migration/`** | **compass 打包(10/16)**:14 包 816MB(8 项目会话+3887 记忆+config,manifest sha256) | 现役 | openclaw 导入待执行 |

## 演进链(防混淆)

```
台式机 --7/14--> migrate-to-laptop(第一代,NAS 中转)
笔记本 --10/16--> migrate-to-macmini(laptop-claude/,openclaw 导入工具链)
compass 语料/记忆 --10/16--> nautilus-migration(manifest 校验,独立于上面两代)
```

## 纪律

1. **三代数据并存,一律不删不改**——NAS 即组织档案层;
2. 新迁移一律**独立目录+manifest sha256**(nautilus-migration 模式),不复用旧目录;
3. openclaw 导入时**只读 nautilus-migration**(compass 的包),勿混 migrate-to-macmini 的旧件;
4. 后续若做 NAS 数据治理(合并/清理),先出方案档候用户批。

—— compass · R545 · 2026-10-16
