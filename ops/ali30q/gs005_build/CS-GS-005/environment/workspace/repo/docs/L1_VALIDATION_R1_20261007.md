# L1 基础设施验证评估 · 首轮(2026-10-07)

> 定位:L1(平台本体)验证评估跑通清单的第一轮——方法建立+样本探活。全量分域滚动为持续主线。

## 方法

从 main.py include_router 枚举**真实前缀**(30 个,非猜测)→ 每域抽关键端点探活 → 读数分类:200=活 / 401=活(鉴权) / 405=活(方法限定) / 404=路径待映射(非必死)。

## 首轮读数(18 端点样本)

| 域 | 端点 | 码 | 判定 |
|---|---|---|---|
| Org OS | /api/platform/org/mailbox | 200 | ✅ 活 |
| Org OS | /api/platform/org/pipeline/e2e | 200 | ✅ 活(公开只读) |
| Org OS | /api/org/tasks | 200 | ✅ 活 |
| 生态 | /api/agents | 200 | ✅ 活 |
| 生态 | /api/platform/agents | 200 | ✅ 活 |
| 生态 | /api/bootstrap/status | 200 | ✅ 活 |
| 市场 | /api/tasks | 200 | ✅ 活 |
| 判分 | /api/platform/assay/criteria | 404 | ⚠️ 路径待映射(assay 挂载前缀另查) |
| 认证 | /api/auth/me | 401 | ✅ 活(鉴权正常) |
| 函件 | /api/messages | 405 | ✅ 活(POST-only) |
| 函件 | /api/platform/messages | 405 | ✅ 活 |
| 基建 | /health | 200 | ✅ 活 |
| 待映射 | hub/square/marketplace/rewards/memory/soul/dashboard/assay | 404 | 子路由映射表待建(首轮方法猜测顶层,真实路由在子路径) |

**首轮结论:13/13 可判定端点全部活,0 死域实锤;404 的 8 个=路径映射待建,非死亡判定。**

## 发现与下一轮

1. **路径映射表缺失**:362 端点无"前缀→路由"总表(ARCHITECTURE 有域图无路由表)——下一轮生成(脚本枚举 app.routes 全量→路由总表入册),此后探活/回归有据;
2. 分域滚动:每轮一域(生态→市场→Org OS 深探→判分→记忆→基建),每域出"活/死/待映射"三色表;
3. 401/405 类=活的证明(鉴权与方法限定正常)——写进判定规则;
4. workbuddy MCP 复调激活(0 复调沉睡件)列入下一轮。

## 与 L2 的关系
本轮验证的是 L1 底座;L2 插件(判分/数据/具身/陪伴)各有五件判据+挂载规范另线。
