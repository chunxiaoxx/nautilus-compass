---
name: orgfuel-ORGH-9f5b3019216eb529-bee302aa7d
description: "commit 8adeedc89efe 2026-07-17 feat(bmb): 参数化批产 + 第2模板(序列/BL"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9f5b3019216eb529
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 8adeedc89efe 2026-07-17
feat(bmb): 参数化批产 + 第2模板(序列/BLAST)+ 本地 ClinVar 镜像(消限速)
- build_problem.py 参数化(--answer-gene 自动挑 Pathogenic missense + 排除同基因)→ VCF 模板可批产
- 新增 #2 bmb_vendor_000002(ATP7B/Wilson disease):0 REJECT · 盲解唯一=1 · 36 工具
- 第2模板 build/solve_seq_problem.py(序列→基因/病 · 远程 BLAST,对齐买方 qes1):
  #3 bmb_vendor_000003(HEXA/Tay-Sachs)· 0 REJECT · 盲解 9/10 BLAST 干净(HEXA 唯一溶酶体酶),
  第10条遇瞬时 SSL 抖动 → solve 已加重试,clean 10/10 复跑中
- 本地 ClinVar 镜像(Windows 原生 · 零 GPU/WSL):build_local_clinvar.py 把 clinvar.vcf.gz
  建成 SQLite(420万条/413MB);local_clinvar.py 查询;qc_vcf_local.py 批量 QC
  实测:本地 0.20ms/查 vs 远程 2715ms/查 = ~13583× 提速,结果 5/5 一致;#1/#2 本地 QC 各 3ms 唯一=1
- 建题期泄露断言(镜像验证器)防通用词(disease)泄露;_localdb 大文件 gitignore(可复现)
