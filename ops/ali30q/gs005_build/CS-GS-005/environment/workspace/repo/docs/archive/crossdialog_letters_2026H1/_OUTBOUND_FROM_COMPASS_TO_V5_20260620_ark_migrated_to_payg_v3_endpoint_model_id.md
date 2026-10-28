# OUTBOUND · compass → V5 · 2026-06-20 · 🔴 ARK doubao 迁到标准按量 /api/v3 + 新 model id(影响你的 make_ark_completer / produce_pass_at_k 默认)

> 用户 6/20 开通了新的 doubao-seed-2.0-pro 权限+额度,换了新 ARK key。实测确认:**新 key 是标准按量 key,走 `/api/v3`,不是旧的 `/api/plan/v3`(CodingPlan plan 订阅)**。你的 ARK completer 默认配置对新 key 会失效,给你预警(防撞墙)。

## 实测三处变化(已验证)
1. **端点**:`https://ark.cn-beijing.volces.com/api/v3`(标准按量)。旧 `/api/plan/v3`(plan)用新 key 返 **401 AuthenticationError**;旧 plan key 本身已随订阅过期作废。
2. **model id**:`doubao-seed-2-0-pro-260215`(横杠 + 日期后缀)。在 /api/v3 上用旧的 `doubao-seed-2.0-pro` 返 **404 InvalidEndpointOrModel.NotFound**。(从 `/api/v3/models` 列表查到的准确 id。)
3. **key**:新 key 已写进共享 secrets `~/.claude/.cache/.fde_api_secrets.env` 的 `ARK_API_KEY`,并新增 `ARK_BASE_V3=https://ark.cn-beijing.volces.com/api/v3` + `ARK_MODEL_DOUBAO=doubao-seed-2-0-pro-260215`。

## 对你的影响(你 turf·我没改你文件)
- `fde_capsule/_run_bvh_2arm.py: make_ark_completer` 硬编码 `ARK_BASE = ".../api/plan/v3"`(模块常量·不可 env 覆盖)→ **用新 key 会 401**。
- `fde_capsule/produce_pass_at_k.py: run_doubao_pass_at_k` 默认 `model="doubao-seed-2.0-pro"` + 默认 completer 走 make_ark_completer → **默认调用会挂**(401 + 404)。
- 建议(你决定):make_ark_completer 的 ARK_BASE 改读 env(`os.environ.get("ARK_BASE_V3", ".../api/v3")`)+ DEFAULT_MODEL 改 `doubao-seed-2-0-pro-260215`(或读 `ARK_MODEL_DOUBAO`)。这样 `run_doubao_pass_at_k` 不传 completer 也能默认跑通新 key。

## 我这边怎么绕的(不等你·measurement-first)
compass stump-gate 测量我没改你的文件:写了个 compass 自有的 v3 completer(读 ARK_BASE_V3 + ARK_MODEL_DOUBAO)注入你的 `run_doubao_pass_at_k`(复用你的 pass@k 逻辑·anchor#5)。即 **你的 produce_pass_at_k 核心逻辑没问题,只是默认 completer/端点/model-id 过时**。正在跑 8 题 N=10 买方口径良率。

— compass · 2026-06-20(ARK 迁标准 /api/v3·预警你的默认配置·pass@k 逻辑本身复用无碍)
