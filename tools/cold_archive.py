# -*- coding: utf-8 -*-
"""冷层压缩+保留策略:30 天前的会话 jsonl → gzip 原位压缩(可逆)。
默认 dry-run 只报不动手;--apply 才压,压前逐文件 roundtrip 校验,防假绿。
纪律:压缩后旧会话从 resume 列表消失(解压即恢复);活动会话按 mtime 自然排除。
"""
import gzip
import os
import sys
import time
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HOME = os.path.expanduser("~")
ROOT = os.path.join(HOME, ".claude", "projects")
AGE_DAYS = 30
KEEP_BYTES = 200 * 1024          # 小于 200KB 的不动(碎会话留着也不占地方)
ACTIVE_SESSION = "74ab6042-59f0-4605-92cc-851ea52a70d7"  # 本会话,双保险排除


def main():
    apply = "--apply" in sys.argv
    now = time.time()
    cands = []
    for proj in sorted(os.listdir(ROOT)):
        pd = os.path.join(ROOT, proj)
        if not os.path.isdir(pd):
            continue
        for f in os.listdir(pd):
            if not f.endswith(".jsonl") or ACTIVE_SESSION in f:
                continue
            p = os.path.join(pd, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            age = (now - st.st_mtime) / 86400
            if age >= AGE_DAYS and st.st_size >= KEEP_BYTES:
                cands.append((p, st.st_size, age))
    total = sum(s for _, s, _ in cands)
    print(f"候选 {len(cands)} 个文件 / {total/1048576:.0f}MB (>{AGE_DAYS}天, >{KEEP_BYTES//1024}KB)")
    byproj = {}
    for p, s, a in cands:
        proj = os.path.basename(os.path.dirname(p))
        byproj.setdefault(proj, [0, 0])
        byproj[proj][0] += 1
        byproj[proj][1] += s
    for proj, (n, s) in sorted(byproj.items(), key=lambda x: -x[1][1]):
        print(f"  {s/1048576:9.1f}MB  {n:4d}文件  {proj}")

    if not apply:
        print("\n[dry-run] 加 --apply 执行压缩(预计省 ~85%)")
        return
    mf = os.path.join(HOME, ".claude", "memory-distill", f"cold_archive_{datetime.now():%Y%m%d}.csv")
    os.makedirs(os.path.dirname(mf), exist_ok=True)
    done = fail = saved = 0
    with open(mf, "w", encoding="utf-8") as log:
        log.write("path,orig_bytes,gz_bytes,verified\n")
        for p, s, _ in cands:
            gz = p + ".gz"
            try:
                raw = open(p, "rb").read()
                with gzip.open(gz + ".tmp", "wb", compresslevel=6) as g:
                    g.write(raw)
                os.replace(gz + ".tmp", gz)
                # roundtrip 校验
                back = gzip.open(gz, "rb").read()
                if len(back) != len(raw):
                    raise ValueError("roundtrip mismatch")
                os.remove(p)
                log.write(f"{p},{len(raw)},{os.path.getsize(gz)},ok\n")
                done += 1
                saved += len(raw) - os.path.getsize(gz)
            except Exception as e:
                fail += 1
                log.write(f"{p},{s},,FAIL:{e}\n")
                if os.path.isfile(gz + ".tmp"):
                    os.remove(gz + ".tmp")
    print(f"[apply] 压缩 {done} / 失败 {fail} / 释放 {saved/1048576:.0f}MB → 清单 {mf}")


if __name__ == "__main__":
    main()
