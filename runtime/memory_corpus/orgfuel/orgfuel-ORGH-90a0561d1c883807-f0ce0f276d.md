---
name: orgfuel-ORGH-90a0561d1c883807-f0ce0f276d
description: "commit efaa7dc2794e 2026-09-05 feat(tools): feishu_send_file"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-90a0561d1c883807
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit efaa7dc2794e 2026-09-05
feat(tools): feishu_send_file.py——飞书 IM 传文件可复用工具(复用 tenant app 凭证)
- 两步流: /im/v1/files multipart 上传(file_type=stream)→ /im/v1/messages receive_id_type=chat_id 发 file 消息
- chats 子命令列 bot 所在会话;send 支持 --note 附言
- 凭证读 ~/.claude/.cache/.fde_api_secrets.env,零新依赖(urllib 手拼 multipart)
- 首用实测: PPT pptx(1.9MB)已送达用户单聊 om_x100b669bc4a840a0c0241c9e513c59a(用户两次催办项关闭)
