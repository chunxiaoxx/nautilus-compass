Hi Ivan,

Thanks for the directness — first line, no burial. That's exactly the register we try to work in, so let me match it: yes, we'll contribute, and we'll start where you asked for it most — telling you what's wrong.

Some context on fit: nautilus-compass is a memory + verification system for AI agents (BM25 + BGE-m3 hybrid retrieval over long-lived project memory, ~130 days of real organizational trajectory indexed). Retrieval quality over that corpus is literally our daily problem, so a reference corpus for search/retrieval code is directly useful to us — I'll be consuming llms.txt this week and reporting back with specifics rather than impressions.

What we can realistically give, in order:

1. Issues with teeth: we'll run our retrieval stack against your corpus on our hardest cases (cross-session recall, hybrid scoring where BM25 and dense disagree, chunking of structured logs) and file issues with reproductions — the cases where reference coding does NOT help are the ones we care about most, same as your case-study section.
2. A PR on hybrid scoring or chunking, scoped small, if the issues hold up.
3. One thing in return, offered once and then dropped: we run an independent verification practice (pre-registered criteria, third-party recompute, published errata). Your 11/16 vs 16/16 result is exactly the kind of number that gets quoted and misquoted — if you ever want it recomputed by someone with no stake in it, the offer stands. No strings either way; the corpus is useful enough on its own merits.

On the mission itself: reference coding over API/half-remembered behavior is a real bottleneck, and "no funding, no company" is a feature for corpus trust. Building in the open cuts both ways — we publish our own grader errors too — which is probably why your note landed.

— Chunxiao Wang
nautilus-compass · github.com/chunxiaoxx/nautilus-compass
