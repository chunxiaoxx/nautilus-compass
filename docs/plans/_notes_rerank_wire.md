# Notes · 生产 reranker 接线点(Task 1.1 调研产出 · 2026-06-05)

## 生产 recall 路径(daemon.py)
- `handle_request(req)` @ `daemon.py:610` —— 唯一生产 recall 入口(TCP/MCP 都走它)。
- recall 分支 `daemon.py:667-719`:
  1. `all_entries` 跨 mem_dir union(`:669-675`)。
  2. dense cosine 打分 → `scored` 降序(`:676-682`)。
  3. **可选 BM25+vec RRF fusion**(`COMPASS_USE_BM25_RRF=1`,`:684-697`)→ 得 `top`;否则 `top = scored[:top_k]`(`:699`)。
  4. 构建 `result["recall"]`(`:701-707`)。

## reranker 注入点
**`top` 定好之后(line 699 之后)、构建 `result["recall"]`(line 701)之前。**
这样 reranker 同时覆盖 vec-only 和 RRF-fused 两条路径,且只对最终 top-K 重排(latency 可控)。

注意:reranker 跨编码器对 top-K 重排,要看「完整候选文本」效果最好。BM25 用 `e.get("embed_text","")`,reranker 应同源用 `embed_text`(非仅 `description`)。
若要让 reranker 看更多候选再砍到 top_k,可对 `scored[:RERANK_CANDIDATES]`(如 top-30/50)重排后取 top_k —— 与 benchmark `TOP_K_RETRIEVE=50` 一致。本期先对已得 `top` 重排(最小改动),候选扩展留 1.4 benchmark 验证时按分数决定。

## reranker 接口(现状:无可复用函数)
- `tests/eval_rerank.py` 内联实现,**未抽取**为可复用函数。daemon.py 零 rerank 代码(grep 确认)。
- 核心调用(`eval_rerank.py:60-66,109-113`):
  ```python
  from sentence_transformers import CrossEncoder
  reranker = CrossEncoder(RERANKER_PATH, device=device)   # device autodetect cuda/cpu
  pairs = [(query, doc_text), ...]
  scores = reranker.predict(pairs)                         # 高分 = 更相关
  reranked = sorted(zip(items, scores), key=lambda x: -x[1])
  ```
- 模型路径:`ZMM_RERANKER_MODEL` env,默认 `~/.cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3`。
- device:`ZMM_DEVICE` env,默认 `cuda if torch.cuda.is_available() else cpu`。

## env flag 惯例(沿用)
模块级常量:`_FLAG = os.environ.get("COMPASS_X","0") == "1"`(参 `daemon.py:87` `_BM25_RRF_USE`)。
本期新增:`COMPASS_PROD_RERANK`(默认 "0" = 关,默认行为不变)。

## 降级写法(沿用 BM25 模式 daemon.py:695-697)
reranker 加载/predict 抛异常 → `log(...)` + fallback 退原 `top`(dense/fused 序),不 crash recall。
进程内单例懒加载(参 `get_embedder()` @ `daemon.py:335` 的 eager-singleton 思路,但 reranker 用 lazy 因默认关)。

## 风险
- **模型加载耗时**:bge-reranker-v2-m3 首次加载数十秒(与 embedder 同量级)。懒加载 → 仅开 flag 且首次 recall 时付出。
- **内存**:reranker ~2GB,与 bge-m3 叠加。生产开 flag 前确认 daemon 内存余量(云端曾有页抖动 OOM 史 · session 0603 G15)。
- **latency**:每 recall 多一次 cross-encoder predict(top-K 对)。top_k=5 时极小;若扩候选到 top-30/50 则按 benchmark 67min/500q ≈ 8s/q GPU,CPU 更慢 → 生产候选数需保守。

## TDD 注入策略(Task 1.2+)
为可测,把 reranker 调用抽成 `daemon.py` 内模块级函数 `_rerank_top(query, top, top_k)`,接受可注入的 predict 函数(测试用 fake CrossEncoder 避免加载真模型)。flag 关时直接返回 `top` 原序。
