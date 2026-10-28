"""SWE-bench_Lite core-subset sizing — pure Python, no Docker.

Phase 4 (Paradigm B) prerequisite per HANDOFF #024 / design doc §7.
Counts test-split instances whose GOLD patch spans >=2 files OR >=2 hunks.
  files = count of `diff --git ` headers in the `patch` field
  hunks = count of lines beginning with `@@`
Neutral structural criterion (NOT selected on baseline failure) -> no selection bias.
Target: confirm the multi-file/multi-hunk subset reaches N ~= 30-60.
"""

from datasets import load_dataset


def count_files(patch: str) -> int:
    return sum(1 for line in patch.splitlines() if line.startswith("diff --git "))


def count_hunks(patch: str) -> int:
    return sum(1 for line in patch.splitlines() if line.startswith("@@"))


def main() -> None:
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    total = len(ds)

    files_ge2 = hunks_ge2 = union_ge2 = both_ge2 = 0
    rows = []
    for ex in ds:
        patch = ex["patch"] or ""
        nf = count_files(patch)
        nh = count_hunks(patch)
        f2 = nf >= 2
        h2 = nh >= 2
        files_ge2 += f2
        hunks_ge2 += h2
        union_ge2 += (f2 or h2)
        both_ge2 += (f2 and h2)
        rows.append((ex["instance_id"], ex["repo"], nf, nh))

    print(f"total test instances: {total}")
    print(f"  files >= 2:            {files_ge2}")
    print(f"  hunks >= 2:            {hunks_ge2}")
    print(f"  files>=2 AND hunks>=2: {both_ge2}")
    print(f"  files>=2 OR  hunks>=2: {union_ge2}   <-- design subset criterion")
    print()

    # distribution of file / hunk counts
    from collections import Counter
    fc = Counter(nf for _, _, nf, _ in rows)
    hc = Counter(nh for _, _, _, nh in rows)
    print("file-count distribution:", dict(sorted(fc.items())))
    print("hunk-count distribution:", dict(sorted(hc.items())))
    print()

    # repo breakdown of the OR-subset
    from collections import defaultdict
    repo_subset = defaultdict(int)
    for iid, repo, nf, nh in rows:
        if nf >= 2 or nh >= 2:
            repo_subset[repo] += 1
    print("OR-subset by repo:")
    for repo, n in sorted(repo_subset.items(), key=lambda x: -x[1]):
        print(f"  {n:3d}  {repo}")

    # write the subset instance ids for downstream use
    import json
    subset = [
        {"instance_id": iid, "repo": repo, "files": nf, "hunks": nh}
        for iid, repo, nf, nh in rows
        if nf >= 2 or nh >= 2
    ]
    out = "swebench_lite_core_subset.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(subset, fh, indent=2)
    print(f"\nwrote {len(subset)} subset rows -> {out}")


if __name__ == "__main__":
    main()
