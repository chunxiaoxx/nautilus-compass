# -*- coding: utf-8 -*-
"""BC1 发布日自动执行(2026-09-27 Runbook 的机械腿).

子命令:
  check-links   发布物链接全检(Runbook P4)
  flip          README 预告→LAUNCHED + 墙页预告块→发布块(工作树内)
  push          git add 指定两文件+commit+push(不用 -A)
  deploy-wall   scp 墙页到 cloud + 外网回读验证
  letter        发布完成通报函(platform+daily)
  counters      首日计数器(报名 issue/UTM 访问)→launch_day_report.md
  all           check-links → flip → push → deploy-wall → letter 顺序,
                任一判据不过即停(不带着红灯往下走)。

Discord 发帖(Runbook ③)走 scripts/post_discord.py(CDP 9224,Slate Enter
带 text="\\r"),中文稿(④)是外部依赖——本脚本只做提醒,不代做。
"""
import argparse
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = ROOT / "README.md"
WALL = ROOT / "landing" / "wall.html"
BLOCK = ROOT / "runtime/assay_bc1_20260927/wall_bc1_block.html"
LETTER = ROOT / "runtime/assay_bc1_20260927/launch_letter.md"
REPORT = ROOT / "runtime/assay_bc1_20260927/launch_day_report.md"
WALL_URL = "https://compass.nautilus.social/wall.html"
SSH_HOST = "cloud"
REMOTE_WALL = "/home/ubuntu/nautilus-compass/landing/wall.html"

LINKS = [  # (url, 允许状态码集)
    ("https://github.com/chunxiaoxx/nautilus-compass/blob/main/"
     "docs/benchmarks/BC1_LAUNCH.md", {200}),
    ("https://github.com/chunxiaoxx/nautilus-compass/tree/main/"
     "runtime/assay_bc1_20260927", {200}),
    ("https://raw.githubusercontent.com/chunxiaoxx/nautilus-compass/main/"
     "runtime/assay_bc1_20260927/SELFTEST_SCORECARD_V2.md", {200}),
    ("https://github.com/chunxiaoxx/nautilus-compass/issues/new"
     "?template=exam-signup.md", {200, 302}),  # 302=登录跳转正常
    (WALL_URL, {200}),
]

TEASER_RE = re.compile(
    r"<h2>BC1 — first benchmark cohort \(2026-09-27\)</h2>.*?</p>",
    re.S)


def http_code(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "bc1-launch-check"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return -1


def check_links() -> bool:
    ok = True
    for url, allow in LINKS:
        code = http_code(url)
        good = code in allow
        ok &= good
        print(f"  [{'OK' if good else 'FAIL'}] {code} {url}")
    return ok


def flip() -> bool:
    """README + 墙页预告→发布。幂等:已翻则跳过。"""
    rd = README.read_text(encoding="utf-8")
    if "[launching 9/27]" in rd:
        README.write_text(rd.replace("[launching 9/27]",
                                     "[LAUNCHED 9/27]"), encoding="utf-8")
        print("  README: flipped")
    else:
        print("  README: 已是发布态或标记缺失(人工核)")
    wall = WALL.read_text(encoding="utf-8")
    if "LAUNCHED 2026-09-27" in wall:
        print("  wall: 已是发布块,跳过")
        return True
    block = BLOCK.read_text(encoding="utf-8").strip()
    new, n = TEASER_RE.subn(block, wall)
    if n != 1:
        print(f"  wall: FAIL——预告块匹配数={n}(应为 1),未改")
        return False
    WALL.write_text(new, encoding="utf-8")
    print("  wall: 预告块已换发布块")
    return True


def git(*args) -> int:
    return subprocess.run(["git", *args], cwd=ROOT).returncode


def push() -> bool:
    if git("add", "README.md", "landing/wall.html") != 0:
        return False
    rc = git("commit", "-m",
             "feat(bc1): 9/27 发布——README/墙页翻发布态(Runbook ①②)")
    if rc != 0:  # 可能无改动(幂等重跑)
        print("  git: 无新改动,直推")
    return git("push", "origin", "main") == 0


def deploy_wall() -> bool:
    rc = subprocess.run(
        ["scp", "-q", str(WALL), f"{SSH_HOST}:{REMOTE_WALL}"]).returncode
    if rc != 0:
        print("  scp FAIL")
        return False
    try:
        with urllib.request.urlopen(WALL_URL, timeout=20) as r:
            body = r.read().decode("utf-8", "replace")
    except Exception as e:
        print("  回读 FAIL:", repr(e)[:120])
        return False
    ok = "LAUNCHED 2026-09-27" in body
    print(f"  外网回读: {'OK——发布块在墙' if ok else 'FAIL——发布块未现'}")
    return ok


def letter() -> bool:
    ok = True
    for to in ("platform", "daily"):
        rc = subprocess.run([
            sys.executable, str(ROOT / "scripts/platform_mail.py"), "send",
            to, f"bc1-launch-20260927-{to}",
            "[发布完成通报] Assay BC1 已发布(9/27 Runbook)",
            str(LETTER), "--deadline", "2026-09-28 22:00"]).returncode
        ok &= rc == 0
    return ok


def counters() -> None:
    lines = ["# BC1 首日计数器(22:00 落账)", ""]
    r = subprocess.run(
        ["gh", "issue", "list", "--repo", "chunxiaoxx/nautilus-compass",
         "--limit", "50", "--json", "number,title,createdAt",
         "--state", "all"], capture_output=True, text=True)
    import json
    n_signup = 0
    if r.returncode == 0:
        for it in json.loads(r.stdout):
            if it["createdAt"] >= "2026-09-27" and re.search(
                    r"exam|bc1", it["title"], re.I):
                n_signup += 1
    lines.append(f"- 报名/考试相关 issue(9/27 起): {n_signup}")
    r = subprocess.run(
        ["ssh", SSH_HOST, "sudo -n zgrep -h bc1_launch_0927 "
         "/var/log/nginx/access.log* 2>/dev/null | wc -l"],
        capture_output=True, text=True, timeout=30)
    utm = r.stdout.strip() if r.returncode == 0 else "查不到(权限/路径)"
    lines.append(f"- UTM(bc1_launch_0927)nginx 命中: {utm}")
    lines.append("- Discord 反应数: 走 cdp_tool.py 直链人工读(③存的 lastid)")
    lines.append("- 判分请求数: 看本仓 issue+邮箱,人工计")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["check-links", "flip", "push",
                                     "deploy-wall", "letter", "counters",
                                     "all"])
    a = ap.parse_args()
    if a.step == "check-links":
        sys.exit(0 if check_links() else 1)
    if a.step == "flip":
        sys.exit(0 if flip() else 1)
    if a.step == "push":
        sys.exit(0 if push() else 1)
    if a.step == "deploy-wall":
        sys.exit(0 if deploy_wall() else 1)
    if a.step == "letter":
        sys.exit(0 if letter() else 1)
    if a.step == "counters":
        counters()
        return
    # all: 判据不过即停
    for name, fn in [("check-links", check_links), ("flip", flip),
                     ("push", push), ("deploy-wall", deploy_wall),
                     ("letter", letter)]:
        print(f"== {name}")
        if not fn():
            print(f"STOP: {name} 红灯,不继续")
            sys.exit(1)
    print("ALL GREEN——剩人工:③Discord 发帖(post_discord.py)④中文稿")


if __name__ == "__main__":
    main()
