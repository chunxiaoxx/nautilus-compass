# 审计流水线(新数据集 → 谈判弹药,7/17 已走通 2 次)

1. **探测**:`curl https://huggingface.co/datasets/<repo>/resolve/main/meta/info.json` 看版本/fps/features;确认有无成败标签列(next.success 类)、夹爪维。
2. **下载**:只拉 `data/**/*.parquet` + `meta/`(低维数据,MB 级;视频不拉);存 `datasets/<name>/`(gitignore)。
3. **审计**:`python scripts/audit_lerobot.py datasets/<name> --name <name> [--gripper-dim -1] [--success-key none] --out docs/audit/<date>-<name>-audit.md`
   - 阈值自动分布校准(warn=p90 复核 / critical=p99 判废 = ICLR2025 口径);
   - 无标签数据集必以"严格口径 0 可结算"为头条(这是发现不是失败)。
4. **Confound-check(铁律)**:结果反直觉(0%/100%)先证伪裁判自己——查单位口径(rad vs px)、标签语义(success 判据是什么)、阈值来源,再下结论。先例:pusht 弧度套像素 90% 误报。
5. **沉淀三处**:audit 报告(可复跑)→ 页面审计表(内部+外发同步)→ nautilus-core research 文档追加一节。
6. **提交**:代码与报告同 commit;数据集不入库。

候选队列:DROID 子集 · AgiBot World alpha 子集(体积大,选低维切片)· 客户 spec 到手后的同构公开集(谈判前定向审计)。
