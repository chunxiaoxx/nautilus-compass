# 页面部署 runbook(每次发布逐条走,7/17 全天 6 次零事故)

## 发布前(本地)
1. 结构自检:python 校验标签平衡(`<script>/<canvas>/<div>/<table>` 开闭数相等)+ `</html>` 恰 1 个;
2. **外发物敏感词 grep 必须=0**:国曙/觅蜂/光轮/凡拓/蜂巢/打法/切它/五目/甲方名;
3. 交互改动:内外两版**同源同步**(从内部版程序化抽取注入外发版,禁手抄第二份)。

## 发布
scp 到 cloud:/tmp → `sudo mv` 到 `/var/www/fde.nautilus.social/embodied/<path>/index.html` → **md5 双端比对必须一致**。

## 发布后复验(缺一不算发布)
- `curl` 无凭据 → **401**(锁在;注意 nginx reload 有传播延迟,第一次 200 要复测);
- `curl -u fde:***` → **200** 且 bytes 合理;
- 关键新内容 `grep -c` ≥1(敏感词与内容词分开 grep,不混一个计数——7/17 踩过混计数探针漏洞);
- 交互改动:浏览器强刷实际点一遍(裁判 R4 误判就是复验时用户先发现的,教训:canvas 交互必须真手玩,curl 看不出)。

## 凭据与路径
账号 fde(密码见 htpasswd,用户已知)· 内部版 /embodied/ · 外发版 /embodied/public/ · /embodied/partner/ 和 /embodied/genui/ = 301 归并勿复活 · 字体 /embodied/fonts/(104 分片,已稳定,勿动)。

## 团队工作台同步(OPS_STATE / workflows / 审计任一有变时必做)
```bash
cd /c/Users/chunx/Projects/embodied-data-factory
for f in "OPS_STATE.md:ops-state.md" "docs/biz/pitch-cheatsheet.md:cheatsheet.md" \
  "workflows/research-agent-template.md:wf-research.md" "workflows/audit-pipeline.md:wf-audit.md" \
  "workflows/deploy-runbook.md:wf-deploy.md" \
  "docs/audit/2026-07-17-lerobot-pusht-audit.md:audit-pusht.md" \
  "docs/audit/2026-07-17-aloha-coffee-audit.md:audit-aloha.md"; do
  src="${f%%:*}"; dst="${f##*:}"; scp -q "$src" "cloud:/tmp/$dst";
done
ssh cloud 'sudo mkdir -p /var/www/fde.nautilus.social/embodied/team/docs && sudo mv /tmp/ops-state.md /tmp/cheatsheet.md /tmp/wf-*.md /tmp/audit-*.md /var/www/fde.nautilus.social/embodied/team/docs/'
curl -s -u "fde:***" -o /dev/null -w "%{http_code}" https://fde.nautilus.social/embodied/team/docs/ops-state.md  # 必须 200
```

## 纪律
每次改动 = git commit(部署的必须是已提交内容);禁 VM 直改;新路径必须先确认 internal-lock 覆盖。
