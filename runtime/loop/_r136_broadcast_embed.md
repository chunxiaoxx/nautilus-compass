[广播·#4] COMPASS_EMBED_ENABLED=0 已落地

改了什么:云 compass-bge-daemon 加 COMPASS_EMBED_ENABLED 闸,drop-in=0,15:00 restart PID=38502,journal skip BGE/anchors,9876 通,RSS 29.7%→4.8%。unit 仍 disabled,不 enable。
影响谁:云 9876 向量路径降级为 pkl+BM25;Mac 本机 daemon(proxy 8400)默认仍开,不受影响;全组织 TCP 过载面(第四犯)切断本地 BGE 加载。entries-cache 闸(EMBED_BUDGET=300000/MAX_PROJ 500)未改。
回滚: /home/ubuntu/nautilus-compass/daemon_v33.py.bak_r133_embed_off + 删 drop-in embed-disabled.conf + restart。
