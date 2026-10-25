# 周一资格战第二验汇总（2026-10-25）

判据正本：`PREREG_ALI_FACTORY_SECOND_VERIFY_20261025.md`  
对象：CS-001 / CS-003 / CS-004 / CS-008  
方法：独立只读环境逐题逐门核验；未修改题目文件；缺件不降门。

证据冻结：`[实测]` `ALI_FACTORY_SECOND_VERIFY_MANIFEST_20261025.json`，SHA-256 `467ecb5d8e43271eaa7180153635c1bd542a3819e61dc56e418a02a46aefdf65`。manifest 记录判据/13门正本哈希、四题完整文件清单与逐文件 SHA-256、Git HEAD；Git status 以 porcelain v1 原始字节的 base64、字节数和独立 SHA-256 保真存储；并记录统一算法和排除规则。本报告裁决仅针对该 manifest。

## 一、总裁决

| 题 | PASS | FAIL | PENDING | 第二验裁决与证据层 |
|---|---:|---:|---:|---|
| CS-001 | 0 | 6 | 7 | FAIL·不可封包 `[实测]` |
| CS-003 | 0 | 5 | 8 | FAIL·不可封包 `[实测]` |
| CS-004 | 0 | 5 | 8 | FAIL·不可封包 `[实测]` |
| CS-008 | 0 | 6 | 7 | FAIL·不可封包 `[实测]` |

结论：`[实测]` 四题均存在已确认硬门 FAIL，同时有 PENDING 门；双验制度下均不得签“可封包”。

## 二、区分度复算

正式第二验结论：`[不可验]` 四题 G1–G6 均为 PENDING。`[实测]` 当前 manifest 中没有明确标记为 S3 的五模型×4轮材料、目标题带、组聚合公式及 G 门矩阵；不得把旧矩阵或 `_s5` 诊断读数升级为资格实测。

| 题 | 正式裁决 | 证据层与原因 |
|---|---|---|
| CS-001 | PENDING | `[不可验]` 无明确 S3 五模型×4轮、题带及聚合公式 |
| CS-003 | PENDING | `[不可验]` 无正式 S3 完整材料及聚合公式 |
| CS-004 | PENDING | `[不可验]` 无正式 S3 完整材料及聚合公式 |
| CS-008 | PENDING | `[不可验]` 无正式 S3 完整材料及聚合公式 |

upgrade_path：冻结明确标记 S3 的20轮逐轮结果、异常状态、25%/50%目标带、国内/SOTA聚合公式及G2/G4/G5矩阵，再由新鲜会话复算。

## 三、provenance 补审

- `[实测]` CS-003：`evidence/provenance_statement.md` 缺失 → FAIL。
- `[实测]` CS-008：`evidence/provenance_statement.md` 缺失 → FAIL。

`[实测]` 零散 LICENSE/vendor 资料不能满足预注册要求的来源、许可证、脱敏、相似度自查、已知限制五项声明。

## 四、共性红灯

1. `[不可验]` G1–G6 正式资格材料缺失：没有明确 S3 五模型×4轮、题带、聚合公式和 G 门矩阵。
2. `[实测]` 私有标签未迁甲方体系：task.toml 仍见 trap_type/“改一查十”。
3. `[实测]` JEV 不完整：G门矩阵、verify、最新 matrix_report 多处缺失或过期。
4. `[实测]` 泄题风险：task.toml/instruction 可见路径含修法、机制或扣分锚点。
5. `[实测]` 嵌仓门失败：CS-001/003/004/008 的统一源文件计数均低于1600。
6. `[不可验]` S3正式题带与组聚合声明缺失，不能用临时诊断数字签资格门。

`[实测]` 源文件统一计数口径：递归扫描 `environment/workspace/repo`，普通文件中后缀（转小写后）属于 `.py/.pyx/.pxd/.c/.h/.cc/.cpp/.cxx/.hpp/.f/.f90/.rs/.go/.java/.js/.ts/.tsx/.sh`；不排除 vendor；`_s5/_judge/cache` 不在扫描根内。可执行复算命令：`python3 -c 'from pathlib import Path; r=Path("<repo>"); ex={".py",".pyx",".pxd",".c",".h",".cc",".cpp",".cxx",".hpp",".f",".f90",".rs",".go",".java",".js",".ts",".tsx",".sh"}; print(sum(1 for p in r.rglob("*") if p.is_file() and p.suffix.lower() in ex))'`。

## 五、逐题证据摘要

`[不可验]` G1–G6 均缺正式 S3 证据，统一 PENDING；`[不可验]` G9 缺批次题型台账，统一 PENDING。独立可签的 `[实测]` FAIL 如下：

- `[实测]` CS-001：G7 领域错位、G8 私有标签、G10 Harbor入口不可复现（`tests/test.sh` 大小写路径错误）、G11 JEV缺失、G12修法暗示、G13源文件1161（<1600）。
- `[实测]` CS-003：G8 私有标签、G10交付包不完整、G11 JEV缺失、G12修法暗示、G13源文件1160（<1600）；provenance专项FAIL。
- `[实测]` CS-004：G8 私有标签、G10证据包缺失、G11 JEV缺失、G12修法暗示、G13源文件4（<1600）。
- `[实测]` CS-008：G7 领域/生态错位（OCR题但 vendor SQLAlchemy 且不进入执行路径）、G8 私有标签、G10入口不可复现（无参数 pip install + 大小写路径错误）、G11 JEV缺失、G12修法暗示、G13源文件696（<1600）；provenance专项FAIL。

`[实测]` 旧四个裸摘要因缺少 manifest、排除规则与统一算法，已撤销，不再作为证据。当前唯一冻结坐标为本报告开头所列 manifest 及其 SHA-256；upgrade_path：题目实物变化后生成新 manifest 并重新独立复算，不覆盖本次证据。

## 六、升级路径

- `[不可验]` 正式判分门：补齐明确标记 S3 的五模型×4轮冻结结果、25%/50%题带、组聚合公式及G2/G4/G5矩阵，再独立复算。
- `[实测]` provenance：生产者补 CS-003/008 五项声明，compass 再独立补审。
- `[实测]` 标签与泄题：task.toml 迁甲方领域/标签体系，并从可见题面删除修法暗示。
- `[实测]` 交付：补 JEV/G门/verify/打包证据；嵌仓不足题重造而非豁免。
- `[不可验]` 双验对拍：v5 第一验成品到达后逐项对拍；任何不一致继续标红，不自行调和。
