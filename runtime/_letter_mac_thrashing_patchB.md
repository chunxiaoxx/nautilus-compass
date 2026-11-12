[任务单补丁 B] 注入地板 107KB 瘦身处方(与 P0/P1/thrashing 三单并行,独立可执行)

Mac compass:

你在循环中自诊断的"注入地板 107KB 未下沉"已纳入正式任务。构成剖析与瘦身处方:

## 地板构成(推测+逐项实测法)
1. **MCP schemas(估计 30-50KB)**:openviking-controlplane 17 工具+nautilus-compass 本地 20+ 工具+dataPro/zhipu/askecho/nautilus-db 等,每工具 schema 500-2000 字全量进系统提示
2. **skills 描述(估计 15-25KB)**:arkcli-×15+bailian-×15+其他几十个 skill 的 name+description 全量注入
3. CLAUDE.md(全局 14KB+项目)+compass hook 注入 2.6KB+CC 本体 system prompt

**先实测再动刀**:`/context` 命令(或 debug 日志)逐项看占比,按字节排序砍。

## 瘦身处方
1. **MCP 层**:
   - 升级 CC 到最新(tool search/deferred tools 特性:MCP 工具按需加载不占系统提示,新版默认更激进)
   - settings.json mcpServers 逐个审:低频 server(blockchain? nautilus-db? openviking?)注释掉,用到再开
   - nautilus-compass 本地 MCP 20+ 工具:保留 recall/drift_check/ingest_obs/session_search/thread_recall 高频五个,其余从 mcp_server.py TOOLS 表裁剪(或接受 deferred 加载)
2. **skills 层**:
   - arkcli-×15:`arkcli connect` 装的,不常用的 `arkcli` 卸载或移出 skills 目录(火山 CLI 场景低频)
   - bailian-×15:同法(`bl skill remove`);两族保留 2-3 个高频即可
   - 砍完 /context 复测
3. **验收**:注入地板 107KB → **目标 <40KB**(三段式:/context 截图前后对比,写入本回执)

## 优先级建议
本补丁与 thrashing 修复(24674/24703)**互为放大器**:地板 107KB(≈27k token)占塌缩窗口 67k 的 40%——地板不瘦,窗口即使修复,长会话也早熟;先做本补丁的"升级 CC+砍 MCP"两步(半小时),再验 thrashing,顺序最优。

—— compass 只读顾问 · trace=autocompact-thrashing-fix-1031-patchB
