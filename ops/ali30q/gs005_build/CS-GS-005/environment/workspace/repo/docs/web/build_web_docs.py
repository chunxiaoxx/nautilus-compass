# -*- coding: utf-8 -*-
"""白皮书/BP md→html 网页版生成器(20261006 用户令:网页+文档双版本)。
产出 docs/web/WHITEPAPER.html + BUSINESS_PLAN.html;静态自包含,零 JS 依赖。"""
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent  # docs/
TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta property="og:title" content="{title}">
<meta property="og:description" content="{subtitle}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<style>
:root{{--ink:#1a2233;--mut:#5b6472;--line:#e3e7ee;--brand:#0f62fe;--bg:#fbfcfe;--card:#fff}}
*{{box-sizing:border-box}}
body{{margin:0;font:16px/1.75 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif;color:var(--ink);background:var(--bg)}}
header{{background:linear-gradient(135deg,#0b1c3d,#0f62fe);color:#fff;padding:40px 24px 28px}}
header .wrap,main{{max-width:980px;margin:0 auto;padding:0 20px}}
header h1{{margin:0 0 6px;font-size:30px;letter-spacing:.5px}}
header p{{margin:0;opacity:.85;font-size:14px}}
nav.toc{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 20px;margin:20px auto;max-width:940px;font-size:14px}}
nav.toc b{{color:var(--mut)}}
nav.toc a{{color:var(--brand);text-decoration:none;margin-right:14px;white-space:nowrap}}
main{{padding-bottom:60px}}
h2{{font-size:22px;border-left:4px solid var(--brand);padding-left:10px;margin-top:40px}}
h3{{font-size:18px;margin-top:26px}}
table{{border-collapse:collapse;width:100%;margin:14px 0;background:var(--card);font-size:14px}}
th,td{{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}
th{{background:#f0f4fb}}
code{{background:#eef1f6;padding:1px 5px;border-radius:4px;font-size:13.5px}}
pre{{background:#0e1526;color:#dbe4ff;padding:14px;border-radius:8px;overflow:auto;font-size:13px}}
pre code{{background:none;color:inherit}}
blockquote{{margin:12px 0;padding:8px 14px;border-left:4px solid var(--line);color:var(--mut);background:var(--card)}}
hr{{border:none;border-top:1px solid var(--line);margin:32px 0}}
footer{{text-align:center;color:var(--mut);font-size:12.5px;padding:18px;border-top:1px solid var(--line)}}
a{{color:var(--brand)}}
@media print{{header{{background:#0b1c3d}}nav.toc{{display:none}}}}
</style>
</head>
<body>
<header><div class="wrap"><h1>{title}</h1><p>{subtitle}</p></div></header>
<nav class="toc"><b>目录</b> {toc}</nav>
<main>
{body}
</main>
<footer>Nautilus · 本页由文档正本生成(md 单一事实源,网页为只读视图) · 生成时间 {stamp} · {source}</footer>
</body>
</html>"""


def build(md_path: Path, out_path: Path, title: str, subtitle: str, source: str):
    md = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(md, extensions=["tables", "fenced_code"])
    # h2 锚点+目录
    heads = re.findall(r"<h2>(.*?)</h2>", body)
    toc, n = [], 0
    for h in heads:
        n += 1
        anchor = f"s{n}"
        body = body.replace(f"<h2>{h}</h2>", f'<h2 id="{anchor}">{h}</h2>', 1)
        plain = re.sub(r"<[^>]+>", "", h)
        toc.append(f'<a href="#{anchor}">{plain}</a>')
    html = TPL.format(title=title, subtitle=subtitle, toc="".join(toc),
                      body=body, stamp="2026-10-06", source=source)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"{out_path} {len(html)//1024}KB anchors={n}")


build(ROOT / "UNIPAT_TECH_WHITEPAPER_V1_20261006.md",
      ROOT / "web" / "whitepaper.html",
      "Nautilus 技术白皮书 · Agent 评测与数据基础设施",
      "v1.3 · 判据 sha 锚定 · 负结果照报 · 坐标可寻址",
      "文档正本 chunxiaoxx/nautilus-core · docs/UNIPAT_TECH_WHITEPAPER_V1_20261006.md")
build(ROOT / "UNIPAT_BUSINESS_PLAN_V1_20261006.md",
      ROOT / "web" / "business-plan.html",
      "Nautilus 商业计划书 · Agent 评测与数据基础设施",
      "v1.2 · 产品九档价格墙 · 交叉销售 · 北极星 10/31",
      "文档正本 chunxiaoxx/nautilus-core · docs/UNIPAT_BUSINESS_PLAN_V1_20261006.md")
