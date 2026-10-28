# 网站资产考古清单(2026-10-08 13:4x · 用户纠偏"半年前已建过,先考古再动手")

> 触发:平台 index_v2 两轮装订(v2.0/v2.1)未考古存量,部分=重复造轮子。本清单=现役网站资产全景(9/3"一亩三分地"教训的网站版:平台对自家网站资产无载体认知)。

## 一、云侧现役资产全景(/var/www/nautilus/current/,外网 nautilus.social)

| 资产 | 内容 | 性质 | 正本/owner |
|---|---|---|---|
| **index.html**(11.6KB) | 「数据飞轮管道平台·动态验证台 V0」活 API 页:live-pool 轨迹池+逐单五段验证+四验门+判读产能诚实记录+**平台产品线四卡+基础设施服务读数区**(v5 K3 岗 10/8 交付 R147/m2) | **活页(API 驱动)** | phase3/frontend/? + v5 K3 岗迭代中 |
| unipat.html / intake.html / criteria/ / criteria.html | 判分线五页(受理/判据披露/样例) | 静+半活 | **phase3/frontend/**(git 正本,786bbd944 治一次性网页病,统一设计语言) |
| pipeline.html | 数据管道主站体系页(重构过,三向互链) | 半活(/api 同域) | phase3/frontend/ |
| **registry.html** | Registry 实态·判例与语料计数器(设计语言同主站) | 活页 | **nautilus-compass@runtime/site/**(compass) |
| **status.html** | 判读卡状态查询(R326 上线/R336 E2E 真数据贯通:提交→查询→结果全链,API systemd+nginx 代理) | 活页 | **nautilus-compass@runtime/site/**(compass) |
| products/ + api/ + assets/ + corpus_stats.json | 产品目录/接口/静态资产(status.html 的 API 代理=compass R336 systemd+nginx) | 混合 | api 代理=compass 配置,余未考古 |
| org/(镜像) | 两外壳 BYZ 案卷卷宗页 | 静态 | 渲染器(flywheel) |
| leaderboard.html | L3 详版(平台 10/8 装订) | 半活 | nautilus-compass@runtime/l3_board |
| index.html.bak-20260923~20261008 | **六代门户迭代史**(9/23 门户版→10/6-08 四卡→m1/m2/R147) | 备份链 | — |

## 二、半年建设史要点(git 考古)

- **phase3/frontend/=git 正本体系**:786bbd944"治一次性网页病"(统一浅色/组件/导航设计语言)、875cea7e7 门面导航三互链、b5da75fac/c49d3e4e1 判分线页面收归正本——**"一个声音"半年前就在做**
- 现役 index.html 演进:动态验证台 V0(活 API)→四卡门户(10/7 平台 patch)→读数区+详情页(v5 K3 岗 10/8)——**多框在正确地增量迭代同一页,无独立重写**
- 10/7 动态数据管道平台 V0 SPA、机制产出账专节——活数据路线早已确立

## 三、轮子判定与修正

| 我做的 | 判定 | 修正 |
|---|---|---|
| index_v2 v2.0(compass 底稿零 CSS 重写) | **轮子**(与现役页/正本体系并立) | 废弃归档 |
| index_v2 v2.1(三层叙事重写) | 叙事方向对(用户纠偏采纳),**载体错**(另起炉灶) | 叙事保留,**载体改为现役 index.html 增量装订** |
| 直接装订 leaderboard | 可(该页无在岗 owner 冲突) | 维持 |

**修正行动**:
1. index_v2 两版归档(候选资格撤销),本文件=考古正本
2. 三层叙事的**增量件**=「组织操作系统」区块(现役页缺这一层)——**候 v5 K3 岗协调后**由装订员 patch 进现役页(其在岗 owner,R147/m2 今天还在交付,禁平台直接动)
3. 装订员 SOP 增补前置步:**装订前必考古**(本清单+git log+云目录),存量有=增量/接线,存量无=才新建
4. 防双修函 v5:确认现役 index.html 在岗 owner 与平台增量协同位

—— platform · 2026-10-08(教训:接线收敛禁新建,第三次踩,考古前置进 SOP)
