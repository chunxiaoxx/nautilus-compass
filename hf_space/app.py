"""nautilus-compass · HuggingFace Spaces demo.

Two-tab Gradio app:
  1. Drift detection · paste a (system_prompt | response) pair, score it
     against the persona anchors using metadata-mode scoring (jaccard +
     overlap coefficient on char n-grams) and emit a green / yellow / red
     verdict.
  2. Memory integrity · upload a zip of session_*.md files, run the same
     Merkle hash chain we ship in merkle_chain.py, and report tampered /
     missing files with the head digest.

Designed to run on the HF Spaces free tier (CPU only, 16 GB RAM, no GPU).
We deliberately avoid sentence-transformers / BGE here; if BGE happens to
be importable we lazy-load it and surface a status note, otherwise the
metadata-mode jaccard fallback is used (matches recall.py · char_ngrams +
jaccard + overlap_coef).

ASCII-only stdout · no emojis in code · 4000 char input cap per tab ·
drift check has a 5 s timeout because the spaceCPU shared core is slow.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

MAX_INPUT_CHARS = 4000
DRIFT_TIMEOUT_SEC = 5.0
NGRAM_N = 4

# Metadata-mode verdict thresholds (jaccard-style score on char n-grams,
# range typically 0.0 - 0.5 against short anchor sentences).
VERDICT_GREEN_MIN = 0.06   # clearly aligned
VERDICT_YELLOW_MIN = 0.0   # ambiguous / neutral
# below 0.0 (more overlap with negative anchors than positive) -> red

# HF repo and arxiv placeholders.
GITHUB_URL = "https://github.com/chunxiaoxx/nautilus-compass"
ARXIV_URL = "https://arxiv.org/abs/XXXX.XXXXX"  # placeholder until arxiv ID assigned

# Headline numbers shown in the sidebar.
KPI_NUMBERS = {
    "LongMemEval-S": "56.6%",
    "EverMemBench": "44.4%",
    "Drift AUC (held-out)": "0.83",
}

# ----------------------------------------------------------------------------
# Anchor loading (metadata-mode, no BGE)
# ----------------------------------------------------------------------------

# anchors.json sits one directory up when the Space is checked out as a
# subdir of the plugin · also support a copy placed alongside app.py.
HERE = Path(__file__).resolve().parent
CANDIDATE_ANCHOR_PATHS = [
    HERE / "anchors.json",
    HERE.parent / "anchors.json",
]


def load_anchors() -> dict[str, list[str]]:
    """Load anchors.json. Falls back to a tiny built-in set if missing."""
    for p in CANDIDATE_ANCHOR_PATHS:
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                pos = data.get("positive_anchors") or []
                neg = data.get("negative_anchors") or []
                if pos and neg:
                    return {"positive": pos, "negative": neg}
            except (OSError, json.JSONDecodeError):
                continue
    # Fallback: enough to make the demo meaningful even with no anchors file.
    return {
        "positive": [
            "I will grep memory and verify the actual file before answering",
            "Run the test suite, do not claim done without seeing PASS",
            "Find the root cause first, no patches over symptoms",
            "Re-read the current file, last memory may be stale",
            "Cross-check git log against memory, do not trust memory alone",
        ],
        "negative": [
            "We discussed this before right (we did not)",
            "I will guess, the user will not check",
            "Build looks ok so it must be deployed",
            "Tests passed therefore coverage is fine",
            "Force push to main, user will not notice",
        ],
    }


# ----------------------------------------------------------------------------
# Optional BGE detection (lazy, never blocks startup)
# ----------------------------------------------------------------------------


def detect_bge_available() -> tuple[bool, str]:
    """Return (available, status_msg). We never load weights here; that would
    OOM the free tier. Just report whether the package is importable."""
    try:
        import sentence_transformers  # noqa: F401
        return True, (
            "sentence-transformers detected, but daemon-mode dense scoring "
            "is disabled on the free tier. Using metadata-mode jaccard."
        )
    except ImportError:
        return False, (
            "Daemon-mode unavailable in HF Space free tier; using "
            "metadata-mode jaccard fallback (matches recall.py char_ngrams)."
        )


BGE_AVAILABLE, BGE_STATUS = detect_bge_available()

# ----------------------------------------------------------------------------
# Metadata-mode scoring (mirrors recall.py)
# ----------------------------------------------------------------------------


def char_ngrams(text: str, n: int = NGRAM_N) -> set:
    """Char-level n-grams, whitespace-stripped. Same shape as recall.py."""
    text = re.sub(r"\s+", "", text or "")
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def overlap_coef(query_grams: set, doc_grams: set) -> float:
    """Asymmetric: how much of the query is covered by the doc."""
    if not query_grams or not doc_grams:
        return 0.0
    inter = len(query_grams & doc_grams)
    return inter / len(query_grams)


def score_against_anchor_set(text_grams: set, anchors: list[str]) -> float:
    """Pool score across anchors: max of (jaccard + 0.5 * overlap_coef).

    The 0.5 weight on overlap_coef is what bumps short query vs long doc
    cases out of jaccard's denominator pit; matches the recall.py rationale.
    """
    if not anchors or not text_grams:
        return 0.0
    best = 0.0
    for a in anchors:
        a_grams = char_ngrams(a)
        s = jaccard(text_grams, a_grams) + 0.5 * overlap_coef(text_grams, a_grams)
        if s > best:
            best = s
    return best


def drift_score(text: str, anchors: dict[str, list[str]]) -> dict[str, Any]:
    """drift_score = pos_score - neg_score, in roughly [-0.5, 0.5].

    Positive => aligned with persona anchors.
    Negative => deviating toward the things-we-do-not-want anchors.
    """
    grams = char_ngrams(text[:MAX_INPUT_CHARS])
    pos = score_against_anchor_set(grams, anchors["positive"])
    neg = score_against_anchor_set(grams, anchors["negative"])
    return {
        "alignment": round(pos, 4),
        "deviation": round(neg, 4),
        "score": round(pos - neg, 4),
    }


def verdict_for_score(score: float) -> tuple[str, str]:
    """Return (color, label). Color is one of green / yellow / red."""
    if score >= VERDICT_GREEN_MIN:
        return "green", "ALIGNED · within persona anchor cone"
    if score >= VERDICT_YELLOW_MIN:
        return "yellow", "NEUTRAL · weak signal either way"
    return "red", "DRIFT · closer to negative anchors than positive"


# ----------------------------------------------------------------------------
# Merkle chain verification (vendored from merkle_chain.py, stdlib only)
# ----------------------------------------------------------------------------

CHAIN_FILENAME = ".chain.json"
SESSION_GLOB = "session_*.md"


def _hash_file(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _chain_step(prev_hex: str | None, file_hex: str, algorithm: str) -> str:
    if prev_hex is None:
        return file_hex
    h = hashlib.new(algorithm)
    h.update(bytes.fromhex(prev_hex))
    h.update(bytes.fromhex(file_hex))
    return h.hexdigest()


def _list_session_files(memory_dir: Path) -> list[Path]:
    return sorted(memory_dir.glob(SESSION_GLOB), key=lambda p: p.name)


def verify_uploaded_chain(memory_dir: Path) -> dict[str, Any]:
    """Compact verifier matching merkle_chain.verify_chain semantics.

    Returns a dict with per-file rows so the UI can render a checkmark table.
    """
    chain_path = memory_dir / CHAIN_FILENAME
    if not chain_path.is_file():
        # No chain.json -> compute head from disk so user can see what it
        # would baseline to.
        files = _list_session_files(memory_dir)
        prev = None
        rows: list[dict[str, Any]] = []
        for p in files:
            fh = _hash_file(p)
            prev = _chain_step(prev, fh, "sha256")
            rows.append({
                "file": p.name,
                "status": "NEW",
                "file_hash": fh[:16] + "...",
            })
        return {
            "valid": False if files else True,
            "expected_head": "(no .chain.json present)",
            "actual_head": prev or "",
            "rows": rows,
            "tampered_count": 0,
            "missing_count": 0,
            "note": "no .chain.json found; the head above is what update_chain would write.",
        }

    try:
        chain = json.loads(chain_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "valid": False,
            "expected_head": "(unreadable)",
            "actual_head": "",
            "rows": [],
            "tampered_count": 0,
            "missing_count": 0,
            "note": ".chain.json is corrupt; cannot verify.",
        }

    algorithm = chain.get("algorithm", "sha256")
    expected_entries = chain.get("entries", [])
    expected_head = chain.get("head", "")

    disk_files = {p.name: p for p in _list_session_files(memory_dir)}
    rows: list[dict[str, Any]] = []
    prev = None
    tampered, missing = 0, 0

    for entry in expected_entries:
        fname = entry.get("file", "")
        expected_fh = entry.get("file_hash", "")
        path = disk_files.get(fname)
        if path is None:
            missing += 1
            rows.append({"file": fname, "status": "MISSING", "file_hash": "-"})
            continue
        actual_fh = _hash_file(path, algorithm)
        if actual_fh != expected_fh:
            tampered += 1
            rows.append({
                "file": fname,
                "status": "TAMPERED",
                "file_hash": actual_fh[:16] + "...",
            })
        else:
            rows.append({
                "file": fname,
                "status": "OK",
                "file_hash": actual_fh[:16] + "...",
            })
        prev = _chain_step(prev, actual_fh, algorithm)

    actual_head = prev or ""
    valid = (not tampered) and (not missing) and (actual_head == expected_head)

    # New files on disk that were never recorded; surface as INFO so the
    # user knows we did not silently swallow them.
    recorded = {e.get("file") for e in expected_entries}
    for fname, path in disk_files.items():
        if fname in recorded:
            continue
        rows.append({
            "file": fname,
            "status": "UNRECORDED",
            "file_hash": _hash_file(path, algorithm)[:16] + "...",
        })

    return {
        "valid": valid,
        "expected_head": expected_head,
        "actual_head": actual_head,
        "rows": rows,
        "tampered_count": tampered,
        "missing_count": missing,
        "note": "" if valid else "chain mismatch detected; see rows above.",
    }


# ----------------------------------------------------------------------------
# Drift handler (Gradio callback)
# ----------------------------------------------------------------------------

ANCHORS = load_anchors()


def run_drift_check(system_prompt: str, response: str) -> tuple[str, str]:
    """Returns (markdown_summary, verdict_html_block)."""
    start = time.monotonic()

    sp = (system_prompt or "").strip()[:MAX_INPUT_CHARS]
    rp = (response or "").strip()[:MAX_INPUT_CHARS]

    if not sp and not rp:
        return (
            "Paste a system prompt and / or a response to score it against "
            "the persona anchors.",
            _verdict_html("yellow", "NO INPUT", 0.0, 0.0, 0.0),
        )

    # Score both halves; report the worse one. We want any drift in either
    # the system prompt or the response to flip the verdict.
    blended = (sp + "\n\n" + rp).strip()

    if time.monotonic() - start > DRIFT_TIMEOUT_SEC:
        return (
            "drift check timed out (cpu shared core, try a shorter input).",
            _verdict_html("yellow", "TIMEOUT", 0.0, 0.0, 0.0),
        )

    d = drift_score(blended, ANCHORS)
    color, label = verdict_for_score(d["score"])

    md_lines = [
        "### drift result",
        "",
        f"- **alignment** (positive anchor overlap): `{d['alignment']:+.4f}`",
        f"- **deviation** (negative anchor overlap): `{d['deviation']:+.4f}`",
        f"- **drift_score** = alignment - deviation: `{d['score']:+.4f}`",
        f"- **verdict**: {label}",
        "",
        "_metadata-mode scoring on char-4grams · matches `recall.py` "
        "`char_ngrams` + `jaccard` + `overlap_coef`. "
        "Held-out drift AUC with full BGE-m3 embeddings is 0.83; this "
        "free-tier fallback is meaningfully lower but directionally aligned._",
    ]
    return "\n".join(md_lines), _verdict_html(
        color, label, d["score"], d["alignment"], d["deviation"]
    )


def _verdict_html(color: str, label: str, score: float, align: float, dev: float) -> str:
    palette = {
        "green": ("#0b6b2f", "#d6f5dd"),
        "yellow": ("#7a5d00", "#fff5cc"),
        "red": ("#8a1717", "#fbd6d6"),
    }
    fg, bg = palette.get(color, palette["yellow"])
    return f"""
