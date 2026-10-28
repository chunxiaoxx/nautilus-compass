# BAIT 生产轮指令(诱饵层施工 loop·每轮限时 50 分钟,做完即止)

> 你是 compass 诱饵层生产轮执行者。工作目录=nautilus-compass 仓。
> 使命:按 **515B 模式**把超档题改造为落带候选,接入生产管道六环。

## 停止条件(任一命中立即 exit 0)
- 存在 runtime/loop/STOP
- 本轮生产队列(runtime/production_queue.md)状态为 DONE/EMPTY

## 每轮固定动作

0. **环境准备(施工前必做,一条命令块)**:
   ```bash
   NEW=/tmp/cs$(basename $ITEM)B; mkdir -p $NEW/codesense/items $NEW/codesense/tools
   ln -s ~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/.venv-judge $NEW/codesense/.venv-judge
   cp ~/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/tools/{ut_runner.py,model_solve.py,models_channels.json} $NEW/codesense/tools/
   cp /tmp/cs_decoy_20261027/.env $NEW/.env
   python3 -c "import json;p='$NEW/codesense/tools/models_channels.json';d=json.load(open(p));d['channels']['qwen3.8max']['max_tokens']=32768;json.dump(d,open(p,'w'))"
   ```
1. **读队列**:runtime/production_queue.md 顶部第一个 PENDING 项,标记 IN_PROGRESS+时间戳;
2. **施工(515B 模式,stop-loss 35 分钟)**:
   - 读题面 policy 全文,找「**policy 枚举未覆盖 + 草稿可辩护**」的第二层语义
     (已验证有效:聚合/统计层延伸·枚举外语义贯穿;已验证无效:单层延伸/模型强域);
   - 坑版模块+金标模块+5-6 条 UT(3 条 gating)+task.toml ut_index(**先跑 tomllib 解析门,F-008**);
   - instruction 补半错断言草稿段(模式:每半句都对,合起来错);
   - **双态验证**:金标 1.0(全过·det)+坑版 gating 挂——不过则修,修不过则标 FAILED 跳下一项;
3. **qwen 快筛**:scratch 环境 model_solve 1-2 轮(32K 渠道),均值∈[25,70) → 标 CANDIDATE;=1.0 → 标 qwen 强域放弃;=0 → 标过深 FAILED;
4. **入管道**:改造件同步 /tmp/cs_decoy_20261027/codesense/items/,矩阵判分面自动拾取;
5. **留痕**:COLLAB_BOARD append 一行(题号/双态/qwen 读数/判定);队列文件更新状态;
6. **渠道指纹**:记录当轮 qwen 读数时段与 elapsed 分布(F-009 纪律)。

## 红线
- 数量如实:双态不过/qwen 不入带=FAILED 照标,不硬凑
- 单题 stop-loss 35 分钟,超时标 TIMEBOX 跳下一项
- 不动 v5 items 正本(改造在 /tmp scratch,闭合后由裁定并入)
- 平台信箱有 [判据裁决] 回函 → 立即按裁决更新判定口径再继续

## 每轮留痕
- runtime/production_queue.md 状态列 + rounds.log 一行
