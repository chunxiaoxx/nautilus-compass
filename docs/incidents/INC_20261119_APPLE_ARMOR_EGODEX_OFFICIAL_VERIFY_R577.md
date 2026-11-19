# INC_20261119 · Apple ARMOR / EgoDex 官方页一手核验 + R576「同名碰撞」结论被证伪（勘误）

- 轮次：LOOP R577（2026-11-19 EST）
- 框：compass（论文/引用/投稿口径归属本框，见 ORG_BRIEF）
- 上游入站：飞轮→Compass 两件（工作区未跟踪文件，不经平台信箱）
  - `_INBOUND_FROM_FLYWHEEL_20261119_apple_robot_paper_verification.md`
  - `_INBOUND_FROM_FLYWHEEL_20261119_academic_research_handoff.md`
- 性质：**本框自报结论的勘误**（推翻本框 R576 的结论，不是推翻他人结论）

---

## 〇、一句话

R576 记「ARMOR 与 arXiv 2412.00396 同名碰撞、该 arXiv **不是** Apple 的 ARMOR、引用不可直引」——**该结论不成立**。经 Apple 官方 detail 页与 arXiv API 逐字比对，二者是**同一篇论文**（标题、4 位作者、摘要全部一致）。R576 的误读来自「把 Apple 列表页相邻条目的作者串当成 ARMOR 的作者」。

---

## 一、[实测] 证据一手来源

| 用途 | URL | 取用方式 |
|---|---|---|
| ARMOR 官方 detail 页 | `https://machinelearning.apple.com/research/armor-egocentric` | `curl -L` 抓 HTML → 去标签取正文（HTTP 200，24,734 B） |
| EgoDex 官方 detail 页 | `https://machinelearning.apple.com/research/egodex-learning-dexterous-manipulation` | 同上（HTTP 200，30,542 B） |
| arXiv 元数据 | `https://export.arxiv.org/api/query?id_list=2412.00396` | 官方 Atom API（`http://export.arxiv.org` 端点 **301**，必须 https） |

### 1.1 ARMOR（官方 detail 页原文要点）

- 标题：**ARMOR: Egocentric Perception for Humanoid Robot Collision Avoidance and Motion Planning**
- 研究领域：Methods and Algorithms；published **February 2025**；content type: paper
- Authors（官方页原文）：**Daehwa Kim, Mario Srouji, Chen Chen, Jian Zhang**
- 摘要数字（官方页逐条）：
  - 训练用 **≈86 小时 AMASS** 人类真实动作，transformer 模仿学习策略做仿真动态碰撞规避
  - vs「多组稠密头戴 + 外挂深度相机」基线：**碰撞 −63.7%**、**成功率 +78.7%**
  - vs 采样式运动规划专家 **cuRobo**：**碰撞 −31.6%**、**成功率 +16.9%**、**计算延迟 −26×**
  - 真机：**部署到 Fourier Intelligence 的 GR1 人形机器人**
  - 官方原句：「We are going to update the link to the source code, HW description, and 3D CAD files in the arXiv version of this text.」⇒ **代码 / 硬件描述 / 3D CAD 尚未开放**（官方页面自述，非我方推断）

### 1.2 arXiv:2412.00396（官方 Atom API entry 级）

- title：`ARMOR: Egocentric Perception for Humanoid Robot Collision Avoidance and Motion Planning`
- authors：`Daehwa Kim`, `Mario Srouji`, `Chen Chen`, `Jian Zhang`
- published / updated：均为 **2024-11-30T08:39:23Z**（v1，无 journal_ref / DOI / comment）
- 摘要：与 Apple 官方页**逐字同源**（86h AMASS / 63.7% / 78.7% / 31.6% / 16.9% / 26× / Fourier GR1）

### 1.3 EgoDex（官方 detail 页原文要点）

- 标题：**EgoDex: Learning Dexterous Manipulation from Large-Scale Egocentric Video**
- published **July 2025**；conference **ICLR**；research area: Computer Vision / Data Science and Annotation
- Authors（官方页原文）：**Ryan Hoque\*, Peide Huang\*, David J. Yoon\*, Mouli Sivapurapu, Jian Zhang**（\* equal contributors）
- 数字：**829 小时**第一视角视频 + 同步采集 3D 手/手指追踪（多标定相机 + 端侧 SLAM，逐关节位姿）、**194 个桌面操作任务**、用 **Apple Vision Pro** 采集
- 训练对象：手部轨迹预测的模仿学习策略（human hand trajectory prediction）
- 官方自述：「the largest and most diverse dataset of dexterous human manipulation to date」（作者自报）

---

## 二、[实测] 结论表（与飞轮交接件逐条对齐）

