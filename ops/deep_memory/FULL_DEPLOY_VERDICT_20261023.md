# 深度记忆库 · 全框部署总卡(2026-10-23)

## 部署结果 [实测]

| 库 | 块数 | 库容 |
|---|---|---|
| nautilus-core | 23,040 | 96MB |
| arm-worker-prime | 24,820 | ~100MB |
| home(Happy Mac 会话) | 20,330 | ~85MB |
| nautilus-v5 | 18,272 | 75MB |
| venture_daily_report | 8,867 | 37MB |
| nautilusflywheel | 12,456 | 54MB |
| venture-daily-report | 6,560 | ~28MB |
| quantum-buddha-project | 6,552 | ~27MB |
| compass | 3,711 | 16MB |
| arm-worker-v7 | 505 | 4MB |
| caishen-ai | 153 | ~1MB |
| **合计(12 库)** | **~138,600** | **~676MB** |

- 嵌入:全部走 Mac mini 本机 BGE(8400),**总耗时约 50 分钟,零 GPU 成本**
- 失败:**0 块**(全程零失败,含一次断点续跑实战)

## 已知冗余(不阻塞使用,留清理待办)
- Happy 双目录(home/C--Users-chunx)互为镜像 → ~2 万块重复入库
- venture 双变体(连字符/下划线)部分重叠 → ~5 千块
- 影响:检索时同块可能出两次(top-k 容忍);清理=合并两库并 md5 去重(值守轮可做)

## 途中事故记录
1. core 嵌入进程一次静默死亡(无 traceback,疑 macOS 后台回收)→ 管线重入设计断点续跑,零重复补完 ✅
2. run_all.sh cd 层级 bug + argparse 把 `-U` 开头目录名当 flag → 修后冒烟再跑 ✅
3. NAS rsync 老版本不支持 --info=progress2 → 降参数重拉 ✅

## 8 个月家底最终账
- 原始:9,550+2,042(NAS 补 182 条差量)会话 / 5.6GB → **语义可检索:~13.9 万块向量**
- 之前:现役检索只覆盖 180 条(千分之一)→ 现在:全部历史深度可查
- NAS 增量 182 条已合并入 projects 归档,待下一批嵌入

## 下一步(值守轮消化)
1. deep_recall 接入 daemon(考古协议第三层)
2. Happy/venture 双库去重
3. NAS 增量 182 条嵌入
4. 每周保鲜:新会话自动入历史库
