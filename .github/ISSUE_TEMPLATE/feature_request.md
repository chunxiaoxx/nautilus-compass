---
name: Feature request
about: Suggest an improvement
labels: enhancement
---

## What

(One sentence describing the proposed feature)

## Why now

What can't you currently do that you want to?

## Sketch (optional)

```
# Pseudo-code or example call
```

## Where in the roadmap

If you've read [paper/V10_ROADMAP.md](../../paper/V10_ROADMAP.md), point to the
phase you think this fits in (e.g., v0.9.5, v1.0.1).

## Compatibility

- [ ] Affects MCP protocol surface (would require client coordination)
- [ ] Affects A2A protocol surface
- [ ] Affects schema (would require migration)
- [ ] Affects user-visible defaults (announce in CHANGELOG)
- [ ] None of the above (pure backend)

## Drift consideration

Does the feature introduce new ways the AI could go wrong? (Hallucinate
agent_id, fabricate drift signals, etc.) If so, how should compass detect it?
