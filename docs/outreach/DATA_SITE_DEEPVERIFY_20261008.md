# data.nautilus.social headless 深验报告(2026-10-08 · compass 出 · 10/11 终检前置件)

> 验法:Chrome headless(new) 渲染 + --virtual-time-budget=12-15s,渲染后 DOM 内容级检查(非 curl 壳验)。工具零依赖(本机 Chrome CLI),配方可复跑。

## 一、五路由渲染实证

| 路由 | 渲染字节 | 可读内容 | 判 |
|---|---|---|---|
| `/` 主页 | 35,093 | 完整叙事:具身数据独立质检定位/84 路实测读数(PASS 67·WARN 17·FAIL 0)/黑帧 0/84/人脸 15/80(v0.2)/判据 v0.1→v0.2 迭代实录(76 路误检→人工定谳不可作数→双标定→真问题)/81pp 同预算效用差/47 条正式批次/6/6 独立复现/六步管道/sha 摘要存证 0b85b7ca | ✅ |
| `/pricing` | 30,554 | 含定价内容(渲染非壳) | ✅ |
| `/console/login` | 4,374 | 真登录表单(input/password) | ✅ |
| `#/doc/l1-sku` | 6,095 | 1,062 可读字符 | ✅ |
| `#/doc/l2-case` | 6,743 | 1,728 可读字符 | ✅ |

## 二、链接层

23 链接全枚举:mailto×4(联系通道统一 chunxiaoxx@gmail.com)/页内锚×6(#sample/#how/#trust/#pricing)/console 路由×9(g/demo×4·g/verify×3·login·g/metrics·g/roadmap)/根×1。
**零空 href、零外链**——无出站死链风险;锚点与 hash 文档路由均实测渲染。

## 三、内容质量判读

- 主页是**数据实证页**不是宣传页:每句关键声明都带读数或 sha(84 路批次/27 帧抽检扩样/0b85b7ca)。
- 亮点:检测器迭代实录段(误检→定谳→双标定→真问题)与我们判分证据三层纪律同构——"体系会纠自己的错,也会抓真问题"。
- 定位句"买训练数据之前,先验货"与 SITE_REVIEW 主站改版方向一致(产品先行)。

## 四、边界与移交

- `/console/g/*` 内页(demo/verify/metrics/roadmap)需登录,**未验**(登录凭据未开),记入 10/11 终检清单由 flywheel 补验或开测试账号。
- SITE_REVIEW 缺陷三"data 站渲染后不可验"**关闭**:本报告即渲染后实证,方法沉淀为可复跑配方(chrome --headless=new --dump-dom --virtual-time-budget=15000)。

## 五、复跑配方

```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu \
  --dump-dom --virtual-time-budget=15000 "https://data.nautilus.social/" > dom.html
```

—— compass · DATA-SITE-DEEPVERIFY · 2026-10-08 · 渲染件存 runtime/loop/_data_*.html
