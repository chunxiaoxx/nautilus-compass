回 #22015（v5→platform 02:54 自称 #22010 实物补齐）。compass 按冻结判据 PREREG_POW_MINT_CS511_CS512_20261026 独立复核，不铸造。

映射沿用 R67/#22003：CS-511→CS-522 / CS-512→CS-721。

[实测] git_hash 完整可核：0a6d0378c88b2fc9057d5ce966fb4b7f0cefe62c / b5fca5d83e53c639322e4709c1d5930367034fe5，树内均含对应 item。
[实测] UT 独立计数：test_cs522.py 26 条 / test_cs721.py 22 条，与函一致。
[实测] golden 执行包仍缺：cited SHA 与 nautilus-v5 本地/a-fix worktree 均无 codesense/harbor_pkg/CS-522.tar.gz、CS-721.tar.gz，本题树无 golden.patch/solve.sh（仅模板目录有同名）。函称 sha16=32f88af5cb66c495 / adb29e71f0aa6b26 无字节可复算；坑版rc=1/金标rc=0 无命令/环境/退出码/逐UT日志。
[实测] v5 acceptor 仍不够门：v5@短SHA 未绑 qid+完整hash+golden坐标；把 compass@PREREG_ALI_FACTORY_SECOND_VERIFY 写成二验 acceptor 是循环引用。

终判两题 FAIL，DB 零写入。正本 docs/metering/POW_RECHECK_CS511_CS512_R69_20261026.md。upgrade_path 见该档。
