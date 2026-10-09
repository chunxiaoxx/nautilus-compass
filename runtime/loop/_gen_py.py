#!/usr/bin/env python3
"""gen.py - generate the Corpus Hub static site (hub.xerj.org) from the registry.

Reads ONLY registry state on this branch (corpus-hub):
  tools/xerj-code/hub/*.json                 - manifests (lane A)
  tools/xerj-code/hub/backlog/backlog-100.json - categories/status/use-cases/tags
  tools/xerj-code/hub/WAVES.md               - G7 scores per wave
  tools/xerj-code/hub/backlog/*-graded.json  - graded G7 suites (non-IT lane)
  tools/xerj-code/hub/backlog/impact-snapshot-*.json - benchmark A/B snapshot
  tools/packs/*/recipe.toml                  - lane B packs
Writes out/ (index, per-corpus, per-category, about, style, data.json).

Design: xerj.org brandbook, day palette only (user directive 2026-10-06:
strictly main-site fonts and CSS, domains as large typography, white default).
Copy: plain short sentences, no em-dashes, no filler intros (user directive
2026-10-06). Stdlib only; deterministic; no network. Rerun + redeploy on
registry change.
"""
import datetime as dt
import html
import json
import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[2]
HUB = ROOT / "tools" / "xerj-code" / "hub"
PACKS = ROOT / "tools" / "packs"
OUT = pathlib.Path(__file__).resolve().parent / "out"

CATS = {
    "SEC": ("Security advisories and identifiers", "Is this CVE exploited in the wild; does this pattern have KEV or GHSA precedent"),
    "STD": ("Standards, specs and regulations", "What RFC 9105 / SP 800-88 / 29 CFR 1910.28 actually says"),
    "OPS": ("Production and incident knowledge", "How real teams handled this; what caused outages like this one"),
    "GOOD": ("Design guidance and exemplars", "What a reviewed, idiomatic implementation looks like"),
    "BAD": ("Failure precedent", "Real vulnerable functions and the fix that closed them"),
    "DATA": ("Data engines, reference source", "How duckdb, rocksdb, sqlite actually do planner, LSM, B+-tree"),
    "NET": ("Net, crypto, serialisation source", "How quinn, rustls, zstd actually do handshake, compression, framing"),
}

STATUSES = {"live": ("live", "ok"), "candidate": ("candidate", "warn"), "planned": ("planned", "mute"),
            "deferred": ("deferred", "warn"), "killed": ("killed", "bad"), "withdrawn": ("withdrawn", "bad")}

STAMP = "2026-10-06"


def plain(s):
    """No em/en dashes in generated copy (user directive 2026-10-06).
    Registry text keeps its bytes; rendering normalizes."""
    s = str(s)
    s = s.replace(" — ", ": ").replace(" —", ":").replace("— ", ":")
    s = s.replace("—", "-")
    s = s.replace(" – ", ": ").replace("–", "-")
    return s


def esc(s):
    return html.escape(plain(s), quote=True)


def human_bytes(n):
    if not n:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def human_files(n):
    return f"{n:,} files" if n else "0 files"


def parse_waves_g7():
    """WAVES.md G7 tables -> {corpus: {median, verdict, wave}}"""
    scores = {}
    text = (HUB / "WAVES.md").read_text()
    for m in re.finditer(r"^## (Wave [^-\n]+).*?\n(.*?)(?=^## |\Z)", text, re.M | re.S):
        wave = m.group(1).strip()
        for line in m.group(2).splitlines():
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) >= 3 and c[0] and not c[0].startswith(("-", "corpus")):
                try:
                    median = float(c[1].split()[0])
                except (ValueError, IndexError):
                    continue
                verdict = "pass" if "pass" in c[2] else c[2] or "n/a"
                scores.setdefault(c[0], {"median": median, "verdict": verdict, "wave": wave})
    return scores


def suite_median(queries):
    """Relevant count of 5, computed when a suite carries no median.
    pass/relevant = 1, partial = 0.5; suite-defect queries are excluded
    from numerator and denominator both."""
    num = {"pass": 1.0, "relevant": 1.0, "partial": 0.5}
    got = [num.get(q.get("verdict") or q.get("grade"), 0.0)
           for q in queries
           if "excluded" not in str(q.get("verdict") or q.get("grade"))]
    if not got:
        return 0.0
    return sum(got) / len(got) * 5.0


def parse_graded_suites():
    """backlog/*graded*.json -> {corpus: {queries:[...], median}}"""
    out = {}
    for p in sorted((HUB / "backlog").glob("*graded*.json")):
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        for slug, suite in data.get("graded", data.get("suites", data.get("corpora", {}))).items():
            if isinstance(suite, dict) and "queries" in suite:
                if "median" not in suite or suite["median"] is None:
                    suite["median"] = suite_median(suite["queries"])
                out[slug] = suite
    return out


def load_impact():
    snaps = sorted((HUB / "backlog").glob("impact-snapshot-*.json"))
    if not snaps:
        return {}, None
    data = json.loads(snaps[-1].read_text())
    return {r["corpus"]: r for r in data.get("rows", [])}, data.get("provenance", {})