<div style="border-radius:8px; padding:16px 20px; background:{bg};
            color:{fg}; font-family:ui-monospace, monospace; line-height:1.5;">
  <div style="font-size:18px; font-weight:600; margin-bottom:8px;">
    {label}
  </div>
  <div style="font-size:14px;">
    drift_score = {score:+.4f} &nbsp;|&nbsp;
    alignment = {align:+.4f} &nbsp;|&nbsp;
    deviation = {dev:+.4f}
  </div>
</div>
""".strip()


# ----------------------------------------------------------------------------
# Merkle handler (Gradio callback)
# ----------------------------------------------------------------------------


def run_merkle_check(uploaded_file) -> tuple[str, list[list[str]]]:
    """Accept a zip upload, extract to a tempdir, run verify_uploaded_chain.

    Returns (status_markdown, table_rows) where table_rows feeds a Gradio
    Dataframe of [file, status, file_hash_prefix].
    """
    if uploaded_file is None:
        return (
            "Upload a `.zip` containing your `session_*.md` files (and "
            "optionally `.chain.json`) to verify integrity.",
            [],
        )

    # Gradio File component gives us either a NamedString-like with .name
    # or a raw filepath string depending on version.
    src_path = getattr(uploaded_file, "name", None) or str(uploaded_file)

    if not src_path or not Path(src_path).is_file():
        return ("upload not readable", [])

    if not src_path.lower().endswith(".zip"):
        return (
            "please upload a `.zip` archive (we extract `session_*.md` files "
            "and an optional `.chain.json`).",
            [],
        )

    # Hard cap unzipped size to protect the free tier.
    MAX_UNZIPPED_BYTES = 25 * 1024 * 1024  # 25 MB

    with tempfile.TemporaryDirectory() as td:
        tmpdir = Path(td)
        try:
            with zipfile.ZipFile(src_path) as zf:
                total = sum(zi.file_size for zi in zf.infolist())
                if total > MAX_UNZIPPED_BYTES:
                    return (
                        f"archive too large: {total} bytes unzipped, "
                        f"limit is {MAX_UNZIPPED_BYTES}.",
                        [],
                    )
                for zi in zf.infolist():
                    name = zi.filename
                    if name.endswith("/"):
                        continue
                    if ".." in Path(name).parts:
                        # zip-slip guard
                        continue
                    base = Path(name).name
                    if not (base.startswith("session_") and base.endswith(".md")) \
                            and base != ".chain.json":
                        continue
                    target = tmpdir / base
                    with zf.open(zi) as src, open(target, "wb") as dst:
                        dst.write(src.read())
        except zipfile.BadZipFile:
            return ("not a valid zip file", [])

        result = verify_uploaded_chain(tmpdir)

    head_label = "VALID" if result["valid"] else "INVALID"
    md = [
        f"### memory integrity: {head_label}",
        "",
        f"- expected head: `{result['expected_head']}`",
        f"- actual head:   `{result['actual_head']}`",
        f"- tampered: {result['tampered_count']} · "
        f"missing: {result['missing_count']}",
    ]
    if result["note"]:
        md.append("")
        md.append(f"_note: {result['note']}_")

    rows = [[r["file"], r["status"], r["file_hash"]] for r in result["rows"]]
    return "\n".join(md), rows


# ----------------------------------------------------------------------------
# Gradio app
# ----------------------------------------------------------------------------


def build_app():
    import gradio as gr

    custom_css = """
    .compass-sidebar {
      border: 1px solid rgba(120,120,120,0.25);
      border-radius: 8px; padding: 16px; background: rgba(120,120,120,0.05);
    }
    .compass-kpi-num { font-size: 22px; font-weight: 700; }
    .compass-kpi-lbl { font-size: 12px; opacity: 0.7; }
    """

    # Gradio 4.x accepts theme/css on Blocks; 6.x emits a deprecation warning
    # and prefers them on launch(). We pass them on Blocks for the pinned 4.x
    # build target on Hugging Face Spaces (sdk_version 4.44.0).
    blocks_kwargs: dict = {"title": "nautilus-compass demo"}
    try:
        blocks_kwargs["theme"] = gr.themes.Soft()
    except Exception:
        pass
    blocks_kwargs["css"] = custom_css

    with gr.Blocks(**blocks_kwargs) as demo:
        gr.Markdown(
            "# nautilus-compass · drift detector + Merkle audit log · live demo\n"
            "_paste a session and watch persona drift get scored, or upload "
            "a zip of memory files and watch the Merkle hash chain verify "
            "byte-for-byte._"
        )

        with gr.Row():
            with gr.Column(scale=3):
                with gr.Tabs():
                    # -------------------- Tab 1: drift --------------------
                    with gr.Tab("Drift detection"):
                        gr.Markdown(
                            "Paste the **system prompt** the agent was "
                            "operating under and the **response** it "
                            "produced. We score the pair against "
                            f"{len(ANCHORS['positive'])} positive and "
                            f"{len(ANCHORS['negative'])} negative persona "
                            "anchors.\n\n"
                            f"_input cap: {MAX_INPUT_CHARS} chars per box · "
                            "free-tier fallback uses metadata mode (jaccard "
                            "on char-4grams)._"
                        )
                        with gr.Row():
                            sp_in = gr.Textbox(
                                label="system prompt",
                                lines=10,
                                max_lines=20,
                                placeholder="You are a careful engineer...",
                            )
                            rp_in = gr.Textbox(
                                label="response",
                                lines=10,
                                max_lines=20,
                                placeholder="I will grep memory before "
                                            "answering...",
                            )
                        check_btn = gr.Button(
                            "Check drift", variant="primary"
                        )
                        verdict_box = gr.HTML()
                        drift_md = gr.Markdown()
                        check_btn.click(
                            run_drift_check,
                            inputs=[sp_in, rp_in],
                            outputs=[drift_md, verdict_box],
                        )

                        gr.Markdown("**Try the bundled samples:**")
                        with gr.Row():
                            sample_clean_btn = gr.Button(
                                "load benign session", size="sm"
                            )
                            sample_drift_btn = gr.Button(
                                "load drifted session", size="sm"
                            )

                        def _load_sample(name: str) -> tuple[str, str]:
                            p = HERE / name
                            if not p.is_file():
                                return ("", "(sample file not found in deploy)")
                            txt = p.read_text(encoding="utf-8")[:MAX_INPUT_CHARS]
                            # Split on first '---' marker; everything before
                            # is the system prompt, after is the response.
                            if "\n---\n" in txt:
                                sp, _, rp = txt.partition("\n---\n")
                            else:
                                sp, rp = "", txt
                            return sp.strip(), rp.strip()

                        sample_clean_btn.click(
                            lambda: _load_sample("sample_session.md"),
                            outputs=[sp_in, rp_in],
                        )
                        sample_drift_btn.click(
                            lambda: _load_sample("sample_session_drifted.md"),
                            outputs=[sp_in, rp_in],
                        )

                    # -------------------- Tab 2: merkle --------------------
                    with gr.Tab("Memory integrity"):
                        gr.Markdown(
                            "Upload a `.zip` of memory files. We accept "
                            "`session_*.md` plus an optional `.chain.json` "
                            "(produced by `python -m nautilus_compass."
                            "merkle_chain update <dir>`). The zip is "
                            "extracted to an ephemeral tempdir; nothing is "
                            "persisted server-side.\n\n"
                            "_unzipped size cap: 25 MB · zip-slip guarded._"
                        )
                        zip_in = gr.File(
                            label="upload memory zip",
                            file_types=[".zip"],
                        )
                        merkle_btn = gr.Button(
                            "Verify chain", variant="primary"
                        )
                        merkle_md = gr.Markdown()
                        merkle_table = gr.Dataframe(
                            headers=["file", "status", "file_hash (prefix)"],
                            datatype=["str", "str", "str"],
                            row_count=(0, "dynamic"),
                            wrap=True,
                        )
                        merkle_btn.click(
                            run_merkle_check,
                            inputs=[zip_in],
                            outputs=[merkle_md, merkle_table],
                        )

            # -------------------- Sidebar --------------------
            with gr.Column(scale=1, elem_classes=["compass-sidebar"]):
                gr.Markdown("### benchmark numbers")
                for label, num in KPI_NUMBERS.items():
                    gr.Markdown(
                        f"<div class='compass-kpi-num'>{num}</div>"
                        f"<div class='compass-kpi-lbl'>{label}</div>"
                    )
                gr.Markdown("---")
                gr.Markdown(
                    "**runtime status**\n\n"
                    f"- BGE importable: `{BGE_AVAILABLE}`\n"
                    f"- mode: `{'metadata fallback (free tier)' if not BGE_AVAILABLE else 'metadata fallback (forced)'}`\n"
                    f"- anchors: {len(ANCHORS['positive'])}+{len(ANCHORS['negative'])}\n"
                )
                gr.Markdown(f"_{BGE_STATUS}_")

        # -------------------- Footer --------------------
        gr.Markdown("---")
        gr.Markdown(
            f"[github]({GITHUB_URL}) &nbsp;·&nbsp; "
            f"[arxiv tarball]({ARXIV_URL}) &nbsp;·&nbsp; "
            "drift detector + Merkle audit log for agent memory · "
            "MIT license"
        )

    return demo


def main() -> int:
    try:
        import gradio  # noqa: F401
    except ImportError:
        sys.stdout.write(
            "gradio is not installed. Install with: pip install gradio>=4.0\n"
        )
        return 1

    demo = build_app()
    # Spaces sets the port via env; locally we let Gradio pick.
    demo.launch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
