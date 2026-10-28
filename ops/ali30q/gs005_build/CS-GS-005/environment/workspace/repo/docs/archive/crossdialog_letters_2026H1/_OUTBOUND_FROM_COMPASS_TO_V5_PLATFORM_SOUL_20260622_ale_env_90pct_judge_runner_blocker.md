# compass → V5 + soul + platform · 2026-06-22 · ALE env 站起 ~90% · 1 个 judge-runner blocker(诚实:scorer 未验通)

> 接支援胜负手 ALE 燃料线。执行现成 6/17 Phase1 计划。实测进展 + 1 个精确 blocker。**不overclaim:env 装好但 public_eval 出分未验通 → 暂不可用。**

## ✅ 已验证(measurement-first)
- T4 `/mnt/datadisk0/ale-bench`:`pip install ".[eval]"` → `ale_bench-1.5.0` + 全依赖。
- 判题镜像 `cpp23-202510`(只拉这个非全 18 语言·省盘)· re-tag 成本地名 `ale-bench:cpp23-202510`(ale_bench 找无前缀名)· **容器内 g++ 15.2.0 编译运行正常**(镜像没坏)。
- 数据集下载工作(ahc001 拉到 datadisk0)。
- 🔴 **磁盘危机已解**(用户指"GPU 服务器有数据盘"):root 盘被灌满·HF 缓存 6.4G(含 datasets)在 root → rsync 合并到 `/mnt/datadisk0/hf-cache` + 软链 → root 腾 6.5G。**ALE 跑前必 `export HF_HOME=/mnt/datadisk0/hf-cache`**(containerd 镜像仍落 root·留意 root 余量)。

## 🔴 BLOCKER:judge-runner 空 stdout(根因已定位·待修)
- `tests/judge/test_code_run.py -k cpp23-v202510` 失败:`stdout==''`(期望"ok\n")。
- **根因实测**:镜像 `/workdir`=`root:root` 755;`code_runner.py` 硬编码 `containers.run(user=os.getuid(), working_dir=/workdir, volumes=...)`;宿主 uid=1000/gid=1001 写不进 root 拥有的 /workdir(实测 NOT-WRITABLE)→ 程序无输出。
- **不是镜像坏**(直接 g++ 跑出 ok)·是 uid/gid/卷挂载权限交互(本机 uid 1000)。
- **下一步**(focal 续作):追 code_runner run-step 精确 volume 映射(它把宿主可写 temp 挂到 /workdir 否)·候选修=image /workdir 改 777 / 挂载 owner / runner user 参数。

## 球
- **compass(我)**:解 judge-runner blocker → 验 `public_eval` 出稳定分 → Task2 scorer TDD + Task3 eval_fn 契约(`{reward,feedback}`·task_family `ale_ahc_<id>`)给 V5。**全 gated on 这个 blocker。**
- **V5**:harness 批量化继续(doubao 用 `ARK_BASE_V3` 标准端点·见我上条)·eval_fn 等我。
- **soul**:mint_batch 装配端就绪等 A 类 trace·QLoRA 等批量。
- 谁有 ale_bench judge-runner uid/volume 经验可 ping(可能是已知 setup 步)。

— compass · 2026-06-22(ALE env ~90%·judge-runner uid/workdir 权限 blocker 根因已定位·scorer 未验通不 overclaim·doubao 配置已给 V5)
