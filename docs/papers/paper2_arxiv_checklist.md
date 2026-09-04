# paper2 · arXiv 提交准备清单(#41 · 备而不发,发布等用户)

> 状态 9/4:全稿 9 页编译收敛(0 错 0 undefined citation),文献 12 条全验证。
> 本清单是提交前最后一公里;提交动作本身 = 对外发布,等用户明示。

## 已完成的一致性检查

- [x] 摘要数字与正文一致:14.2% / 71 题 / 5.4pt / 32.8pt 三处对齐(9/4 核)
- [x] 摘要 "six-item" vs 正文 P1-P5 矛盾 → 已改 five-item(9/4 commit)
- [x] 编译两遍收敛 0 错;citation 0 undefined
- [x] 文献 12 条逐条 WebSearch 验证(纠 3 处:evalbiasbench/selfenhancement/crescent)
- [x] 诚实边界落稿:三口径并报 / 451 题上游 attribution(xiaowu0162)/ 服务商不指名
      (写 intermittent gateway failures)/ ssp 小样本二项噪声带

## 提交前待办(机械项)

- [x] 标题去 "(Draft v2)" 尾巴(9/4,重编译两遍 0 错 0 undefined,PDF 231KB)
- [ ] tex 源码打包:单文件无 includegraphics(纯文本+表格,无图)→ 打包即 tex+bbl;
      arXiv 编译要求 bibliography 内联或附 .bbl(用 `bibtex` 生成后把 bbl 内容
      粘到 tex 尾部 thebibliography——现稿已是 thebibliography 手写,无需 bbl ✓)
- [ ] 元数据:
  - 主分类 **cs.CL**(Computation and Language,评测/agent 文献主阵地)
  - 副分类 cs.LG(AI 工程可靠性角度);可选第三 cs.SE
  - license:默认(arXiv 非独占)或 CC BY 4.0(利于传播;用户拍)
- [ ] PDF 与 tex 编译产物一致性(提交时 arXiv 重编译,以 tex 为准)

## 待用户拍板(3 点)→ 9/4 已拍板

1. **署名**:✅ 用户拍板(9/4)——2026 年 4 月已发过 arXiv,**有账号**,署名等元数据
   与 4 月那篇一致。待用户提供 4 月论文的 arXiv ID/署名名单以照抄(或提交时按账号
   档案署名)。
2. **license**:✅ 与 4 月提交一致(默认 arXiv 非独占;若前次用了 CC BY 4.0 则同)。
3. **提交时机**:材料定稿后即可提交(9/12 营销帖之前,帖子引用 arXiv 链接);提交需
   登录账号,由用户操作或提供方式。

## 提交步骤(拍板后 ~30min)

1. tex 清 Draft 尾巴 → 重编译终版 PDF
2. arXiv start / Submit:填元数据 + 上传 tex 单文件 + 同意条款
3. arXiv 宣告邮件确认 → 拿到 arXiv:XXXX.XXXXX 后回填 README/营销帖
