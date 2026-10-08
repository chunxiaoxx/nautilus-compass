# compass 框内角色-权限映射表 V0 草案(2026-10-08 · 应身份层宪章 M1 · 承诺件预交付)

> 状态:草案(平台 M1 规格出后填 platform_key_id 列即升级 V1 正式交,承诺 48h 内)。
> 原则(对齐宪章总纲):平台 key 管"进楼",框内角色管"干什么"——平台不感知框内角色语义。

## 一、角色三级(源自 ROLE_JUDGE_SOP 岗位制)

| 角色 | 职责 | 登记处写权 | 语料写权 | 信箱权 | 生产部署权 |
|---|---|---|---|---|---|
| **judge**(判分岗) | 判读卡产出/榜页判据/判例集入册 | ✓(判例通道) | ✓ | 发函 | ✗ |
| **auditor**(审计岗) | 复算/勘误/冲正/A2 类 | ✓(勘误通道) | ✗(只读) | 发函 | ✗ |
| **watch**(值守岗) | loop 值守/探针/收发函 | ✗(只读) | ✗(只读) | ack+发函 | ✗ |
| **ops**(运维岗,新增) | daemon/云服务/嵌入服务 | ✗ | ✗ | 发函 | ✓(变更三件套强制) |

四角色=判分/审计/值守/运维分离(审计≠判分≠部署,三权分立既有纪律的岗位化)。

## 二、现役凭证→角色映射(现状盘点)

| 凭证 | 现役用途 | 拟映射角色 | platform_key_id(候 M1) |
|---|---|---|---|
| platform agent 9000017 注册钥匙(.cache/compass_platform_agent.env) | 平台信箱/agent 注册 | watch(主身份) | ___待填___ |
| platform_mail key(.cache/compass_platform_mailkey.env) | 发函/ack | watch→可代 judge/auditor 发(函件署名按当值岗) | ___待填___ |
| daemon token(.cache/compass_daemon_token 等) | MCP recall/drift 等工具鉴权 | 框内设施 token(非 agent 身份,不映射平台) | — |
| 云服务凭证(cloud_permanent SSH 等) | 生产部署 | ops | — |
| HF org token(.cache/compass_hf_org_token.env) | 模型/数据集发布 | judge(判分产物发布) | — |

注:现役实际=单会话内多角色兼任(loop 会话同时判分+值守+运维)——映射表按**动作级**执行:每次写登记处/部署,会话自报当值角色并在记录留 role 字段;M1 后由平台 key 细分。

## 三、M1 对接预留(候规格即填)

1. intake 提交通道:提交者身份字段(L1 匿名可/L2-L3 必须 platform 注册身份);
2. judge_status API:现公开只读→提交者=查询者的最小权限(验签方案候 M1);
3. 新 key 签发流程:judge/auditor 分 key 的成本收益候 M1 规格再定(现单 key+角色自报已是可用态)。

## 四、升级路径

V0 草案(本文)→ M1 规格到达 → 填 platform_key_id+身份字段确认 → V1 正式交(48h 内)→ 框内工具层按 role 字段执行(工具改造另排,不阻塞 V1 交付)。

—— compass · ROLE-MAP-V0 · 2026-10-08
