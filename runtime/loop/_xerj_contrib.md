# Contributing a corpus to the Hub

One pull request to the [`corpus-hub`](https://github.com/xerj-org/xerj/tree/corpus-hub)
branch per corpus. This guide is the whole process: what makes a good corpus, which lane
it goes down, the licence rules, and the checklist a reviewer will run. The general
engineering bar is [`CONTRIBUTING.md` on `main`](https://github.com/xerj-org/xerj/blob/main/CONTRIBUTING.md);
everything here is corpus-specific. A gentler walkthrough of the same material lives at
[xerj.org/docs/corpus-hub](https://xerj.org/docs/corpus-hub); this file is the source of
record — when the two disagree, this one wins.

---

## 1. What makes a good corpus

A corpus exists so that an agent — yours, or someone else's — retrieves **precedent**
instead of re-deriving it. Three properties decide whether a contribution is accepted:

1. **A domain a reviewer can name.** "Rust FTS engines", "Rust vulnerability advisories",
   "our internal incident postmortems". A corpus that contains everything retrieves like
   a search engine with no query. If you cannot finish the sentence *"an agent working on
   ___ would query this corpus for ___"*, it is not ready.
2. **Content the model has not memorised.** Retrieval's measured advantage is on niche,
   private, internal, or post-cutoff material. A corpus of famous public snippets a model
   already knows by heart adds install cost without adding knowledge. (Our own
   reference-coding study found exactly this: retrieval saved nothing on the two tasks
   whose libraries the model had memorised — the win lives everywhere else.)
3. **A right to redistribute, recorded per source.** You are the pack author; you own
   what goes in. Every source needs a licence you checked yourself and a `review` block
   saying what you concluded.

Sizes seen in practice: reference corpora from ~28 MB (three small storage engines) to
~1.2 GB (clickhouse) of checked-out source. Record packs: the `rust-vulns` pack is
1,950 records / ~10 MB zipped. Packs must stay under 2 GB per Release asset.

## 2. Pick a lane

| | reference corpus | record pack |
|---|---|---|
| content | other people's **source code**, cloned at pinned SHAs | **structured records** you assemble (advisories, datasets, docs) |
| you write | `hub/<name>.json` (a `corpus.json` manifest) | `tools/packs/<name>/recipe.toml` (+ README) |
| consumer runs | `xerj corpus add --from hub/<name>.json` then `xerj corpus index <name>` | downloads the signed pack, `xerj corpus add --from <pack> --verify-sig <pub>` |
| rebuilt by | anyone, anywhere, byte-identical (SHAs pinned) | a maintainer, on publish (the recipe is the whole build) |
| examples | `hub/xerj-storage.json`, `hub/xerj-vector.json` | `tools/packs/rust-vulns/` |

Rule of thumb: **code other people maintain → reference corpus; data you curate → pack.**

## 3. Lane A — reference corpus

Build locally, then submit the manifest the build generated:

```sh
# 1. build it (this clones at HEAD and records the SHAs it used)
xerj corpus add <name> <git-url>...

# 2. the manifest lands in ~/.xerj-code/corpora/<name>/corpus.json.
#    Copy it to hub/<name>.json — the filename MUST equal the "corpus" field.

# 3. check it passes the untrusted-input gate (same one consumers run)
cd engine && cargo test --profile ci-test -p xerj-common xccode::manifest

# 4. open the PR
```

Now the part only you can do: **open every repo's licence file yourself** and fill a
`review` block per source. Do not copy the detector's answer — it has been wrong in both
directions:

```json
"review": {"spdx": "MIT", "use": "adapt-with-attribution",
           "by": "@your-handle", "at": "2026-10-01",
           "note": "detector said MIT; confirmed against LICENSE (MIT, (c) 2020 …)."}
```

`use` must be exactly one of:

| `use` | licences | what it permits downstream |
|---|---|---|
| `adapt-with-attribution` | Apache-2.0, MIT, BSD | adapt freely; cite `file:line` when you do |
| `approach-only` | AGPL, SSPL, Elastic, BUSL, GPL, LGPL, MPL | read the design, write your own code — **never paste** |
| `mixed` | permissive core + restricted parts (e.g. Meilisearch MIT core / BUSL-EE) | check the file's header and path before copying anything |

XERJ is Apache-2.0 and states publicly that it shares no code with copyleft projects;
`approach-only` sources are in the Hub to answer *"what does the real thing do here?"*,
and that is all they are for. A wrong `use` value is the single fastest way to get a PR
rejected.

**Pins:** leave the SHAs exactly as the build recorded them. A shared pin is what makes
two people's retrieval results comparable. Refreshing a pin is its own PR, saying why.

## 4. Lane B — record pack

A pack is built from a declarative recipe; the tooling is domain-agnostic (identity
resolution, checksums, signatures) and all domain knowledge lives in your TOML. Start
from [`tools/packs/TEMPLATE-recipe.toml`](../../packs/TEMPLATE-recipe.toml), or read the
showcase: [`tools/packs/rust-vulns/recipe.toml`](../../packs/rust-vulns/recipe.toml)
(annotated with why each source is in and what was measured missing from each).

```sh
xerj corpus build <name> --recipe tools/packs/<name>/recipe.toml
xerj corpus add <name> --from ~/.xerj-code/builds/<name>/pack/<name>   # self-verify
```

Your PR includes **the recipe and a README** — never the built pack. In the README:

- **Provenance:** every source, its licence, and why it is in (the `rust-vulns` README is
  the pattern: which sources, what each uniquely contributes, what was measured missing).
- **Identity rules:** which fields make two records "the same thing" (for `rust-vulns`:
  CVE / GHSA / RUSTSEC aliases resolved by union-find; 4,107 envelopes → 1,950 records).
- **Known limits:** what the pack does not claim.

After review, a maintainer builds, signs (ed25519), and attaches the pack to a dated
GitHub Release; the recipe in git and the signature chain are then the reproducibility
story. Do not commit private keys — `tools/packs/keys/` holds only public halves.

## 5. The review checklist (what a maintainer runs)

- [ ] Filename equals the `corpus` field; JSON parses; SHAs are full 40-hex.
- [ ] Every source has a licence field **and** a human `review` block (`use` legal value).
- [ ] `cargo test --profile ci-test -p xerj-common xccode::manifest` passes (Lane A).
- [ ] Recipe validates and the PR carries no built pack, no key material, no secrets.
- [ ] The PR body names the domain and the query an agent would run (§1, property 1).
- [ ] The PR body states record counts and, for packs, the identity-resolution numbers.
- [ ] CI on this branch (`.github/workflows/corpus-hub-validate.yml`) is green.

## 6. What happens after merge

Reference corpora are consumable immediately from this branch (raw.githubusercontent
URLs — see the branch README). Record packs get built, signed, and attached to a
Release by a maintainer, usually within a few days; the pack's README then carries the
exact `curl` + `xerj corpus add --from … --verify-sig …` lines. Published packs are
re-datable: `rust-vulns` is rebuilt daily, and consumers' `xerj corpus index` refuses an
index older than 30 days by design — freshness is part of the contract.
