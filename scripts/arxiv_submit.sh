#!/usr/bin/env bash
# arxiv_submit.sh - Build paper2 and package source tarball for arXiv submission.
#
# Usage:
#   ./arxiv_submit.sh              # build + package
#   ./arxiv_submit.sh --dry-run    # validate environment only, no compile
#   ./arxiv_submit.sh --help

set -euo pipefail

# ---------- config ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PAPER_DIR="$REPO_ROOT/paper"
MAIN_TEX="paper2_main.tex"
MAIN_STEM="paper2_main"
BIB_FILE="paper2_refs.bib"
EXPECTED_PAGES_MIN=8
OUT_TARBALL="$REPO_ROOT/paper2_arxiv_submission.tar.gz"

# ---------- color logging ----------
if [[ -t 1 ]]; then
    C_R=$'\033[31m'; C_G=$'\033[32m'; C_Y=$'\033[33m'; C_B=$'\033[34m'; C_N=$'\033[0m'
else
    C_R=""; C_G=""; C_Y=""; C_B=""; C_N=""
fi
info()  { echo "${C_B}[INFO]${C_N} $*"; }
ok()    { echo "${C_G}[ OK ]${C_N} $*"; }
warn()  { echo "${C_Y}[WARN]${C_N} $*"; }
err()   { echo "${C_R}[ERR ]${C_N} $*" >&2; }

# ---------- args ----------
DRY_RUN=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        --help|-h)
            sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) err "unknown flag: $arg"; exit 2 ;;
    esac
done

# ---------- step 1: validate ----------
info "Step 1/4: validating environment"

[[ -d "$PAPER_DIR" ]] || { err "paper dir not found: $PAPER_DIR"; exit 1; }
[[ -f "$PAPER_DIR/$MAIN_TEX" ]] || { err "main tex not found: $PAPER_DIR/$MAIN_TEX"; exit 1; }
[[ -f "$PAPER_DIR/$BIB_FILE" ]] || { err "bib file not found: $PAPER_DIR/$BIB_FILE"; exit 1; }
[[ -d "$PAPER_DIR/sections" ]] || warn "sections/ dir not found (optional)"
[[ -d "$PAPER_DIR/figures" ]]  || warn "figures/ dir not found (optional)"

ENGINE=""
if command -v pdflatex >/dev/null 2>&1; then
    ENGINE="pdflatex"
elif command -v tectonic >/dev/null 2>&1; then
    ENGINE="tectonic"
else
    err "no LaTeX engine found (need pdflatex or tectonic)"
    err "install: TeX Live (apt install texlive-full) or tectonic (cargo install tectonic)"
    exit 1
fi
ok "LaTeX engine: $ENGINE"

if [[ "$ENGINE" == "pdflatex" ]] && ! command -v bibtex >/dev/null 2>&1; then
    err "pdflatex found but bibtex missing — install texlive-bibtex-extra"
    exit 1
fi

if [[ $DRY_RUN -eq 1 ]]; then
    ok "dry-run complete; environment OK. Re-run without --dry-run to build."
    exit 0
fi

# ---------- step 2: compile ----------
info "Step 2/4: compiling $MAIN_TEX with $ENGINE"
cd "$PAPER_DIR"

run_latex() {
    local pass="$1"
    info "  pdflatex pass $pass"
    if ! pdflatex -interaction=nonstopmode -halt-on-error "$MAIN_TEX" > "/tmp/${MAIN_STEM}_pass${pass}.log" 2>&1; then
        err "pdflatex pass $pass failed. First error context:"
        grep -nE '^(!|l\.[0-9]+|.*Error)' "/tmp/${MAIN_STEM}_pass${pass}.log" | head -20 >&2 || true
        err "full log: /tmp/${MAIN_STEM}_pass${pass}.log"
        err "or inspect: $PAPER_DIR/${MAIN_STEM}.log"
        exit 1
    fi
}

if [[ "$ENGINE" == "tectonic" ]]; then
    info "  tectonic single-pass (auto bib + reruns)"
    if ! tectonic --keep-intermediates --reruns 3 "$MAIN_TEX" > /tmp/tectonic.log 2>&1; then
        err "tectonic compile failed. Tail of log:"
        tail -30 /tmp/tectonic.log >&2
        exit 1
    fi
