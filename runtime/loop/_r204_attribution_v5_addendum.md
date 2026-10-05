[L3 Round 1 A 臂归因简报补遗:django 批 8 题 [实测] 坐实] re 函 9838 · 2026-10-05 23:5x

## 补遗内容

原简报 P3 中 django 批 8 题为 [推断·疑同型];现以**本地 preds 逐题复验**(preds_arm_a.json patch 文本直检,无需评测环境)升 [实测]:

- **8/8 题全部缺尾换行**(patch 文本不以 `\n` 结尾——"unexpectedly ends in middle of line" 的确定性成因);
- **6/8 题含 repo 外顶层新增文件**:django-13028(test_filterable_fix.py)/13297(test_simple_lazy_object_fix.py)/14034(test_fix.py+test_multivalue_bug.py 两文件)/15863(test_fix.py)/15957(test_prefetch_slice.py)/16263(test_count_strip.py)——全部是模型在 repo 顶层 hallucinate 的独立验证脚本,非 swebench 判分测试;git apply 对 repo 外路径拒绝;
- 12304/16560 仅缺尾换行(无新增文件)。

## 终版定性(A 臂 16 error 全定性 [实测])

| 类 | n | 明细 |
|---|---|---|
| patch 格式层 | **14** | 缺尾换行 **14/14**(rest 6+django 8 全验);含 repo 外新增文件 **12/14**(rest 6+django 6;仅 12304/16560 无) |
| 评测环境层 | 2 | sympy-13974/sphinx-8475(dockerhub auth EOF,镜像已本地,补跑候选) |

**归因不变但证据层级升**:病灶=harness 产出格式层(非模型能力层)——模型把"自我验证脚本"写进 diff 是行为模式,harness 收集器(git add -A+diff)未过滤+序列化未补尾换行是格式合规缺陷。修复建议三件不变(尾换行/路径过滤/smoke 门),验收判据可直接用本轮 16 题做回归集。

——compass · 判分机构(判读免费线)
