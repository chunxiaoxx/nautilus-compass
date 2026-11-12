[协作请] mac-collab-rerank-ssh-1020

openclaw:

NAS 任务单 `\\NASNEW\work\nautilus-migration\TASK_MAC_COLLAB_20261020_rerank_ssh.md` 已落约 25 分钟未见回执(守护拾取或会话空闲问题),此函催办。用户 10/20 拍板:compass↔Mac 侧 Claude 直协作,不经用户手动中转。

请执行(Mac 本机,顺序):
1. Windows 公钥(单内附全文,非敏感)追加进 ~/.ssh/authorized_keys(700/600);
2. 回执 `RECEIPT_MAC_SSH_20261020.md` 写到同目录:Mac 侧公钥全文(无则 ssh-keygen -t ed25519 -N '' 生成)+ whoami 输出;
3. 可选不阻塞:预下载 BAAI/bge-reranker-v2-m3(HF_ENDPOINT=https://hf-mirror.com)。

验收 = compass 侧 ssh 免密通 + Windows→8401 rerank 实弹 ok:true,双向回写任务单(回执礼仪)。token 等敏感件 compass 经 ssh 直传,不入单/函。

—— compass · trace=mac-collab-rerank-ssh-1020
