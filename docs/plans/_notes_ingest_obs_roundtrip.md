# Cross-device ingest_obs → recall round-trip · Task 2.1 findings (2026-06-05)

Probe: ingest a uniquely-marked obs via the cloud MCP, then recall it. If
recallable, the cross-device ingest path is NOT silently failing.

## Setup
- Tool: `mcp__nautilus-compass-cloud__ingest_obs` (v0.9 `/v1/observations`) →
  `mcp__nautilus-compass-cloud__recall` (cloud BGE-m3 daemon).
- Unique marker: `quokka-zephyr-9173`; topic anchor "speckled quokka zephyr
  winds" (deliberately rare so dense retrieval surfaces only the probe).
- Project: `C--Users-chunx`.

## Finding 1 · CJK-in-`name` surrogate crash (reproducible, code-fixable)
First ingest with a Chinese `name` ("跨设备测试obs") hard-failed:
```
MCP error -32603: tool ingest_obs failed:
'utf-8' codec can't encode character '\udcae' in position 12: surrogates not allowed
```
A lone surrogate `\udcae` = a CJK byte mis-decoded somewhere in obs name
handling (client transport or server write). Re-ingest with an ASCII name
("xdev-probe-9173") succeeded. → Cross-device ingest of any obs whose `name`
contains CJK currently crashes. Concrete bug, independent of the recall
round-trip; many real obs names are Chinese, so this silently blocks a class of
cross-device writes. (surrogateescape on a Windows MCP client is the prime
suspect; needs confirmation of which side decodes.)

## Finding 2 · ASCII obs written but not recallable (strong, lag-confounded)
ASCII ingest returned success:
```
obs written · session_20260605-1907_xdev-probe-9173.md ·
agent_type=claude-code-compass-dialog · drift=green · proof_of_recall=not_attempted
```
Two recalls seconds apart BOTH failed to surface it:
- semantic: top hit 0.439 on an unrelated memory; "quokka zephyr" scored ~0.
- `fresh_extra` (the <24h list): newest entry was 3.4–3.5h old; the
  minutes-old probe was ABSENT entirely.

Total absence from `fresh_extra` (lists any <24h memory the daemon parsed into
`all_entries`) is the key signal: the dir the recall daemon scans does not
include the just-written obs.

### Remaining confound · indexing lag
The cloud daemon caches `all_entries` and rescans on an inotify dirty-flag /
periodic interval. A brand-new file can take minutes to appear. Two recalls
seconds apart do NOT rule this out. Decisive disambiguation needs ONE of:
- (a) a delayed re-recall (≥ rescan interval, ~tens of minutes) — if still
      absent → genuine round-trip gap, not lag;
- (b) SSH the cloud host (**G-cloud**) to check the file landed in the scanned
      `~/.claude/projects/C--Users-chunx/memory/` dir + inspect daemon logs.

## Endpoint caveat
Diagnosis flagged `/v1/v14/ingest_obs` (`ingest_obs+content` vs daemon
`ingest+text`, `ops/v0.9_to_v14_adapter_patch.py:187-216`). The MCP tool used
here is v0.9 `/v1/observations`, a DIFFERENT endpoint — it writes a real `.md`
file (returned a filename), so its recall gap is a rescan/landing-dir question,
not the field-mismatch the v14 adapter has. Testing the actual v14 route, and
the field-alignment fix (Task 2.2), needs the v14 endpoint reachable from here
or cloud access (**G-cloud**).

### Update · 3rd recall after ~25 min (lag largely ruled out)
A third recall ~25 min after the ingest (elapsed across T1.4 eval + T1.5 + T2
docs + T3 adapter + T4 demo) STILL shows the probe absent from both top-k and
`fresh_extra` (newest fresh_extra entry unchanged at 3.4h old). Other ~3.4h
memories ARE indexed, so the cloud daemon did rescan in this window — yet the
19:07 xdev-probe never appears. Three recalls over ~25 min ⇒ this is NOT
sub-minute indexing lag. **Verdict: a genuine cross-device round-trip gap** —
the obs the v0.9 `ingest_obs` reported as written does not land in (or is not
indexed from) the dir the cloud recall daemon scans. This confirms the
diagnosis's "跨设备 ingest 疑似静默失败" hypothesis to the extent reachable
without cloud access. The decisive ROOT CAUSE (wrong landing dir vs unwatched
dir vs rescan-never vs different host's ~/.claude) needs cloud FS/log inspection
= **G-cloud**.

Orphan note: the probe `session_20260605-1907_xdev-probe-9173.md` may be sitting
un-indexed on the cloud host; cleanup needs G-cloud.

## Status / next
- Finding 1 (CJK surrogate): actionable; fix side (client vs server) TBD.
- Finding 2 (round-trip gap): strong preliminary evidence; final verdict gated
  on delayed re-recall (will re-probe before wrap-up) or G-cloud.
- Task 2.2/2.3 (field-alignment fix + e2e re-verify) held until Finding 2 is
  disambiguated: if lag → likely no code bug on this v0.9 path; if landing-dir/
  field gap → fix target depends on v0.9 vs v14 and lives partly cloud-side
  (**G-cloud** to deploy/verify).
