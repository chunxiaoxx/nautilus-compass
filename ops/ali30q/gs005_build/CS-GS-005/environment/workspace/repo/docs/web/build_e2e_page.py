# -*- coding: utf-8 -*-
"""E2E 验证工件 md → e2e.html(挂 nautilus.social,与 pipeline.html 互链)。"""
import re
import sys
from datetime import datetime
from pathlib import Path

import markdown

CORE = Path(r"C:/Users/chunx/Projects/nautilus-core")
SRC = Path(r"C:/Users/chunx/nautilus-v5/vtf/_pipeline/PIPELINE_E2E_VERIFY_LATEST.md")
OUT = CORE / "docs" / "web" / "e2e.html"
TPL = Path(r"C:/Users/chunx/Projects/nautilus-core/docs/web/build_web_docs.py").read_text(encoding="utf-8")
tpl = re.search(r'TPL = """(.*?)"""', TPL, re.S).group(1)

md = SRC.read_text(encoding="utf-8")
body = markdown.markdown(md, extensions=["tables"])
html = tpl.format(title="Nautilus 数据飞轮 · E2E 逐单验证台",
                  subtitle="涡轮增压五段链 · 每单实证 · DB 实态生成(非叙事) · 数据源 GET /api/platform/org/pipeline/e2e",
                  toc="", body=body, stamp=datetime.now().strftime("%F %T"),
                  source="vtf/_pipeline/PIPELINE_E2E_VERIFY_LATEST.md")
OUT.write_text(html, encoding="utf-8")
print(f"{OUT} {len(html)//1024}KB")
