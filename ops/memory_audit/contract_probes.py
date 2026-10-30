#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""迁移后遗症契约审计 · 第1条:消费者×输入形态探针矩阵(v2)。

四形态(迁移史真实出现过的,v2 修正 cwd 构造法——编码名必须与假目录名匹配):
  A 带点路径组件 → Claude Code 实际目录把点编为横线(本次7天死根因形态的忠实复刻)
  B 中文路径(unicode 不破坏)
  C Windows 旧名(编码形态单测:C:\\ → --)
  D 精确名优先于带后缀改名产物
方法: 假 HOME 构造 projects 树,patch recall.HOME + chdir 逐形态断言。退出码 0/1。
"""
import os
import sys
import tempfile
from pathlib import Path

PLUG = Path.home() / ".claude/plugins/nautilus-compass"
sys.path.insert(0, str(PLUG))
import recall  # noqa: E402

PASS, FAIL = [], []


def encode(cwd: str) -> str:
    return cwd.replace(":\\", "--").replace(":/", "--").replace("\\", "-").replace("/", "-")


def probe(tag: str, cwd: Path, fake_home: Path, expect_dir: str):
    old_home, old_cwd = recall.HOME, os.getcwd()
    recall.HOME = fake_home
    os.chdir(cwd)
    try:
        got = recall.find_active_project_memory_dir()
        ok = got is not None and got.parent.name == expect_dir
        (PASS if ok else FAIL).append(f"{tag}: expect={expect_dir} got={getattr(got, 'parent', None) and got.parent.name}")
    except Exception as e:
        FAIL.append(f"{tag}: 异常 {type(e).__name__}: {e}")
    finally:
        recall.HOME = old_home
        os.chdir(old_cwd)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td).resolve()
        home = root / "home"
        # A: cwd 带点组件,目录用横线(复刻 chunxiao.wang→chunxiao-wang)
        cwd_a = root / "wd.chunxiao.wang" / "proj"
        cwd_a.mkdir(parents=True)
        enc_a = encode(str(cwd_a))                      # 含点版本
        dir_a = enc_a.replace(".", "-")                 # Claude Code 实际命名
        p = home / ".claude/projects" / dir_a / "memory"
        p.mkdir(parents=True); (p / "m.md").write_text("x")
        probe("A 带点路径→横线目录", cwd_a, home, dir_a)
        # B: 中文组件(编码保留 unicode,目录同形=精确匹配)
        cwd_b = root / "项目甲"
        cwd_b.mkdir(parents=True)
        dir_b = encode(str(cwd_b))
        p = home / ".claude/projects" / dir_b / "memory"
        p.mkdir(parents=True); (p / "m.md").write_text("x")
        probe("B 中文路径(unicode)", cwd_b, home, dir_b)
        # C: Windows 编码形态单测
        enc_c = encode("C:\\Users\\chunx\\Projects\\proj")
        (PASS if enc_c == "C--Users-chunx-Projects-proj" else FAIL).append(
            f"C Windows旧名: enc={enc_c!r} {'OK' if enc_c == 'C--Users-chunx-Projects-proj' else 'BAD'}")
        # D: 精确名 vs 带后缀兄弟目录
        cwd_d = root / "wd_d" / "proj"
        cwd_d.mkdir(parents=True)
        dir_d = encode(str(cwd_d))
        for suf in ("", ".dup20261023"):
            p = home / ".claude/projects" / (dir_d + suf) / "memory"
            p.mkdir(parents=True); (p / "m.md").write_text("x")
        probe("D 精确名优先于后缀名", cwd_d, home, dir_d)
    print(f"契约探针矩阵: {len(PASS)} 过 / {len(FAIL)} 挂")
    for line in PASS: print(f"  ✅ {line}")
    for line in FAIL: print(f"  ❌ {line}")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main())