def load_registry():
    backlog = json.loads((HUB / "backlog" / "backlog-100.json").read_text())
    rows = {r["slug"]: r for r in backlog["corpora"]}
    corpora = []
    # lane A manifests
    for p in sorted(HUB.glob("*.json")):
        if p.stem in ("TEMPLATE", "corpus-schema"):
            continue
        m = json.loads(p.read_text())
        slug = m["corpus"]
        row = rows.get(slug, {})
        corpora.append({
            "slug": slug, "lane": "A", "cat": row.get("cat", "?"),
            "status": row.get("status", "unknown"), "refresh": row.get("refresh", "pinned"),
            "usecase": row.get("domain", ""), "repos": m.get("repos", []),
            "added": m.get("cloned_at", ""), "kind": "reference corpus",
            "consumed": rows.get(slug, {}).get("sources", [{}])[0].get("url", ""),
            "tags": row.get("tags", {}), "merged_into": row.get("merged_into", ""),
        })
    # lane B recipes
    for p in sorted(PACKS.glob("*/recipe.toml")):
        if p.parent.name == "TEMPLATE-recipe":
            continue
        r = tomllib.loads(p.read_text())
        meta = r.get("recipe", {})
        slug = p.parent.name
        row = rows.get(slug, {})
        corpora.append({
            "slug": slug, "lane": "B", "cat": row.get("cat", "?"),
            "status": row.get("status", "unknown"), "refresh": row.get("refresh", "weekly"),
            "usecase": row.get("domain", ""), "repos": [],
            "sources": r.get("sources", []), "added": "", "kind": "curated pack",
            "consumed": meta.get("notes", "") or row.get("sources", [{}])[0].get("url", ""),
            "tags": row.get("tags", {}), "merged_into": row.get("merged_into", ""),
        })
    # backlog-only rows (planned/deferred/candidates with no manifest yet)
    have = {c["slug"] for c in corpora}
    for slug, row in rows.items():
        if slug not in have:
            corpora.append({
                "slug": slug, "lane": row.get("lane", "?"), "cat": row.get("cat", "?"),
                "status": row.get("status", "?"), "refresh": row.get("refresh", ""),
                "usecase": row.get("domain", ""), "repos": [], "sources": row.get("sources", []),
                "added": "", "kind": "backlog row", "consumed": row.get("sources", [{}])[0].get("url", ""),
                "tags": row.get("tags", {}), "merged_into": row.get("merged_into", ""),
            })
    return sorted(corpora, key=lambda c: c["slug"])


def corpus_stats(c):
    files = sum(r.get("files") or 0 for r in c["repos"])
    nbytes = sum(r.get("bytes") or 0 for r in c["repos"])
    licences = sorted({r["review"]["spdx"] for r in c["repos"] if r.get("review")})
    if not licences:
        licences = sorted({s.get("licence", "?") for s in c.get("sources", [])[:1]})
    return files, nbytes, licences


def region(c):
    return (c.get("tags") or {}).get("region", "")


def tag_line(c):
    """Card tag line: REGION · TOPIC · TOPIC (subtopics in the tooltip)."""
    t = c.get("tags") or {}
    parts = []
    if t.get("region"):
        parts.append(t["region"].upper())
    for x in t.get("topics", [])[:2]:
        parts.append(x.upper())
    sub = t.get("subtopics", [])
    tip = ", ".join(sub) if sub else ""
    if not parts:
        return ""
    return f'<span class="ctags" title="{esc(tip)}">{esc(" · ".join(parts))}</span>'


def g7_badge(slug, g7, graded):
    if slug in graded:
        med = graded[slug].get("median") or 0.0
        cls = "ok" if med >= 3 else "bad"
        return f'<span class="badge g7 {cls}" title="retrieval spot-check, relevant of 5 queries">G7 {med:.1f}/5</span>'
    if slug in g7:
        g = g7[slug]
        cls = "ok" if g["verdict"] == "pass" else "bad"
        tip = esc(g["wave"])
        return f'<span class="badge g7 {cls}" title="retrieval spot-check ({tip})">G7 {g["median"]:.1f}/5</span>'
    return '<span class="badge g7 mute" title="not yet spot-checked">G7 n/a</span>'


def impact_badge(c, impact):
    r = impact.get(c["slug"])
    if not r or r.get("status") != "measured":
        return ""
    return (f'<span class="badge imp" title="drift-anchored agent A/B: bare pass then corpus pass">'
            f'A/B {esc(r["p"])} to {esc(r["x"])}</span>')


def card(c, g7, graded, impact):
    files, nbytes, licences = corpus_stats(c)
    st, stcls = STATUSES.get(c["status"], (c["status"], "mute"))
    return f'''<a class="card" data-cat="{esc(c['cat'])}" data-region="{esc(region(c))}" href="corpus/{esc(c['slug'])}.html">
  <div class="chead"><span class="cname">{esc(c['slug'])}</span><span class="dot {stcls}"></span></div>
  <p class="cuse">{esc(plain(c['usecase'])[:180])}{'...' if len(c['usecase']) > 180 else ''}</p>
  {tag_line(c)}
  <div class="cmeta">{'<span>merged into ' + esc(c['merged_into']) + '</span>' if c.get('merged_into') else '<span>' + human_bytes(nbytes) + '</span><span>' + human_files(files) + '</span>'}<span>{st}</span></div>
  <div class="cbadges"><span class="badge cat">{esc(c['cat'])}</span><span class="badge lane">{esc(c['lane'])}</span>{g7_badge(c['slug'], g7, graded)}{impact_badge(c, impact)}</div>
</a>'''


