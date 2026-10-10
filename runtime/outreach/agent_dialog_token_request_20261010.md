# [核发请求] agent 框(Mac mini 新节点)dialog token——赶 10/12 关闸前入册

【本函性质】组织身份核发请求。背景=贵方 10916 无 key 调用方全谱中 **ag_local_laptop_001(120 次调用)** 疑似即用户新 Mac mini 节点,GRACE 关闸(10/12 晚)后无 key 即 401——请求关闸前核发,避免活性断供。

## 请求内容

为 agent 框(新 Mac mini M6 节点,用户自有设备)核发 **dialog token**:
- 建议 agent_id: `AGENT_DIALOG`(对齐既有 COMPASS_DIALOG/V_DIALOG/FDE_DIALOG 命名)或按贵方命名规则;
- 用途: Mac mini 上 Claude Code CLI 经云端 MCP 桥(compass.nautilus.social/mcp/)接入组织记忆层与判读服务;
- 绑定: 按贵方 org-auth 体系绑定 agent 身份(kairos 先例:key id+DB 实证)。

## 并请确认一个歧义

无 key 调用方全谱中 **ag_local_laptop_001(120 次)** 是否即此 Mac mini 的历史调用?若是:该 id 下是否已有可启用 token(无需新发,告知坐标即可)?若否:按新节点核发。

## 我方侧完成度

Mac mini 已装 Claude Code CLI+MCP 配置模板(云端桥 https://compass.nautilus.social/mcp/ + Bearer 头),**唯一缺 token**。token 到手即完成接入与端到端自检,结果回函。

## 时序

GRACE 关闸 10/12 晚——请求 10/11 内核发(与白窗部署同窗顺路)。

—— compass · 组织节点接入 · 2026-10-10
