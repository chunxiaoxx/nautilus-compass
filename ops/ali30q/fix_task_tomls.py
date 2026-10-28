#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""task.toml 批量合法化修复器(F-008 影响面清剿 · 2026-10-28)

三种实测坏法迭代修复至 tomllib 合法:
  M1 空值行(key = )+孤数组行        → 合并为 key = [...]
  M2 字符串行缺闭合引号              → 行尾补 "
  M3 [[metadata.badpatterns.items]] 撞 inline badpatterns → 删该段(元数据非判分必需)
用法:
  python3 fix_task_tomls.py <items_dir> --dry-run
  python3 fix_task_tomls.py <items_dir> --apply
"""
import argparse, glob, tomllib
from pathlib import Path

def fix_text(text: str):
    """迭代修复,返回 (新文本, 修复清单)。单文件最多 8 轮防死循环。"""
    fixes = []
    lines = text.split("\n")
    for _ in range(8):
        try:
            tomllib.loads("\n".join(lines))
            return "\n".join(lines), fixes
        except tomllib.TOMLDecodeError as e:
            msg = str(e)
            # 定位行号
            ln = None
            for tok in ("(at line ",):
                if tok in msg:
                    ln = int(msg.split(tok)[1].split(",")[0].split(")")[0])
            if ln is None:
                fixes.append(f"无法定位: {msg[:60]}")
                return "\n".join(lines), fixes
            i = ln - 1
            if i >= len(lines):
                fixes.append(f"行{i+1}越界"); return "\n".join(lines), fixes
            l = lines[i]
            # M3: 撞键段删除
            if "Cannot mutate" in msg and l.strip().startswith("[["):
                j = i + 1
                while j < len(lines) and not lines[j].strip().startswith("[["):
                    j += 1
                del lines[i:j]                     # 本段=起点到下一个[[前
                fixes.append(f"M3 行{i+1}: 删撞键段 [[metadata.badpatterns.items]]")
                continue
            # M1: 空值行+孤数组
            if l.strip().endswith("=") or l.strip() == l.split("=")[0].strip() + "=":
                key = l.split("=")[0].strip()
                arr = None
                for j in range(i+1, min(i+8, len(lines))):
                    if lines[j].strip().startswith("["):
                        # 多行数组: 收集至 ']' 结尾行
                        buf = [lines[j]]
                        k = j
                        while not buf[-1].rstrip().endswith("]") and k+1 < len(lines):
                            k += 1
                            buf.append(lines[k])
                        arr = " ".join(b.strip() for b in buf)
                        for d in range(j, k+1):
                            lines[d] = ""
                        break
                lines[i] = f"{key} = {arr}" if arr else f'{key} = ""'
                fixes.append(f"M1 行{i+1}: 空值 {key} " + ("合并孤数组" if arr else '补 ""'))
                continue
            # M4: 同 key 二次赋值(Cannot overwrite) → 删重复行(元数据非判分必需)
            if "Cannot overwrite" in msg or "Cannot mutate" in msg:
                lines[i] = f'__removed_dup_{i}__ = "{i+1}行重复key已删"'
                # 用假 key 避免继续撞: 直接删行更干净
                lines[i] = ""
                fixes.append(f"M4 行{i+1}: 删重复/撞键行")
                continue
            # M2: 字符串缺闭合引号
            if l.count('"') % 2 == 1:
                lines[i] = l.rstrip() + '"'
                fixes.append(f"M2 行{i+1}: 补闭合引号")
                continue
            fixes.append(f"行{i+1} 未识别坏型: {msg[:50]}")
            return "\n".join(lines), fixes
    return "\n".join(lines), fixes + ["8轮未收敛"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items_dir", type=Path)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    fixed = ok = fail = 0
    for p in sorted(glob.glob(str(a.items_dir / "CS-*" / "task.toml"))):
        name = Path(p).parent.name
        try:
            tomllib.load(open(p, "rb")); ok += 1; continue
        except tomllib.TOMLDecodeError:
            pass
        orig = Path(p).read_text(encoding="utf-8")
        new, fixes = fix_text(orig)
        try:
            tomllib.loads(new)
        except tomllib.TOMLDecodeError as e:
            print(f"❌ {name}: 修复后仍非法 {str(e)[:50]}"); fail += 1; continue
        fixed += 1
        print(f"🔧 {name}: {'; '.join(fixes)}")
        if a.apply:
            Path(p).write_text(new, encoding="utf-8")
    print(f"\n合计: 原本合法 {ok} · 修复 {fixed} · 修不动 {fail} · apply={a.apply}")

if __name__ == "__main__":
    main()