| 交接件自报项 | 官方页复核 | 判定 |
|---|---|---|
| ARMOR ≈86h AMASS | 官方页同 | ✅ 一致 |
| ARMOR 仿真碰撞规避 + Fourier GR1 真机部署 | 官方页明确写出 | ✅ 一致 |
| ARMOR「完整任务数/seed/碰撞定义/置信区间/真机对照/代码仍需回读」 | 官方页摘要**仍无**任务数/seed/碰撞定义/置信区间；**真机有部署但无碰撞/成功数字**；代码官方明写「将更新」⇒ 仍缺 | ✅ 缺口坐实（其中"代码仍缺"由推断升级为**官方页面实证**） |
| EgoDex 829h / 194 桌面任务 | 官方页同 | ✅ 一致（构成独立确认，非循环引用） |
| EgoDex「主要是人类手部轨迹预测」 | 官方页：train & evaluate IL policies for **hand trajectory prediction** | ✅ 一致 |

### 2.1 边界（Compass 侧口径不变）

- EgoDex = **压缩/数据端**证据（人类 ego → 3D 手/动作 latent），**不可**写成机器人迁移或真机泛化。
- ARMOR = **感知/仿真策略端**证据（碰撞规避 + 规划），**不可**写成 RSI、开放世界泛化或通用泛化。
- HALO（arXiv:2611.06908）/ AMP1（arXiv:2611.09892）编号级核验沿用 R576 结论（本轮未重核，见 §四 边界）。

---

## 三、[实测] R576 结论勘误（根因分析）

**R576 原记载**（`runtime/loop/queue.md` R724 与记忆卡 `inbound-cross-frame-via-workdir-20261119.md`）：

> ⚠️「ARMOR / EgoDex（Apple ML 官方页）」与 arXiv `2412.00396`「ARMOR: Egocentric Perception for Humanoid Robot Collision Avoidance and Motion Planning」（2024 旧文）**同名碰撞**，引用须落到 Apple ML Research 官方页、不可引该 arXiv 条目。

**勘误**：不成立。二者为同一篇（标题 + 4 作者 + 摘要逐条一致）。**正确口径 = 可直接引 arXiv:2412.00396，并用 Apple 官方页互证**（arXiv 给正文/版本，Apple 页给 published date 与"代码待更新"声明）。

**根因 = 读法缺陷（可复用教训）**：Apple 研究列表页（`/research/?q=...`）是**一个 JSON 数组**，每个条目形如
`{...,"authorsOrdered":"<上一篇作者>","slug":"<本篇 slug>","title":"<本篇标题>",...}`。
即：**作者串出现在 slug/title 之前**，属于**上一条目**。R576 在列表页 HTML 中按「标题 → 最近的 authorsOrdered」就近取值，跨条目取到了相邻论文的作者：

| 被误取的作者串 | 实际归属 | 误记给了 |
|---|---|---|
| `Siqi Shen, Yu Liu, Daniel Biggs, Omar Hafez, Jiandong Yu, Wentao Zhang, Bin Cui, Jiulong Shan`（2025-02-14 论文） | 另一篇 Apple 论文 | ARMOR（R576） |
| `Dan Busbridge, Amitis Shidani, Floris Weers, Jason Ramapuram, Etai Littwin, Russ Webb`（2025-07-01，ICML） | 另一条 EgoDex 相邻条目 | EgoDex（同一陷阱） |

⇒ **纪律（新增）**：官方站点的**列表页只用于定位，不用于取事实**；作者/日期/数字一律落到 **detail 页**再读。本轮 ARMOR 与 EgoDex 的字段**全部取自 detail 页**，未使用列表页字段。

---

## 四、边界与未做项

- [不可验] ARMOR 的**任务数、seed、碰撞定义、置信区间、真机 GR1 上的碰撞/成功数字**：官方摘要未给；本轮未取 arXiv 正文 PDF（仅取 API 元数据）⇒ 结论仅覆盖「官方页/摘要层」这一层。
- [未做] 未核 arXiv 正文全文（PDF）、未核 EgoDex 数据集版本号与许可、未核「本地未找到用户本轮上传的具体附件」这一交接方自述前提（仍为自述）。
- [未做] 未回函飞轮（按「不自动 ack/发送」纪律）、未改写飞轮任何文件。
- HALO / AMP1 的编号级结论沿用 R576（本轮未重核，非本轮增量）。

---

## 五、证据坐标

- 本档：`docs/incidents/INC_20261119_APPLE_ARMOR_EGODEX_OFFICIAL_VERIFY_R577.md`
- 留痕：`runtime/loop/rounds.log`（R577）、`runtime/loop/queue.md`（R724 勘误 + R725 主件）、`COLLAB_BOARD.md`
- 记忆卡：`apple-armor-egodex-verify-r577-20261119.md`（新建）、`inbound-cross-frame-via-workdir-20261119.md`（已勘误）
- 官方回函：平台信箱 id **116359**，trace `oge-status-demand-compass-2026-11-20-done`（需求函 id 115584 已 ack）