# Brandbook tokens from xerj.org (landing/style.css), day palette only.
# White schema is the one scheme: no dark variant, no prefers-color-scheme
# override (user directive 2026-10-06).
STYLE = """/* corpus hub - xerj.org brandbook, day palette, white only */
:root{
--z-bg:#f6f4ee;--z-ink:#11120f;--z-mute:#696762;--z-faint:#e3dfd4;--z-line:#cfcbbf;
--z-accent:#7f5200;--z-cmp:#6f8aa8;
--ok:#2e6b3a;--bad:#8c2f2f;--warn:#8a6d1a;
--font-display:'Big Shoulders Display','Inter',system-ui,sans-serif;
--font-prose:'Inter',system-ui,sans-serif;
--font-data:'IBM Plex Sans','Inter',system-ui,sans-serif;
--font-mono:'JetBrains Mono','IBM Plex Mono',monospace;
--fs-11:11px;--fs-13:13px;--fs-16:16px;--fs-20:20px;--fs-32:32px;
--fs-56:56px;--fs-96:96px;--fs-160:160px;
--track-ui:.14em;--track-label:.08em;
--sp-1:4px;--sp-2:8px;--sp-3:12px;--sp-4:16px;--sp-5:20px;--sp-6:24px;
--sp-8:32px;--sp-10:48px;--sp-12:64px;--sp-16:96px;
--page-x:64px;--max-w:1680px;
}
*{box-sizing:border-box}
body{margin:0;font-family:var(--font-prose);background:var(--z-bg);color:var(--z-ink);
line-height:1.5;font-size:var(--fs-16)}
a{color:inherit}
code{font-family:var(--font-mono);font-size:.92em;background:var(--z-faint);padding:.1em .35em}
/* nav: main-site pattern, 1px bottom line */
.nav{display:flex;align-items:baseline;gap:var(--sp-5);padding:var(--sp-4) var(--page-x);
border-bottom:1px solid var(--z-line);font-family:var(--font-data);font-size:var(--fs-11);
font-weight:600;text-transform:uppercase;letter-spacing:var(--track-ui);flex-wrap:wrap}
.nav .brand{font-family:var(--font-display);font-weight:900;font-size:var(--fs-16);
letter-spacing:.24em;color:var(--z-ink);text-decoration:none}
.nav .brand b{color:var(--z-accent)}
.nav a{color:var(--z-mute);text-decoration:none}
.nav a:hover{color:var(--z-ink)}
.nav .spacer{flex:1}
main{max-width:var(--max-w);margin:0 auto;padding:var(--sp-8) var(--page-x) var(--sp-16)}
/* type */
.kicker{font-family:var(--font-data);font-size:var(--fs-11);font-weight:500;
letter-spacing:var(--track-ui);text-transform:uppercase;color:var(--z-mute)}
.kicker .accent{color:var(--z-accent)}
.kicker .dash{opacity:.4;margin:0 6px}
h1.hero{font-family:var(--font-display);font-weight:900;font-size:clamp(64px,10vw,var(--fs-160));
line-height:.88;letter-spacing:-.02em;margin:0 0 var(--sp-8);color:var(--z-ink)}
h1.hero .accent{color:var(--z-accent)}
h2.scene{font-family:var(--font-display);font-weight:900;font-size:var(--fs-56);
line-height:.95;letter-spacing:-.005em;margin:0 0 var(--sp-6)}
p.lead{font-family:var(--font-prose);color:var(--z-mute);font-size:var(--fs-20);
line-height:1.5;max-width:56ch}
.note{color:var(--z-mute);font-size:var(--fs-13)}
/* hero stats: display numerals, 1px rules */
.stats{display:flex;flex-wrap:wrap;border-block:1px solid var(--z-line);margin:var(--sp-8) 0}
.stats>div{padding:var(--sp-4) var(--sp-8) var(--sp-4) 0;margin-right:var(--sp-8);
border-right:1px solid var(--z-line)}
.stats>div:last-child{border-right:0;margin-right:0}
.stats b{display:block;font-family:var(--font-display);font-weight:800;font-size:var(--fs-56);
line-height:1;color:var(--z-ink)}
.stats span{font-family:var(--font-data);font-size:var(--fs-11);font-weight:500;
text-transform:uppercase;letter-spacing:var(--track-ui);color:var(--z-mute)}
/* domains: the front page centrepiece, giant display words */
.domains{margin:var(--sp-8) 0}
.domain{display:grid;grid-template-columns:110px 1fr auto 40px;align-items:center;gap:var(--sp-6);
padding:var(--sp-5) 0;border-top:1px solid var(--z-line);text-decoration:none}
.domain:last-child{border-bottom:1px solid var(--z-line)}
.domain .dcount{font-family:var(--font-mono);font-size:var(--fs-20);color:var(--z-mute)}
.domain .dcount b{color:var(--z-ink);font-weight:700}
.domain .dword{font-family:var(--font-display);font-weight:900;
font-size:clamp(40px,6vw,var(--fs-96));line-height:.92;letter-spacing:-.01em;
color:var(--z-ink);text-transform:uppercase}
.domain .dinfo{text-align:right;max-width:46ch}
.domain .dinfo b{display:block;font-family:var(--font-data);font-size:var(--fs-13);
font-weight:600;text-transform:uppercase;letter-spacing:var(--track-label);color:var(--z-ink)}
.domain .dinfo span{font-family:var(--font-prose);font-size:var(--fs-13);color:var(--z-mute)}
.domain .dgo{font-family:var(--font-mono);font-size:var(--fs-20);color:var(--z-mute)}
.domain:hover .dword{color:var(--z-accent)}
.domain:hover .dgo{color:var(--z-accent)}
/* toolbar: square 1px inputs and chips, no radius */
.toolbar{display:flex;flex-direction:column;gap:var(--sp-3);margin:var(--sp-8) 0 var(--sp-4)}
.toolbar .row{display:flex;gap:var(--sp-2);flex-wrap:wrap;align-items:center}
.toolbar input{font-family:var(--font-prose);font-size:var(--fs-13);padding:.5em .8em;
border:1px solid var(--z-line);background:transparent;color:var(--z-ink);min-width:22rem}
.toolbar input:focus{outline:none;border-color:var(--z-accent)}
.chip{font-family:var(--font-data);font-size:var(--fs-11);font-weight:500;
text-transform:uppercase;letter-spacing:var(--track-label);border:1px solid var(--z-line);
background:transparent;color:var(--z-mute);padding:.35em .9em;cursor:pointer}
.chip:hover{border-color:var(--z-ink);color:var(--z-ink)}
.chip.on{background:var(--z-ink);color:var(--z-bg);border-color:var(--z-ink)}
/* cards: 1px square, no radius, no shadow */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:1px;
background:var(--z-line);border:1px solid var(--z-line);margin-top:var(--sp-4)}
.card{display:flex;flex-direction:column;gap:var(--sp-2);text-decoration:none;
background:var(--z-bg);padding:var(--sp-4)}
.card:hover{background:var(--z-faint)}
.chead{display:flex;justify-content:space-between;align-items:center}
.cname{font-family:var(--font-mono);font-weight:600;font-size:var(--fs-13)}
.dot{width:.65em;height:.65em;border-radius:50%;display:inline-block}
.dot.ok{background:var(--ok)}.dot.warn{background:var(--warn)}
.dot.bad{background:var(--bad)}.dot.mute{background:var(--z-mute)}
.cuse{color:var(--z-mute);font-size:var(--fs-13);margin:0;min-height:2.8em}
.ctags{font-family:var(--font-mono);font-size:var(--fs-11);letter-spacing:var(--track-label);
color:var(--z-accent)}
.cmeta{display:flex;gap:var(--sp-4);color:var(--z-mute);font-size:var(--fs-11);
font-family:var(--font-mono)}
.cbadges{display:flex;gap:var(--sp-1);flex-wrap:wrap}
.badge{font-family:var(--font-mono);font-size:var(--fs-11);border:1px solid var(--z-line);
padding:.1em .5em;color:var(--z-mute)}
.badge.cat{color:var(--z-accent);border-color:var(--z-accent)}
.badge.g7.ok,.badge.imp{color:var(--ok);border-color:var(--ok)}
.badge.g7.bad{color:var(--bad);border-color:var(--bad)}
.badge.g7.mute{opacity:.6}
/* detail pages */
section.detail h2{font-family:var(--font-display);font-weight:700;font-size:var(--fs-32);
line-height:.95;border-bottom:1px solid var(--z-line);padding-bottom:var(--sp-2);margin:var(--sp-10) 0 var(--sp-4)}
table{border-collapse:collapse;width:100%;font-size:var(--fs-13);font-family:var(--font-prose)}
th,td{text-align:left;padding:.45em .6em;border-bottom:1px solid var(--z-line);vertical-align:top}
th{color:var(--z-mute);font-weight:600;font-family:var(--font-data);font-size:var(--fs-11);
text-transform:uppercase;letter-spacing:var(--track-label)}
td.mono{font-family:var(--font-mono);font-size:var(--fs-13)}
.kbox{border:1px solid var(--z-line);padding:var(--sp-4) var(--sp-5);margin:var(--sp-4) 0}
.g7q{margin:var(--sp-3) 0;padding:var(--sp-3) var(--sp-4);border-left:3px solid var(--z-line)}
.g7q.pass{border-color:var(--ok)}.g7q.fail{border-color:var(--bad)}
.backlink{font-family:var(--font-mono);font-size:var(--fs-13);color:var(--z-mute);text-decoration:none}
.backlink:hover{color:var(--z-ink)}
h1.slug{font-family:var(--font-mono);font-size:var(--fs-32);font-weight:700;margin:var(--sp-4) 0 0}
/* footer: main-site pattern */
footer{border-top:1px solid var(--z-line);color:var(--z-mute);padding:var(--sp-5) var(--page-x);
font-family:var(--font-data);font-size:var(--fs-11);font-weight:500;text-transform:uppercase;
letter-spacing:var(--track-ui);display:flex;gap:var(--sp-8);flex-wrap:wrap}
footer a{color:var(--z-mute);text-decoration:none}
footer a:hover{color:var(--z-ink)}
@media (max-width:900px){
:root{--page-x:18px;--sp-12:40px;--sp-16:56px}
.toolbar input{min-width:100%}
.domain{grid-template-columns:1fr;gap:var(--sp-2)}
.domain .dinfo{text-align:left;max-width:none}
.stats>div{border-right:0;margin-right:0;padding-right:0;width:50%}
}
"""

FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@400;700;800;900&family=Inter:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">"""

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}">
{fonts}
<link rel="stylesheet" href="{rel}assets/style.css"></head>
<body><nav class="nav"><a class="brand" href="https://xerj.org">XERJ<b>·</b>HUB</a>
<a href="{rel}index.html">CORPORA</a><a href="{rel}index.html#domains">DOMAINS</a>
<a href="{rel}about.html">ABOUT</a>
<a href="https://github.com/xerj-org/xerj/tree/corpus-hub/tools/xerj-code/hub">REGISTRY (GIT)</a>
<span class="spacer"></span><a href="https://xerj.org">XERJ.ORG</a></nav>
{body}
<footer><span>XERJ · CORPUS HUB · {stamp}</span>
<span>PINNED SOURCES · VERIFIED LICENCES · MEASURED RETRIEVAL</span>
<span><a href="{rel}index.html">CORPORA</a> · <a href="{rel}about.html">ABOUT</a> ·
<a href="{rel}llms.txt">LLMS.TXT</a></span></footer>
</body></html>"""


def page(title, desc, body, rel=""):
    return PAGE.format(title=esc(title), desc=esc(desc), body=body, rel=rel,
                       fonts=FONTS, stamp=STAMP)


FILTER_JS = """<script>
var cards=[...document.querySelectorAll('.card')];
var st={q:'',cat:'',region:''};
function apply(){
  cards.forEach(function(c){
    var ok=true;
    if(st.q&&c.textContent.toLowerCase().indexOf(st.q)<0)ok=false;
    if(st.cat&&c.dataset.cat!==st.cat)ok=false;
    if(st.region&&c.dataset.region!==st.region)ok=false;
    c.style.display=ok?'':'none';
  });
  var n=0;cards.forEach(function(c){if(c.style.display!=='none')n++;});
  var el=document.getElementById('count');
  if(el)el.textContent=n+' of '+cards.length+' shown';
}
document.getElementById('q').addEventListener('input',function(e){
  st.q=e.target.value.toLowerCase();apply();
});
document.querySelectorAll('.chip[data-cat]').forEach(function(b){
  b.addEventListener('click',function(){
    var on=b.classList.contains('on');
    document.querySelectorAll('.chip[data-cat]').forEach(function(x){x.classList.remove('on');});
    if(!on)b.classList.add('on');
    st.cat=on?'':b.dataset.cat;apply();
  });
});
document.querySelectorAll('.chip[data-region]').forEach(function(b){
  b.addEventListener('click',function(){
    var on=b.classList.contains('on');
    document.querySelectorAll('.chip[data-region]').forEach(function(x){x.classList.remove('on');});
    if(!on)b.classList.add('on');
    st.region=on?'':b.dataset.region;apply();
  });
});
</script>"""


def render_index(corpora, g7, graded, impact, prov):
    live = [c for c in corpora if c["status"] == "live"]
    total_bytes = sum(sum(r.get("bytes") or 0 for r in c["repos"]) for c in live)
    n_imp = sum(1 for c in live if impact.get(c["slug"], {}).get("status") == "measured")
    regions = sorted({region(c) for c in corpora if region(c)} - {""}, key=lambda r: (r == "GLOBAL", r))
    cards = "\n".join(card(c, g7, graded, impact) for c in corpora)
    dom_rows = []
    for k, (title, what) in CATS.items():
        cs = [c for c in corpora if c["cat"] == k]
        n_live = sum(1 for c in cs if c["status"] == "live")
        more = f" + {len(cs) - n_live} more" if len(cs) > n_live else ""
        dom_rows.append(f'''<a class="domain" href="category/{k}.html">
<span class="dcount"><b>{n_live}</b>{esc(more)}</span>
<span class="dword">{esc(k)}</span>
<span class="dinfo"><b>{esc(title)}</b><span>{esc(what)}</span></span>
<span class="dgo">&rarr;</span>
</a>''')
    domains = "\n".join(dom_rows)
    cat_chips = "".join(f'<button class="chip" data-cat="{k}">{k}</button>' for k in CATS)
    region_chips = "".join(f'<button class="chip" data-region="{esc(r)}">{esc(r)}</button>' for r in regions)
    body = f'''<main>
<div class="kicker"><span class="accent">HUB.XERJ.ORG</span><span class="dash">·</span><span>REFERENCE MEMORY FOR AI AGENTS</span></div>
<h1 class="hero">REFERENCE<br>MEMORY FOR<br><span class="accent">AI AGENTS</span></h1>
<p class="lead">An agent with the right text at hand beats an agent guessing from memory.
Each corpus here is a pinned, licence-checked slice of one domain that the agent
downloads per task and searches in seconds. No waiting for the next model
retrain. No fighting website blocks and rate limits. Every corpus names its
sources, its pins, its licence verdict, and what the retrieval tests scored.</p>
<div class="stats">
<div><b>{len(live)}</b><span>live corpora</span></div>
<div><b>{len(CATS)}</b><span>domains</span></div>
<div><b>{len(corpora)}</b><span>registry rows</span></div>
<div><b>{human_bytes(total_bytes)}</b><span>pinned text</span></div>
<div><b>{n_imp}</b><span>with agent A/B results</span></div>
</div>
<section class="domains" id="domains">
<div class="kicker"><span class="accent">01</span><span class="dash">·</span><span>DOMAINS</span></div>
{domains}
</section>
<div class="kicker"><span class="accent">02</span><span class="dash">·</span><span>ALL CORPORA</span> <span id="count" style="text-transform:none"></span></div>
<div class="toolbar">
<div class="row"><input id="q" type="search" placeholder="filter by name, topic, use-case, licence"></div>
<div class="row"><span class="kicker">DOMAIN</span><button class="chip on" data-cat=""></button>{cat_chips}</div>
<div class="row"><span class="kicker">REGION</span>{region_chips}</div>
</div>
<div class="grid" id="grid">{cards}</div>
</main>
{FILTER_JS}'''
    return page("XERJ Corpus Hub: reference memory for AI agents",
                "Pinned, licence-checked, measured corpora an agent downloads per task and searches instead of guessing",
                body)


def detail_body(c, g7, graded, impact, prov):
    files, nbytes, licences = corpus_stats(c)
    st, stcls = STATUSES.get(c["status"], (c["status"], "mute"))
    cat_desc = CATS.get(c["cat"], ("", ""))
    t = c.get("tags") or {}
    tags_txt = " · ".join(([t["region"].upper()] if t.get("region") else [])
                          + [x.upper() for x in t.get("topics", [])]
                          + [x.upper() for x in t.get("subtopics", [])]) or "none"
    rows = []
    for r in c["repos"]:
        rv = r.get("review", {})
        rows.append(f'''<tr><td class="mono"><a href="{esc(r.get('url',''))}">{esc(r.get('repo',''))}</a></td>
<td class="mono">{esc(r.get('sha','')[:12])}</td><td>{esc(rv.get('spdx','?'))}</td>
<td class="mono">{human_bytes(r.get('bytes'))} / {human_files(r.get('files'))}</td>
<td class="note">{esc(plain(rv.get('note',''))[:400])}</td></tr>''')
    for s in c.get("sources", []):
        rows.append(f'''<tr><td class="mono"><a href="{esc(s.get('url',''))}">{esc(s.get('slug', s.get('url','')))}</a></td>
<td class="mono">recipe</td><td>{esc(s.get('licence','?'))}</td><td class="mono">curated pack</td>
<td class="note">{esc(plain(s.get('licence_hint',''))[:400])}</td></tr>''')
    g = graded.get(c["slug"])
    if g:
        qs = "\n".join(f'''<div class="g7q {'pass' if (q.get('verdict') or q.get('grade')) in ('relevant','partial','pass') else 'fail'}">
<b>Q:</b> {esc(q['q'])}<br><b>expect:</b> <span class="note">{esc(q.get('expect',''))}</span><br>
<b>top-5:</b> <span class="note mono">{esc(' / '.join(q.get('top5', [])[:5]))}</span><br>
<b>grade:</b> {esc(str(q.get('verdict') or q.get('grade','')))}</div>''' for q in g["queries"])
        g7sec = f'<section class="detail" id="g7"><h2>Retrieval spot-check (G7)</h2><p class="note">{g.get("median","?")}/5 relevant. Graded {esc(g.get("graded_at",""))}.</p>{qs}</section>'
    elif c["slug"] in g7:
        e = g7[c["slug"]]
        g7sec = f'''<section class="detail" id="g7"><h2>Retrieval spot-check (G7)</h2>
<p><b>{e["median"]:.1f}/5</b> median relevant ({esc(e["wave"])} stratified sample). Verdict: <b>{esc(e["verdict"])}</b>.</p></section>'''
    else:
        g7sec = '''<section class="detail" id="g7"><h2>Retrieval spot-check (G7)</h2>
<p class="note">Not yet spot-checked. Queries are pre-registered in the registry before grading.</p></section>'''
    imp = impact.get(c["slug"])
    if imp and imp.get("status") == "measured":
        impsec = f'''<section class="detail" id="ab"><h2>Agent A/B (drift-anchored)</h2>
<table><tr><th>arm</th><th>score</th><th>drift tasks</th></tr>
<tr><td>bare (offline, honest-unknown)</td><td class="mono">{esc(imp["p"])}</td><td class="mono">{esc(imp.get("dp","n/a"))}</td></tr>
<tr><td>with this corpus</td><td class="mono">{esc(imp["x"])}</td><td class="mono">{esc(imp.get("dx","n/a"))}</td></tr></table>
<p class="note">snapshot {esc(prov.get("date",""))} from <code>{esc(prov.get("branch",""))}</code>; protocol: benchmarks/corpus-tasks/PROTOCOL.md</p></section>'''
    else:
        impsec = ""
    return f'''<main>
<p><a class="backlink" href="../index.html">&larr; all corpora</a></p>
<h1 class="slug">{esc(c['slug'])} <span class="dot {stcls}"></span></h1>
<p class="note">{esc(c['kind'])} · status <b>{st}</b> · domain <b>{esc(c['cat'])}</b> ({esc(cat_desc[0])}) · lane {esc(c['lane'])} · refresh {esc(c['refresh'])} · tags <b>{esc(tags_txt)}</b></p>
<section class="detail"><h2>What an agent uses it for</h2><p>{esc(c['usecase'] or 'n/a')}</p></section>
{f'<div class="kbox"><b>Withdrawn</b><br>Merged into <a href="{esc(c["merged_into"])}.html"><code>{esc(c["merged_into"])}</code></a>. Use that corpus.</div>' if c.get('merged_into') else f'<div class="kbox"><b>Use it</b><br><code>xerj corpus add --from https://raw.githubusercontent.com/xerj-org/xerj/corpus-hub/tools/xerj-code/hub/{esc(c["slug"])}.json</code><br><code>xerj corpus index {esc(c["slug"])}</code> then <code>xerj code {esc(c["slug"])} "your question"</code></div>'}
<section class="detail"><h2>Sources and pins</h2><table>
<tr><th>source</th><th>pin</th><th>licence</th><th>size</th><th>review note</th></tr>{''.join(rows)}</table>
<p class="note">{human_bytes(nbytes)} across {human_files(files)}. Added {esc(c['added'][:10] or 'n/a')}.</p></section>
<section class="detail"><h2>Rights</h2><p>{esc(' + '.join(licences) or '?')}.
{esc('Redistribution permitted with attribution per the licence review' if any(r.get('review',{}).get('use')=='adapt-with-attribution' for r in c['repos']) else 'See per-source review blocks')}.
The review block records a human opening each licence file at the pin. Detector output is a hint, never the verdict.</p></section>
{g7sec}{impsec}
</main>'''


def category_body(k, cs, g7, graded, impact):
    title, what = CATS[k]
    cards = "\n".join(card(c, g7, graded, impact) for c in cs)
    n_live = sum(1 for c in cs if c["status"] == "live")
    return f'''<main>
<p><a class="backlink" href="../index.html">&larr; all domains</a></p>
<div class="kicker"><span class="accent">{esc(k)}</span><span class="dash">·</span><span>DOMAIN</span></div>
<h1 class="hero" style="font-size:clamp(56px,9vw,var(--fs-160))">{esc(k)}</h1>
<p class="lead">{esc(title)}. Agent asks: {esc(what)}. {n_live} live of {len(cs)} entries.</p>
<div class="grid">{cards}</div>
</main>'''


ABOUT = '''<main>
<div class="kicker"><span class="accent">ABOUT</span><span class="dash">·</span><span>THE HUB IN ONE PAGE</span></div>
<h1 class="hero" style="font-size:clamp(48px,7vw,120px)">WHY A<br><span class="accent">CORPUS HUB</span></h1>
<p class="lead">Agents answer from memory, and memory is stale, generic, or wrong on exactly
the questions that matter: what the regulation says at this pin, whether this CVE is
exploited, how this engine actually implements it. A corpus fixes that. The agent
downloads the domain it needs, searches it, and cites what it found. This hub is the
registry of those corpora: pinned, licence-checked, and measured.</p>
<section class="detail"><h2>Every corpus passes seven gates</h2>
<table>
<tr><th>gate</th><th>what satisfies it</th></tr>
<tr><td>G1 domain</td><td>the row finishes "an agent working on ___ would query this for ___" in one specific sentence</td></tr>
<tr><td>G2 shape</td><td>the retrieval unit matches the question: clause-level sections for standards, function bodies for code, advisory records for precedent</td></tr>
<tr><td>G3 un-memorisation</td><td>answer-bearing content is niche, internal, post-cutoff, or too detailed for recall. Famous-and-small is killed as retrieval theatre</td></tr>
<tr><td>G4 licence</td><td>a human opened the licence at the pin and wrote the review block. Detector output is a hint, never the verdict</td></tr>
<tr><td>G5 pin truth</td><td>manifest SHA equals the commit the build used. Rewrites are withdrawals, not re-pins</td></tr>
<tr><td>G6 registry validation</td><td>validate_hub.py green in CI on the corpus-hub branch</td></tr>
<tr><td>G7 retrieval spot-check</td><td>5 pre-registered domain queries, top-5 graded manually, median 3 or more relevant to pass</td></tr>
</table></section>
<section class="detail"><h2>Scores on the cards</h2>
<p><b>G7</b> is the retrieval spot-check above. <b>A/B</b> is the drift-anchored agent
benchmark: the same task run bare (offline, instructed to answer honestly rather than
fabricate) and with the corpus. The badge shows pass counts, bare then corpus.
A tie is a publishable outcome; the registry records it either way.</p></section>
<section class="detail"><h2>Tags</h2>
<p>Every corpus carries a region (US, UK, DE, EU, or GLOBAL) and topics. Filter the
front page by domain and region; free-text search covers topics and subtopics.</p></section>
<section class="detail"><h2>Rights policy</h2>
<p>Per-source licence verdicts live in each manifest's review block. PD (US government
works), OGL v3.0 (UK), and permissive licences ship as <code>adapt-with-attribution</code>.
GPL, AGPL, SSPL, and other restrictive sources are <code>approach-only</code>: readable
as design evidence, never copied. Closed families (ICC I-codes, Eurocodes, NEC, ASTM,
ISO, DIN) are documented as closed and excluded.</p></section>
<section class="detail"><h2>Contribute</h2>
<p>The registry is a git branch: <a href="https://github.com/xerj-org/xerj/tree/corpus-hub">corpus-hub</a>.
Read <a href="https://github.com/xerj-org/xerj/blob/corpus-hub/tools/xerj-code/hub/CONTRIBUTING.md">CONTRIBUTING.md</a>
and the program doc (PROGRAM-100.md). This site is generated from the registry by
<code>tools/corpus-hub-site/gen.py</code>. No hand-written corpus pages, ever.</p></section>
</main>'''


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "corpus").mkdir(exist_ok=True)
    (OUT / "category").mkdir(exist_ok=True)
    (OUT / "assets" / "style.css").write_text(STYLE)
    corpora = load_registry()
    g7 = parse_waves_g7()
    graded = parse_graded_suites()
    impact, prov = load_impact()
    (OUT / "index.html").write_text(render_index(corpora, g7, graded, impact, prov))
    for c in corpora:
        (OUT / "corpus" / f"{c['slug']}.html").write_text(
            page(f"{c['slug']}: XERJ Corpus Hub", c["usecase"][:150], detail_body(c, g7, graded, impact, prov), rel="../"))
    for k, (title, what) in CATS.items():
        cs = [c for c in corpora if c["cat"] == k]
        (OUT / "category" / f"{k}.html").write_text(
            page(f"{k}: {title} domain", what, category_body(k, cs, g7, graded, impact), rel="../"))
    (OUT / "about.html").write_text(page("About: XERJ Corpus Hub", "How corpora are gated, scored, tagged, and licenced", ABOUT, rel=""))
    # llms.txt - agent-facing index of the registry, generated like everything
    # else. Short first screen (study rule 7), no obligation language, every
    # step verifiable; one line per live corpus.
    live = [c for c in corpora if c["status"] == "live"]
    imp2, _ = load_impact()
    lines = [
        "# XERJ Corpus Hub",
        "",
        "> Reference memory for AI agents: pinned, licence-checked, measured",
        f"> corpora an agent downloads per task and searches instead of guessing",
        f"> from memory or fighting web blocks. {len(live)} live corpora.",
        "> Registry of record (wins on any conflict with this generated file):",
        "> https://github.com/xerj-org/xerj/tree/corpus-hub/tools/xerj-code/hub",
        f"> Last updated: {STAMP}.",
        "",
        "Consume any corpus (no build step, the binary indexes from the manifest):",
        "",
        "    xerj corpus add --from https://raw.githubusercontent.com/xerj-org/xerj/corpus-hub/tools/xerj-code/hub/<slug>.json",
        "    xerj corpus index <slug>",
        '    xerj code <slug> "your question"',
        "",
        "Retrieval is lexical-by-default. Scores are measured, never asserted:",
        "G7 = 5 pre-registered queries graded on top-5; A/B = drift-anchored",
        "agent benchmark (bare pass count -> with-corpus pass count).",
        "",
        "## Live corpora",
        "",
    ]
    for c in live:
        files, nbytes, licences = corpus_stats(c)
        t = c.get("tags") or {}
        tags = "/".join(([t["region"]] if t.get("region") else []) + t.get("topics", []))
        g = graded.get(c["slug"])
        g7s = f"G7 {g['median']:.1f}/5" if g else (f"G7 {g7[c['slug']]['median']:.1f}/5" if c["slug"] in g7 else "G7 not yet graded")
        ab = ""
        r = imp2.get(c["slug"])
        if r and r.get("status") == "measured":
            ab = f"; agent A/B {r['p']} -> {r['x']}"
        lines.append(f"- [{c['slug']}](https://hub.xerj.org/corpus/{c['slug']}): {c['cat']} · {tags} · {'+'.join(licences) or '?'} · {human_bytes(nbytes)} · {g7s}{ab}; {plain(c['usecase'])[:160]}")
    lines += ["", "## Also in the registry", "",
              f"- {len(corpora) - len(live)} rows in candidate, planned, deferred, killed, or",
              "  withdrawn states (visible, not hidden: hub policy is honest statuses).",
              "  Browse all: https://hub.xerj.org"]
    (OUT / "llms.txt").write_text("\n".join(lines) + "\n")
    n = len(list((OUT / "corpus").glob("*.html")))
    print(f"generated: index, about, {len(CATS)} category pages, {n} corpus pages -> {OUT}")


if __name__ == "__main__":
    main()