else
    run_latex 1
    info "  bibtex"
    if ! bibtex "$MAIN_STEM" > "/tmp/${MAIN_STEM}_bibtex.log" 2>&1; then
        warn "bibtex returned nonzero; check /tmp/${MAIN_STEM}_bibtex.log (often non-fatal)"
        tail -15 "/tmp/${MAIN_STEM}_bibtex.log" >&2 || true
    fi
    run_latex 2
    run_latex 3
fi
ok "compile complete"

# ---------- step 3: verify pdf ----------
info "Step 3/4: verifying ${MAIN_STEM}.pdf"
PDF="$PAPER_DIR/${MAIN_STEM}.pdf"
[[ -f "$PDF" ]] || { err "pdf not generated: $PDF"; exit 1; }

PAGES=""
if command -v pdfinfo >/dev/null 2>&1; then
    PAGES=$(pdfinfo "$PDF" | awk '/^Pages:/ {print $2}')
elif command -v gs >/dev/null 2>&1; then
    PAGES=$(gs -q -dNODISPLAY -c "($PDF) (r) file runpdfbegin pdfpagecount = quit" 2>/dev/null || echo "")
fi

if [[ -n "$PAGES" ]]; then
    if (( PAGES < EXPECTED_PAGES_MIN )); then
        warn "pdf has $PAGES pages (expected >= $EXPECTED_PAGES_MIN). Check output."
    else
        ok "pdf: $PAGES pages"
    fi
else
    warn "no pdfinfo/gs; skipping page count check"
fi

PDF_SIZE=$(wc -c < "$PDF" 2>/dev/null || echo 0)
ok "pdf size: $PDF_SIZE bytes"

# ---------- step 4: package source tarball ----------
info "Step 4/4: packaging source tarball (no aux/log/pdf)"
cd "$PAPER_DIR"

INCLUDE=()
[[ -f "$MAIN_TEX" ]]   && INCLUDE+=("$MAIN_TEX")
[[ -f "$BIB_FILE" ]]   && INCLUDE+=("$BIB_FILE")
[[ -f "${MAIN_STEM}.bbl" ]] && INCLUDE+=("${MAIN_STEM}.bbl")  # arXiv prefers .bbl
[[ -d sections ]]      && INCLUDE+=("sections")
[[ -d figures ]]       && INCLUDE+=("figures")

rm -f "$OUT_TARBALL"
tar --exclude='*.aux' --exclude='*.log' --exclude='*.out' --exclude='*.toc' \
    --exclude='*.blg' --exclude='*.fls' --exclude='*.fdb_latexmk' \
    --exclude='*.synctex.gz' --exclude='*.pdf' \
    -czf "$OUT_TARBALL" "${INCLUDE[@]}"

TAR_SIZE=$(wc -c < "$OUT_TARBALL")
ok "tarball: $OUT_TARBALL ($TAR_SIZE bytes)"
info "tarball contents:"
tar -tzf "$OUT_TARBALL" | sed 's/^/    /'

# ---------- arXiv upload guide ----------
cat <<EOF

${C_G}========== arXiv submission guide ==========${C_N}

  1. Go to: https://arxiv.org/submit
  2. Login (or register; ORCID recommended).
  3. New Submission -> "Start a new submission".
  4. License: choose CC BY 4.0 or arXiv non-exclusive.
  5. Upload Files: pick
       ${OUT_TARBALL}
  6. Process: arXiv runs AutoTeX (~30s); fix any errors it reports.
  7. Metadata:
       - Title         (copy from \\title{} in $MAIN_TEX)
       - Authors
       - Abstract      (copy from \\begin{abstract})
       - Primary cat:  cs.CL  (computational linguistics)
       - Cross-list:   cs.IR, cs.LG  (as appropriate)
       - MSC / ACM:    optional
       - Comments:     "8 pages + appendices, code: <repo url>"
  8. Preview the rendered PDF; verify pages, figures, refs.
  9. Submit. New papers freeze ~14:00 ET; appears next announce cycle.

  Tips:
  - arXiv prefers source (.tex + .bbl + figures), not just PDF.
  - .bbl is included; arXiv may not have your bib style available.
  - Figures are TikZ -> compile in-place; no PDF figures needed.
  - If withdrawn/replaced later: keep same submission, upload v2.

${C_G}=============================================${C_N}
EOF

ok "done."
