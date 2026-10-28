# _OUTBOUND_FROM_OPENCLAW_TO_FLYWHEEL_20261020 · 存储融通工程协作单

> 发件:openclaw(Mac mini 中枢) · 收件:Flywheel · 2026-10-20
> 主题:115+NAS+数据飞轮+Cloud 存储融通——现成底座接口清单移交
> 物理件:正本 `\\NASNEW\work\nautilus-migration\COORD_storage_fusion_flywheel_20261020.md`(Mac: /Volumes/work-nfs/nautilus-migration/...;台式机: H:\nautilus-migration\...)

用户已定调:飞轮牵头融通,实现「外部采集→入池」「加工后→对外发送」,打通 tailnet 与 cloud 网络。

本中枢移交**实测在跑的现成底座**(请勿重复建设):

1. **统一池视图**:cloud `/mnt/org-storage`(rclone union: NAS-SFTP+115-CD2,systemd 常驻)
2. **115 三姿势**:CD2 WebDAV :19798/dav/115open · Mac rclone `cd2-115:` · alist :5244;Pool/=具身数据专用池
3. **NAS 全通道**:NFS 417MB/s + SMB×5 + WebDAV :6085 + tailnet 直连 100.95.194.60
4. **网络骨干**:tailnet 三点(Mac 100.84.23.45/cloud 100.109.6.13/NAS 100.95.194.60)+ funnel 公网四入口+ /pub 只读外发站
5. **Mac 加工引擎**:whisper/DuckDB/ffmpeg/ImageMagick/Blender/Playwright + pg17 六库 + bge:19988 + rerank:8401 + v5 API:18001

**缺口三件**(融通要补):①受控入向收件口(建议 alist /api/fs/put+inbox-external) ②出向直链(alist 分享) ③池内 raw/curated/outbox 目录约定。

接口详情与坑清单见正本。接入遇堵:NAS 任务单回写本函或 Mac shell(chunxiao.wang@192.168.5.120,compass 已验证可达)。

—— openclaw · Mac mini · 2026-10-20
