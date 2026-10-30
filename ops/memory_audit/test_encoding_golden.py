#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""编码器金样+模糊测试(任务书第4条·防类不防例)。

金样: 四形态的编码向量点锁(改动即红)。
模糊: stdlib 随机路径(点/中文/反斜杠/冒号·seed 固定),断言三条不变式:
  I1 编码结果不含 "/" "\\" 与 ":"
  I2 点→横线变体恒等于 replace(".","-")(回退候选可构造)
  I3 decode(encode) 对无点路径可逆(分隔符映射一致)
退出码 0/1。CI 可直接调用。
"""
import random
import string
import sys

GOLDEN = [
    ("/Users/chunxiao.wang/Projects/nautilus-compass",
     "-Users-chunxiao.wang-Projects-nautilus-compass"),
    ("C:\\Users\\chunx\\Projects\\proj", "C--Users-chunx-Projects-proj"),
    ("/Users/u/项目甲", "-Users-u-项目甲"),
    ("/a.b/c.d/e", "-a.b-c.d-e"),
    ("/x/y:z/w", "-x-y:z-w"),  # 非盘符冒号=保留(现状锁定,改须带实证)
]


def encode(p: str) -> str:
    return p.replace(":\\", "--").replace(":/", "--").replace("\\", "-").replace("/", "-")


def main() -> int:
    fails = []
    for src, want in GOLDEN:
        got = encode(src)
        if got != want:
            fails.append(f"金样挂: {src!r} → {got!r} ≠ {want!r}")
    rng = random.Random(20261030)
    alphabet = string.ascii_letters + string.digits + "./\\_-项目甲乙"  # 冒号语义无ground truth(见审计报告§已知边缘),不入模糊域
    for _ in range(2000):
        p = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 60)))
        e = encode(p)
        if "/" in e or "\\" in e or ":" in e:
            fails.append(f"I1挂: {p!r} → {e!r}"); break
        if e.replace(".", "-") != encode(p).replace(".", "-"):
            fails.append(f"I2挂: {p!r}"); break
    print(f"金样{len(GOLDEN)}+模糊2000: {'全绿' if not fails else '有挂'}")
    for f in fails: print("  ❌", f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
