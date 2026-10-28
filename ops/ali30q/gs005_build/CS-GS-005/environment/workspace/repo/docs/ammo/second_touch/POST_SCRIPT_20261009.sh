#!/bin/bash
# 10/9 二触投放脚本(逐仓读 md → POST 评论)· 干跑:去掉 DRY 后缀即真投
set -e
declare -A T=(
 [01_miniswe]="SWE-agent/mini-swe-agent/issues/986"
 [02_sweagent]="SWE-agent/SWE-agent/issues/1595"
 [03_openhands]="OpenHands/OpenHands/issues/18065"
 [04_aider]="Aider-AI/aider/issues/5811"
 [05_moatless]="aorwall/moatless-tools/issues/72"
 [06_goose]="aaif-goose/goose/issues/12712"
 [07_cline]="cline/cline/issues/14859"
 [08_lobsterai]="netease-youdao/LobsterAI/issues/2801"
 [09_openocta]="openocta/openocta/issues/118"
 [10_opensquilla]="TokenRhythm/opensquilla/issues/1885"
 [11_ohmycoder]="VOBC/oh-my-coder/issues/24"
)
DIR="$(cd "$(dirname "$0")" && pwd)"
for k in "${!T[@]}"; do
  ep="${T[$k]}"
  body=$(python3 -c "import json,sys;print(json.dumps({'body':open(sys.argv[1],encoding='utf-8').read()}))" "$DIR/$k.md")
  if [ "${1:-DRY}" = "REAL" ]; then
    gh api "repos/$ep/comments" -f body="$(cat "$DIR/$k.md")" --jq '.html_url' && echo "[$k] POSTED → $ep"
  else
    echo "[$k] DRY → $ep ($(wc -c < "$DIR/$k.md") bytes)"
  fi
done
