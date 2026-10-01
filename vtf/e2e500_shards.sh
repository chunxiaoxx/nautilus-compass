#!/bin/bash
# e2e 500 全量 4 分片(context 修复版配置,同 e2e_ctx.sh env)· cloud 上跑
cd /home/ubuntu/nautilus-compass
git pull -q --ff-only
export $(grep -E "^(ARK_API_KEY|ARK_BASE_URL)=" ~/.claude/.cache/.fde_api_secrets.env | tr -d "\r" | xargs)

run_shard () {
  local S=$1 E=$2
  env ZMM_UTTERANCE_RETRIEVE=1 ZMM_HYBRID=1 ZMM_DATE_ANCHOR=1 \
    ZMM_UTTERANCE_TYPES=single-session-user,single-session-preference,knowledge-update,temporal-reasoning \
    ZMM_SSU_UTTERANCE=1 ZMM_SSU_UTT_TYPES=single-session-user,single-session-assistant,single-session-preference,knowledge-update \
    ZMM_LOAD_RERANKER=1 \
    ZMM_LONGMEMEVAL_PATH=.cache/longmem_s.json \
    ZMM_LLM_PROVIDER=openai ZMM_LLM_BASE_URL=$ARK_BASE_URL ZMM_LLM_API_KEY=$ARK_API_KEY \
    ZMM_SUBJECT_MODEL=doubao-seed-2-0-pro-260215 \
    ZMM_JUDGE_PROVIDER=openai ZMM_JUDGE_BASE_URL=https://newapi.07211996.xyz/v1 ZMM_JUDGE_API_KEY=sk-tU6bGHCw6cMotQvtAa502W4hEtMJe4PSkWbWWY5iuv0f4Bgf \
    ZMM_JUDGE_MODEL=glm-5.3-flash \
    python3 tests/eval_longmemeval_accuracy.py --pipeline=m3-only --full --start $S --end $E \
    > /tmp/e2e500_s${S}.log 2>&1
}

setsid nohup bash -c "$(declare -f run_shard); run_shard 0 125" < /dev/null > /dev/null 2>&1 &
sleep 3
setsid nohup bash -c "$(declare -f run_shard); run_shard 125 250" < /dev/null > /dev/null 2>&1 &
sleep 3
setsid nohup bash -c "$(declare -f run_shard); run_shard 250 375" < /dev/null > /dev/null 2>&1 &
sleep 3
setsid nohup bash -c "$(declare -f run_shard); run_shard 375 500" < /dev/null > /dev/null 2>&1 &
echo "4_SHARDS_LAUNCHED"
