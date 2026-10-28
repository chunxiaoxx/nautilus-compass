# 网站系统全面体检报告(2026-10-10 凌晨 · 全实测)

> 范围:七站五域建设+运行全景/查漏/前端美化/前后端融合。方法:生产 curl 逐面探测+源码盘点,零自报。
> 服务目标:10/11 22:00 全绿=10/12 开业门面(10/8 作战板令)。
> **执行修正(10/10 凌晨 P1 落地后)**:#1 撤销(线上首页导航条 13 链齐备,含 v1.7 白皮书/BP——初判系探针 pattern 盲区);#2 已收敛(301+port_in_redirect off);#3 已落地(五页 tokens+根域 tokens.css 上线);#5 已答(受理 API=/api/platform/org/assay/submissions,422 在役)。查漏余 #4/#6-9。

## 一、全景现状

| 站/域 | 建设态 | 运行实测 |
|---|---|---|
| **主站** nautilus.social | 静态门面:九页+sites/developers/customer/admin+login/intake/status;源码 phase3/frontend | 12 面全 200;OG 九页全覆盖;submit 页 200 |
| **app** app.nautilus.social | React SPA 41 页(源码 **phase3/website**:vite+ts+react-query+web3auth);统一后台+客户门户+/live 活页 | 10 路由全 200;数据面 agents/bounties/health 200+users/stats 401(登录门正常);白名单门禁生效;**tokens.css V1 唯一落点** |
| **bench** | 榜页 V2.1 数据驱动+判据披露页 | 200;CTA 实链主站 /submit/(200 通);marker 命中 1(正式终检再核) |
| **data** | flywheel 域,同源闸标杆 | 200 |
| **compass** | 站页 | 200;页脚互链候(B5) |
| **fde+周边** | fde/crm/hr-chunxiao/api 中继(i 域 zenmind) | fde 200;zenmind/hr 静默中 |
| **部署层** | nginx systemd 已交接(10/9);443=SNI 分发;conf 正本入仓(10/9 刷新) | 五站 200;403 双封生效 |

## 二、查漏清单(★=今晚体检新抓;○=已知遗留)

1. ★ **导航体系漏链两外壳+pricing**:首页与 sites.html 的链接面均无 /whitepaper/、/bp/、pricing——两外壳(BP/白皮书)游离在导航外,开业门面不可接受。
2. ★ **双白皮书路径并存且版本不同**:/whitepaper/(新渲染·组织叙事)与 /org/whitepaper.html(旧版·技术白皮书)title/内容两样——口径漂移+SEO 分裂;需定位保留版+另一路径 301。
3. ★ **tokens.css V1 未铺开**:仅 app 域落地;根域 index/sites/developers/customer 均 0 引用——L1 设计系统停在单点。
4. ★ /live 页两小项遗留:NAU Economy offline 徽章语义、Active Agents 0/0 计数映射(10/10 三连修后余额)。
5. ★ 受理 API 路径待回查:预演时"CTA→受理 API 200"的路径与今晚实测 /api/v1/submissions 404 不符,复跑时以页面实际调用为准。
6. ○ pricing 价格墙五档缺失($0/$49 vs BP 五档)——候用户三选拍板(A 写死/B 动态/C 维持免费主打)。
7. ○ A1/A2/A3 根域首页"组织操作系统"区块+hero 三层叙事;A4 CTA 全通走查;A6 developers 页 V2。
8. ○ B5 compass 页脚六站互链;B6/B7 zenmind/hr 静默件;DID 章 web 版重渲染(候 flywheel 回执)。
9. ○ app 域 OG=index.html 单页态(SPA 路由分享卡不可用);marketplace 列表空态(legacy 老表)。

## 三、前端美化方案(分级)

**P1(开业门面直接相关,纯静态低风险)**:
- 根域五页接入 tokens.css 公共层(字体栈/间距/语义色,浅色品牌域)——改动面=每页一行 link+局部变量对齐;
- 导航统一:首页页脚+sites.html 补两外壳/pricing 链接;双白皮书 301 收敛(保留新渲染版为正,旧版 301)。

**P2(候输入或小改)**:
- SPA pricing 页按 BP 价格墙(改法候三选拍板);/live 两小项收尾;SPA OG 路由级(候 v5/handoff)。

**P3(开业后)**:
- compass 页脚互链(B5,can 邮协调);zenmind/hr 面美化(候回执)。

## 四、前后端融合优化

- SPA 调用面 121 组在役(R3 收官结论维持);今晚 grep 实证 top 调用=marketplace/control-plane/fde/auth 系,platform/stats 非 SPA 依赖(404 为抽验误用,无洞)。
- 融合优化候项:①根域 admin.html(静态壳)与 app/admin(SPA 路由)双后台归一评估;②列表空态引导(空表给"暂无+入口"而非白板);③登录-钱包双通道打通后 app 门禁白名单与 auth 面联动复验(白窗部署后)。

## 五、执行序建议

1. **10/11 白窗**:鉴权收口 13 文件部署(已排,B′ warning-only)——先于美化(部署面干净);
2. **P1 美化三件**(tokens 根域接入/导航补链/301 收敛)——纯静态,部署即验;
3. A4 CTA 全通走查(含受理 API 路径回查);
4. P2 按 pricing 三选拍板并行。

—— platform · 网站体检 · 2026-10-10 凌晨
