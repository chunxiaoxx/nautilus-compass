# 网站架构设计 V1(正本 · 2026-10-08)

> 依据:RFC 六议题共识+用户裁 (b)+1+三层叙事纠偏+资产考古清单。任何框动网站先读本篇。

## 一、分层叙事(L0→L2,访客视角)

```
L0 品牌:nautilus.social 首页 hero
        "一群 AI,像一个组织一样工作、结算、自我迭代"
L1 信任:组织操作系统(六件真家伙)+基础设施(插座/中转/判分底座/GPU)
        —— 访客先信"这个组织是真的",才谈买
L2 变现:六条产品线,每卡带 CTA 下单入口
        判分评测 / SWE数据集 / 具身数据 / 陪伴智能 / 创投内容 / 元基准+NACRE
        (+自研 harness·涡轮增压 = 组织自己的生产底座展示)
```

## 二、域名拓扑(裁 (b) 混合:在役子域+新内容根路径)

| 域 | 内容 | owner | 状态 |
|---|---|---|---|
| **nautilus.social**(根) | 门面三层+判分五页+products/*+docs+developers | platform 装订 | 在役 |
| **bench.** | agent 评测产品(V2.2) | v5 | 候挂(flywheel 迁毕净空) |
| **data.** | 具身产品页群(+/bench 迁入路径) | flywheel | 在役 |
| **compass.** | 记忆层产品页 | compass | 在役 200 |
| **i.chunxiao.wang/org/** | 文档镜像(BYZ 案卷)+zenmind 两册 | platform 装订/zenmind | 在役 200 |
| **api.chunxiao.wang** | LLM 中转站 | hr | 在役(developers 页如实披露=自用基础设施) |

规则:子域名=有真实流量/SLA 的在役服务;新页面一律根路径 `/product`;子域间页头互链+回根链接。

## 三、技术栈(共识:零新栈)

- **内容页**=md→HTML 渲染器(flywheel `_render_twoshells.py` 在役,og 版本串自动提取+滞后检测);静态文件 nginx 直出
- **活页限五**(fetch 同域 /api):index 轨迹池 / pipeline / registry 计数器 / status 判读卡查询 / criteria——真实数据即信用;API 限流 60/min 已配
- **禁项**:不引前端框架/构建链;不走外部托管(7/17 红线);不留 .bak 于 sites-enabled

## 四、目录与正本约定

```
云 /var/www/nautilus/current/     ← 唯一对外根(改动=装订员 SOP 六步+md5 登记)
├── index.html(活:轨迹池+产品线卡+基础设施读数)
├── unipat/intake/criteria/pipeline/leaderboard(判分线,正本 phase3/frontend/)
├── registry/status(compass@runtime/site/ 正本)
├── products/*(六线卡:harness 本地详页,embodied/companion/compass=导流页)
├── org/(两外壳案卷镜像)
└── developers.html(本设计新增:开发者入口)
正本仓库:nautilus-core(phase3/frontend+docs/web)/ nautilus-v5 / nautilus-compass(runtime/site)/ nautilusflywheel(渲染器)
```

## 五、装订治理(生产系统)

流程=信箱总线提交材料(md+仓@commit 坐标+版本号)→装订员审材(坐标可寻址/版本一致/无未批对外承诺)→**考古前置**(存量有=增量接线,无=才新建)→渲染(统一视觉)→上站(三验:200+标记+md5)→台账登记→回执。
**装订权≠内容权**:平台持挂载/视觉/验收权;各框保留内容正本权与撤回权;一页一 owner,代修须登记(leaderboard 先例)。

## 六、演进路线

- **V1(10/12 开业)**:根域三层+六线导流+bench 归位+两外壳 web 版+developers 页 + 全站探针矩阵
- **V2(10/20 前后)**:Step2 自助发单台 / 状态页(SLA 数字须用户批) / 搜索
- **V3(L2 首单后)**:c 档托管客户面 / 多语言 / 元基准公开判读入口

## 七、与现状差距

见作战板 SITE_BUILD_BOARD_20261008.md(17 件,loop 每轮刷)——本篇=稳定设计,该篇=动态待办。
