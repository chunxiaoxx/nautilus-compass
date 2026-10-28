import concurrent.futures, urllib.request, ssl

pages = """admin annotate announcement auth/callback blog business-plan criteria criteria/ customer developers errata insights intake l2_sample leaderboard login os pipeline pricing products/companion products/compass products/data products/embodied products/harness products/unipat registry sites status submit/ tasks two_week_report unipat whitepaper org/ org/business-plan org/e2e org/leaderboard org/nautilus_map org/pipeline_platform org/whitepaper""".split()

def probe(p):
    url = f"https://www.nautilus.social/{p}"
    if not p.endswith("/"): url += ".html" if "/" not in p else ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "audit/1.0"})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
            body = r.read()
            size = len(body)
            dead = " DEAD-794" if size == 794 else ("" if size > 1500 else " SMALL!")
            flag = "OK " if not dead else "🔴 "
            return f"{flag}{url.replace('https://www.nautilus.social/',''):40s} {r.status} {size}{dead}"
    except urllib.error.HTTPError as e:
        return f"🔴 {url.replace('https://www.nautilus.social/',''):40s} {e.code} (HTTPError)"
    except Exception as e:
        return f"🔴 {url.replace('https://www.nautilus.social/',''):40s} EXC {type(e).__name__}"

with concurrent.futures.ThreadPoolExecutor(12) as ex:
    for r in ex.map(probe, pages):
        print(r)
