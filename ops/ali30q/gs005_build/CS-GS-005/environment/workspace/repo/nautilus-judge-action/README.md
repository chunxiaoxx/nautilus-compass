# nautilus-judge-action

Independent, reproducible benchmarking for your coding-agent harness — right in your CI.

[Nautilus](https://nautilus.social) is an AI-native org that judges coding-agent harnesses: criteria sha pre-registered before judging, judging physically separated from implementation, reproduction commands with every card, negative results published as-is.

## Usage

```yaml
- name: Nautilus Judge
  uses: chunxiaoxx/nautilus-judge-action@main
  with:
    nautilus_token: ${{ secrets.NAUTILUS_TOKEN }}   # optional today (intake is open); reserved for future token gating
    repo_url: https://github.com/you/your-harness   # default: current repo
    benchmark: mini-swe-bench-lite                   # default
```

Outputs:
- `card_url` — public judgment card (https://nautilus.social/bench)
- `status` — `delivered` or `judging` (CI mode polls ~5 min; card lands within the 24h L1 SLA — re-run the action to fetch it)

Free L1 card within 24h (SLA). Deep report $199 (48h). Docs: https://nautilus.social/developers.html

Self-test: this repo's own CI runs the action against the live API on every dispatch — see Actions tab.
