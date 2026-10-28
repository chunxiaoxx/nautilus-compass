---
name: nautilus-research
description: Run deep multi-agent research via Nautilus DeerFlow engine. Planner decomposes topics, parallel Researchers investigate each angle, Reporter synthesizes findings into structured reports.
user-invocable: true
homepage: https://nautilus.social
---

# Nautilus Deep Research

Run comprehensive, multi-angle research using Nautilus's DeerFlow engine — a three-role AI chain where a Planner decomposes your topic, multiple Researchers investigate in parallel, and a Reporter synthesizes everything into a structured report.

## When to Use This Skill

Use this skill when the user needs:
- In-depth analysis of a complex topic
- Multi-angle investigation beyond a single LLM response
- Structured research reports with findings and recommendations
- Research that should be saved to Google Docs

## Commands

### /research [topic]
Run a standard depth research on a topic.

Example: `/research Impact of AI agents on labor markets`

### /research-deep [topic]
Run thorough research (more sub-questions, deeper analysis).

### /research-quick [topic]
Run a quick research pass (faster, fewer angles).

## How to Execute

Call `POST https://nautilus.social/api/research/deep` with:

```json
{
  "topic": "<research topic>",
  "depth": "standard",
  "save_to_gdoc": false
}
```

**depth options**: `"quick"` | `"standard"` | `"thorough"`

For `thorough` depth, the API returns immediately with a `job_id`. Poll `GET https://nautilus.social/api/research/status/<job_id>` until `status` is `completed`.

**Response format**:
```json
{
  "success": true,
  "data": {
    "report": "Full markdown report...",
    "sections": {
      "summary": "...",
      "findings": ["..."],
      "recommendations": ["..."]
    },
    "gdoc_url": "https://docs.google.com/..."
  }
}
```

## How It Works

1. **Planner**: Breaks your topic into 3-5 targeted sub-questions
2. **Researchers**: Each sub-question gets its own parallel investigation
3. **Reporter**: Synthesizes all findings into a structured report with summary, key findings, and recommendations

This produces significantly richer results than a single-prompt approach because each sub-question gets dedicated attention and the final synthesis reconciles different angles.

## Tips

- Be specific: "GPT-4 vs Claude 3 for code generation benchmarks" > "AI models"
- Use `thorough` for strategic decisions, `quick` for background checks
- Set `save_to_gdoc: true` to get a shareable Google Doc link (requires Google Workspace configured on the server)
