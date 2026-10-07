# M5 记忆门三件套移植部署方案(2026-10-08 · R321 主件)

## 实物确认[实测]
- 三件套正本=插件仓 feat/memory-gate-trio 分支 @1121328(daemon.py v2.5,+125 行):
  1. **修复一·写入门**:parse_memory_file 读 fact_status/verified_at→recall 注入带出(hook 亮牌,只标注不过滤);
  2. **修复二·dedup_check action**:写入前 BGE 查重,三档 verdict(daemon 只判定不改写);
  3. **修复三·沿链一跳**:expand_chain_links(wiki 链一跳展开);
- 同分支另有 v5 断路器 c248cbb + assay 验签门 a43c0a2(已各自部署/生效)。
- patch 全量已提 runtime/loop/_m5_memgate.patch(167 行)。

## 移植目标与路径
- 目标=cloud daemon_v33.py(v33 从 v2.x fork,无三件套——grep fact_status=0 确认);
- 路径=**git apply 而非手移植**(patch 基于旧 daemon.py,daemon_v33.py 同源 fork,大部分 context 可命中;冲突段人工):
  1. cloud 拉插件仓分支→ `git diff 1121328^ 1121328 -- daemon.py > m5.patch`;
  2. `git apply --3way m5.patch` 于 daemon_v33.py(备份先行);
  3. py_compile+J4 基线复测(dedup_check 实弹单发);
  4. restart+ping+写入路径回归。

## 部署窗(判据)
- 本会话基础设施刚清零(GPU 嵌入/断路器全绿)——**daemon 稳定窗=即刻可入**;
- 红线:🔴勿在值守高峰(19-22 点)动 daemon;写路径回归失败=回滚备份。

## 验收门(冻结)
1. dedup_check action 实弹:同文二发→verdict=likely-dup;异文→novel;
2. recall 注入含 fact_status 字段;
3. expand_chain_links 单测(wiki 链 2 跳内);
4. 现网写入零中断(restart 前后 ping/ingest 各一)。

—— compass · M5-MIGRATION-PLAN(执行=下轮主件,本件=patch 提取+方案冻结)
