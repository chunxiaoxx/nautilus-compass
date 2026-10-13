---
name: orgfuel-ORGQ-7f75afc9099e7e52-747135df70
description: "轮次记录 R451 · 2026-10-10 凌晨五(用户拷问修正+rerank A100 服务端上线✅[实测 10ms"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-7f75afc9099e7e52
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R451 · 2026-10-10 凌晨五(用户拷问修正+rerank A100 服务端上线✅[实测 10ms]——pkill 自匹配第 6 次+SSH 重试通道)
### R451 · 2026-10-10 凌晨五(用户拷问修正+rerank A100 服务端上线✅[实测 10ms]——pkill 自匹配第 6 次+SSH 重试通道)
- **用户四问修正**:①"为何等 10/18"——承认排期错误(把"开业周不动对外服务"偷换成"内部增强也推迟",而 rerank 是 env 开关 opt-in 对开业零风险),当场落地不等;②NACRE/assay/compass/基准评测四线进展展开陈述(v1 在役 88.51%/assay 3.3.0+验签门/Round1 榜单/E1-TUNE 方法论)。
- **主件=路径 a 服务端落地✅[实测]**:A100 rerank 服务(a100_rerank_svc.py v2,裸 transformers 零新依赖,9879 端口,token 鉴权)——**GPU 实测 10ms/查询**(3 docs;对照本机 CPU 3.44s=344 倍),排序语义正确,uptime 稳定。rerank 激活四前提的延迟前提就此补齐。
- **排障两课**:①`pkill -f` 自匹配**第 6 次**实锤——bash -c 命令串后半段明文目标名被正则命中,宿主自杀新进程从未启动(log 旧错假象);修法=pkill 与启动分两次 run+cmdline 避明文;②A100 SSH banner 间歇断连频发→a100_exec.py 加 3 次指数退避重试(通道治本)。
- **daemon 接入候下件**:本机 recall→A100 rerank 需稳定 SSH 隧道(autossh),E1 判据 0.8333 为接
