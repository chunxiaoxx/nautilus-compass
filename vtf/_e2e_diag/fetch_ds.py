"""Resumable dataset downloader: Range-request loop until complete."""
import os
import time
import requests

URL = ("https://huggingface.co/datasets/xiaowu0162/longmemeval/"
       "resolve/main/longmemeval_s")
OUT = os.path.join(os.path.dirname(__file__), "longmemeval_s")
TOTAL = 278025796
CHUNK = 1 << 18

for attempt in range(60):
    pos = os.path.getsize(OUT) if os.path.exists(OUT) else 0
    if pos >= TOTAL:
        print(f"DONE {pos}")
        break
    try:
        with requests.get(URL, stream=True, timeout=60,
                          headers={"Range": f"bytes={pos}-"}) as r:
            r.raise_for_status()
            mode = "ab" if pos else "wb"
            with open(OUT, mode) as f:
                for chunk in r.iter_content(CHUNK):
                    f.write(chunk)
    except Exception as e:
        print(f"attempt {attempt}: {type(e).__name__} at "
              f"{os.path.getsize(OUT) if os.path.exists(OUT) else 0}")
        time.sleep(3)
else:
    raise SystemExit("60 attempts exhausted")

sz = os.path.getsize(OUT)
print(f"FINAL size={sz} ok={sz == TOTAL}")
import json
d = json.load(open(OUT, encoding="utf-8"))
uniq = {sid for q in d for sid in q.get("haystack_session_ids", [])}
print(f"questions={len(d)} unique_sessions={len(uniq)}")
import collections
ev = collections.Counter(len(q.get("answer_session_ids", [])) for q in d)
print("evidence_count_dist:", dict(sorted(ev.items())))
print("fields:", sorted(d[0].keys()))
