#!/usr/bin/env python3
# 候选起点(correct-by-construction 仅当输入恰好按版本升序到达——现实里靠不住)。
# 场景:一个把"带版本的记录"按 uid 合并/去重的服务的最小缩影。每条记录有
#   uid(标识)、version(整数版本号)、payload(内容)。同一 uid 可能有多个版本
#   (改稿/重发),需求是对每个 uid 取**最新版本**(version 最大)的 payload。
#
# 协议:stdin 每行一条记录 "uid|version|payload"
#   - version 是整数;payload 是不含 '|' 的串。
#   - 输出:每个 uid 一行 "uid|payload",按 uid 字典序排序(保证确定性)。
#
# BUG:用 {r_uid: r for ...} 字典推导去重——只用 uid 当键,谁在迭代顺序里
# 最后出现谁覆盖(last-in-iteration-wins),完全没看 version。当输入恰好按
# version 升序到达时碰巧对(最后的就是最新的);但记录乱序到达(改稿后旧版后到、
# 重发、并发写入)时系统性取错版本:高版本(改稿)被后到的低版本(旧版)遮蔽,
# 拿到过期内容。
#
# 任务:修复使每个 uid 取到 version 最大那条的 payload,与输入到达顺序无关。
# 只许改本文件。仅标准库。
import sys


def parse(line):
    uid, ver, payload = line.split("|", 2)
    return uid, int(ver), payload


def main():
    records = []
    for line in sys.stdin.read().splitlines():
        if not line.strip():
            continue
        uid, ver, payload = parse(line)
        records.append({"uid": uid, "version": ver, "payload": payload})

    # BUG: 只用 uid 当键,迭代顺序里最后出现的覆盖之前的。没纳入 version。
    # 输入乱序时(高版本不在末尾),会被后到的低版本遮蔽。
    latest = {r["uid"]: r for r in records}

    for uid in sorted(latest):
        print(f"{uid}|{latest[uid]['payload']}")


if __name__ == "__main__":
    main()
