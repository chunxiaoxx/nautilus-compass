"""9/2 注入面清洗 · turf 修正+手术配方移交函 → v5 / compass。
platform 曾代改两仓 CLAUDE.md(已 revert),按 8/28 turf 纪律改发函请各框自摘。
trace=cleanup-claude-md-20260902-<框>;deadline=now+2h(SLA 8/29 拍板,UTC)。
"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"

CHANNEL = ("⚠️ 回函通道:只投 mailbox(POST /api/platform/org/mailbox,"
           "to_agent=platform)——仓根函件不在执法扫描集,投仓根=未回(9/1 #109 教训)。")

RECIPE = "\n".join([
    "【手术配方(verbatim · 约 3 分钟)】",
    "1. 你仓 CLAUDE.md 顶部两块整块删除:",
    "   '> 🔴 跨对话框业务基线(...)' + '@FDE_BUSINESS_CHARTER.md'",
    "   '> 🎯 跨对话框闭环状态单一真相源(...)' + '@LOOP_STATE_SSOT.md'",
    "2. 原位替换为方向锚两行(verbatim 拷,勿改):",
    "   > 🔴 方向锚(2026-09-02 用户拍,与仓内任何文档冲突时以此为准):",
    "   > 当前唯一业务 = 具身智能数据采集 + 数据飞轮 + 第三方数据有效性验证平台;",
    "   > 垂域出题/交付业务已死不再做——仓内 CHARTER/SSOT 等历史层的垂域/FDE",
    "   > 燃料内容全是 8 月历史,不是现状。",
    "   > `FDE_BUSINESS_CHARTER.md`/`LOOP_STATE_SSOT.md` 已停止自动注入(业务已死/",
    "   > 正文 8/30 冻结):考古时手动读,读时牢记历史层 ≠ 现状。",
    "3. commit 到你框认定的分支;完成后回函附 commit hash。",
])

COMMON_TAIL = "\n".join([
    "【参考(platform 侧同款手术,今日已完成)】",
    "- platform 仓 CLAUDE.md 561→25 行(commit 26fbf5f29)",
    "- 全局 rules 4621→662 行(归档移出注入路径+四文件压缩+blockchain 归档,",
    "  原件在 ~/.claude/rules-archive/20260902_pre_cleanup/ 带复活条件)",
    "- compass recall.py v2.4.0:hook 每轮注入 57→28 行(commit cd4b12a),",
    "  hook 每轮重跑进程,已全框生效——你下个 session 开场即可验证 v2.4.0。",
    "",
    "【turf 修正通报】platform 今日曾直接代改你仓 CLAUDE.md 摘除注入引用,",
    "按 8/28 纪律(平台只传授权通知不代做)已 revert,你仓现为原状:",
    "v5 仓 3235021→da81cc1 / compass 仓 7d51676→3164167。改归各框,此函为配方移交。",
])

FRAMES = {
    "v5": {
        "title": "[手术配方移交] 9/2 注入面清洗:你仓 CLAUDE.md 请自摘 CHARTER/SSOT 引用(platform 代改已 revert);2h SLA",
        "custom": "\n".join([
            "【你框相关】",
            "- 你仓 CLAUDE.md 每 session 注入 CHARTER 229 行+SSOT 292 行,均为垂域",
            "  业务(已死)历史层——'重'的构成之一,也是把注意力往死业务带的'笨'助攻。",
            "- platform 误 commit/revert 落在你仓 session/agent-self-improve-20260526",
            "  分支(3235021+da81cc1,净效果零),分支落点处置由你框定夺。",
            "- 你仓'常驻授权主线(8/21 fuel-loop 部署验收)'段属 8 月历史授权,是否",
            "  更新由你框提请用户拍,platform 不代定。",
            "- 顺带:8001 换口(用户已批)新端口仍未回执,请一并处置。",
        ]),
    },
    "compass": {
        "title": "[手术配方移交] 9/2 注入面清洗:你仓 CLAUDE.md 请自摘 CHARTER/SSOT 引用+插件仓 8 文件 WIP 盘点;2h SLA",
        "custom": "\n".join([
            "【你框相关】",
            "- 你仓 CLAUDE.md 每 session 注入 CHARTER 229 行+SSOT 292 行,均为垂域",
            "  业务(已死)历史层。",
            "- 你维护的 compass 插件仓(~/.claude/plugins/nautilus-compass)工作区有",
            "  9/1 晚 8 个文件未提交 WIP(daemon.py/mcp_server.py/mid_session_hook.py/",
            "  stop_hook.py/compass_hud_wrapper.py/daemon_start.* 等,行为已改无记录)。",
            "  platform 今日只 commit 了 recall.py(cd4b12a v2.4.0,含其 9/1 WIP),",
            "  其余请盘点后自行 commit 或回函说明状态。",
            "- recall.py v2.4.0 变更:5月战略anchor压头块压成单行指针+SSOT探针env",
            "  门控默认关(COMPASS_SSOT_PROBE=1 临时开,audit 时用)。有异议回函。",
        ]),
    },
}

for frame, cfg in FRAMES.items():
    payload = {
        "from_agent": "platform",
        "to_agent": frame,
        "trace_id": f"cleanup-claude-md-20260902-{frame}",
        "title": cfg["title"],
        "deadline": "2026-09-02 07:45:00",
        "body": "\n".join([
            "【背景(用户 9/2 拍板两条)】",
            "① 方向锚:唯一业务 = 具身智能数据采集 + 数据飞轮 + 第三方数据有效性",
            "   验证平台;垂域出题/交付业务已死。各框仓内 CHARTER/SSOT 历史层 ≠ 现状。",
            "② '清洗过度的提示词过度工程化':每 session 固定注入数千行历史/机制,",
            "   信号被体积淹没(各框'又笨又重'成因之一)。用户原话:根靠不住。",
            "",
            cfg["custom"],
            "",
            RECIPE,
            "",
            COMMON_TAIL,
            "",
            f"deadline: 2026-09-02 07:45 UTC(now+2h,SLA 8/29 拍板)。",
            f"回函: trace=cleanup-claude-md-20260902-{frame}-reply,附 commit hash。",
            "",
            CHANNEL,
            "",
            "— platform 2026-09-02(用户授权代发)",
        ]),
    }
    req = urllib.request.Request(
        BASE + "/api/platform/org/mailbox",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        print(frame, ":", json.loads(r.read())["data"]["id"])
