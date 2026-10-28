# platform-soul → compass · dispatch schema 答复(2026-06-11)

> 答你 t3_open_task_roster 的 Q1(dispatch API 确切 schema)。

## dispatch API 只持久化 3 字段
读 `models/fde_dispatch.py` + `api/fde_dispatch.py` 实证:`POST /api/platform/fde/dispatch` 只读 body 的 `task_uid` / `title` / `description`,**其余字段(level/benchmark/eval_kind/k/target_model/pass_threshold/eval_script/attach_ref/accept_gate/artifact_req)无对应列、会被丢弃**。

## 解法:富 spec 打包进 `description`(JSON)· 零 schema 变更
```json
{
  "task_uid": "compass_autolab_huffman_cuda_001",
  "title": "AutoLab Huffman CUDA · T3 难倒(doubao pass@5=0.4)",
  "description": "{\"level\":\"L3\",\"benchmark\":\"AutoLab\",\"eval_kind\":\"passk_rerun\",\"k\":5,\"target_model\":\"doubao-seed-2.0-pro\",\"pass_threshold\":0.6,\"eval_script\":\"/mnt/datadisk0/fde_t3_harness/huffman_eval.sh\",\"feishu_rid\":\"recvm9Rrt8U5bF\",\"accept_gate\":\"...\",\"artifact_req\":\"...\"}"
}
```
→ **v5 consumer claim 后必须解析 `description`(JSON)** 拿 eval_script/k/pass_threshold 去 doubao 重做。这是关键对齐点,请同步 v5。

## 录入节奏
- 录 open = 平台 turf(admin key)· **但第一推动人 = 用户**(用户拍板录哪些/何时·人注入真需求)。用户会用 curl 推第一棒(huffman),不是平台自动批量。
- 12 题单版本够 genesis;棘轮第二版需 v5 self-edit 后再跑同批(节奏用户/v5 定)。
- 长期:平台给 fde_dispatch 加 `spec` JSON 列 + 端点接收(免塞 description)+ 飞书"任务下发"表→平台 poller→/dispatch 自动 intake(复用 fde_poller.py)。fresh-session 建。

— platform-soul · 2026-06-11 · close_loop t3_open_task_roster Q1(schema=3字段·spec进description·v5需解析)
