---
title: nautilus-compass demo
emoji: 🧭
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: "4.44.0"
app_file: app.py
pinned: false
license: mit
---

# nautilus-compass · drift detector + Merkle audit log · live demo

Two-tab Gradio demo for [`nautilus-compass`](https://github.com/chunxiaoxx/nautilus-compass),
the persona-drift detector and tamper-evident memory log for long-running
agent sessions.

## What it does

**Tab 1 · Drift detection.** Paste a `(system_prompt, response)` pair from a
real session. We score the pair against the persona anchors shipped with
`nautilus-compass` (25 positive + 25 negative behavioural exemplars), emit
an alignment / deviation / drift_score triple, and render a green / yellow /
red verdict.

- Green = response sits inside the persona anchor cone.
- Yellow = neutral, weak signal either way.
- Red = response is closer to the *negative* anchors (sycophancy,
  fake-completion, root-cause skipping, etc.) than the positive ones.

Two bundled samples (`sample_session.md` and `sample_session_drifted.md`)
demonstrate the alert behaviour without you typing anything.

**Tab 2 · Memory integrity.** Upload a `.zip` of `session_*.md` files plus
an optional `.chain.json`. We re-run the same Merkle hash chain that the
plugin's `merkle_chain.py` ships and report tampered / missing / unrecorded
files with full hash diff. Nothing is persisted server-side; the zip is
extracted to an ephemeral tempdir.

## Why it lives on a free Spaces tier

This Space is the no-install introduction. The full system runs locally as a
Claude Code plugin and uses BGE-m3 dense embeddings (held-out drift AUC
0.83). On the free Spaces tier (CPU only, 16 GB RAM, no GPU) we cannot load
BGE without OOM-ing or starving the demo of latency budget, so we ship the
**metadata-mode fallback** that already exists in `recall.py` (char-4grams +
jaccard + overlap coefficient). Verdicts are directionally aligned but
noticeably looser than the BGE numbers; for the real thing, install the
plugin and run the daemon locally.

## Headline numbers

| Bench | Score |
| --- | --- |
| LongMemEval-S | 56.6% |
| EverMemBench | 44.4% |
| drift AUC (held-out) | 0.83 |

## Local test before pushing

The Space's entrypoint is plain Gradio; you can run it locally first.

```bash
cd hf_space
pip install -r requirements.txt
python app.py
# Gradio prints a localhost URL · open it · kill with Ctrl-C
```

If Gradio is not installed, `python -c "import gradio"` will raise
`ImportError`; install it via `pip install "gradio>=4.0"` and retry.

## Deploying to Hugging Face Spaces

### 1. Install the HF Hub CLI

```bash
pip install -U huggingface_hub
huggingface-cli login
# Paste your HF token. It is saved to ~/.cache/huggingface/token.
# A "write" token is required to push code to a Space.
```

### 2. Create the Space (one-off)

Either via the web UI at https://huggingface.co/new-space (pick the
**Gradio** SDK and grab the `username/space-name` slug) or via the CLI:

```bash
huggingface-cli repo create nautilus-compass-demo --type space --space-sdk gradio
```

### 3. Push the contents

The cleanest path is to clone the empty Space repo and copy this directory's
files into it:

```bash
git clone https://huggingface.co/spaces/<your-username>/nautilus-compass-demo
cp app.py requirements.txt README.md .gitignore \
   sample_session.md sample_session_drifted.md \
   nautilus-compass-demo/
cd nautilus-compass-demo
git lfs install   # not strictly needed, no large files in this Space
git add .
git commit -m "scaffold nautilus-compass demo"
git push
```

The first push triggers a build. Watch the **Logs** tab on the Space page;
expect a cold start of roughly 60-120 seconds while the container provisions
and Gradio installs. After that, container restarts are typically under
20 seconds.

### 4. (Optional) Bundle anchors.json

For the most informative drift verdicts, copy `anchors.json` from the
plugin root next to `app.py` before pushing:

```bash
cp ../anchors.json nautilus-compass-demo/anchors.json
```

The app looks for `anchors.json` next to `app.py` first, then one
directory up; if neither is present it falls back to a small built-in
anchor set so the demo still works.

## Free tier limits to keep in mind

- **CPU only.** No GPU, so dense embedding models are out; we use the
  metadata-mode jaccard fallback. The demo enforces a 5 s timeout on the
  drift check and a 4000 char cap per textbox.
- **16 GB RAM.** Loading BGE-m3 weights (~2.3 GB on disk + activations)
  will spike close to this and starve Gradio of memory; we don't try.
- **50 GB persistent storage.** The Space's git repo is the persistent
  layer. We don't write anything to disk during inference; uploaded zips go
  to `tempfile.TemporaryDirectory()` and are wiped after the request.
- **Cold start.** First request after a sleep can take ~30 s because the
  container has to boot. Keep this in mind if you embed the Space in a
  demo video.
- **No long-running daemons.** The plugin's BGE daemon (`daemon.py`) is
  not run in this Space; for that, deploy locally or self-host on a GPU
  VM (see `SELF_HOST.md` in the main repo).

## License

MIT, same as the upstream `nautilus-compass` project.
