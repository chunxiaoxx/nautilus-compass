#!/usr/bin/env bash
# Build arxiv-ready submission tarball for paper2.
#
# Usage:  cd paper && ./build_arxiv.sh
# Output: arxiv_submission_YYYYMMDD.tar.gz · upload to arxiv.org
#
# Requires: pdflatex · bibtex · tar
# Tested with TeXLive 2023+.

set -euo pipefail

DATE=$(date +%Y%m%d)
TARBALL="arxiv_submission_${DATE}.tar.gz"
WORKDIR=$(mktemp -d)
trap 'rm -rf "${WORKDIR}"' EXIT

cd "$(dirname "$0")"
SRC=$(pwd)

echo "[arxiv-build] copying sources to ${WORKDIR}"
cp paper2_main.tex     "${WORKDIR}/"
cp paper2_refs.bib     "${WORKDIR}/"
mkdir -p               "${WORKDIR}/sections"
cp sections/paper2_*.tex "${WORKDIR}/sections/"

# Optional figures · build standalone tikz tex into PDF first
if [ -d figures ]; then
    cp -r figures      "${WORKDIR}/" 2>/dev/null || true
    pushd "${WORKDIR}/figures" >/dev/null
    for tex in *.tex; do
        [ -f "$tex" ] || continue
        # only compile standalone-class figures (skip readme/non-tex)
        if grep -q '{standalone}' "$tex"; then
            echo "[arxiv-build] compiling figure: $tex"
            pdflatex -interaction=nonstopmode "$tex" >/dev/null 2>&1 || \
                echo "[arxiv-build] WARN: figure $tex failed (continuing)"
        fi
    done
    popd >/dev/null
fi

cd "${WORKDIR}"

# pdflatex sufficient (paper has no Chinese glyphs · only \textyen)
LATEX="pdflatex"
echo "[arxiv-build] using ${LATEX}"

echo "[arxiv-build] running ${LATEX} (1/3)"
${LATEX} -interaction=nonstopmode paper2_main.tex > /dev/null 2>&1 || {
    echo "[arxiv-build] pass 1 failed · checking log"
    tail -50 paper2_main.log | grep -E "Error|Undefined|!"
    exit 1
}

echo "[arxiv-build] running bibtex"
bibtex paper2_main > /dev/null 2>&1 || true

echo "[arxiv-build] running ${LATEX} (2/3, 3/3)"
${LATEX} -interaction=nonstopmode paper2_main.tex > /dev/null 2>&1
${LATEX} -interaction=nonstopmode paper2_main.tex > /dev/null 2>&1

if [ ! -f paper2_main.pdf ]; then
    echo "[arxiv-build] FAILED · paper2_main.pdf missing"
    tail -30 paper2_main.log
    exit 1
fi

# Page count + size
PAGES=$(pdfinfo paper2_main.pdf 2>/dev/null | awk '/^Pages:/ {print $2}')
SIZE=$(du -sh paper2_main.pdf | awk '{print $1}')
echo "[arxiv-build] PDF built · ${PAGES} pages · ${SIZE}"

# Generate .bbl from bibtex (arxiv prefers it)
if [ -f paper2_main.bbl ]; then
    cp paper2_main.bbl "${SRC}/"
    echo "[arxiv-build] .bbl copied to ${SRC}/"
fi

# Save the PDF for review
cp paper2_main.pdf "${SRC}/paper2_main.pdf"
echo "[arxiv-build] PDF copied to ${SRC}/paper2_main.pdf"

# Build tarball: include .tex + .bbl + .bib + figures
echo "[arxiv-build] building ${TARBALL}"
cd "${WORKDIR}"
tar czf "${SRC}/${TARBALL}" \
    paper2_main.tex \
    paper2_refs.bib \
    paper2_main.bbl \
    sections/ \
    $([ -d figures ] && echo figures/)

cd "${SRC}"
echo
echo "✅ ARXIV TARBALL READY:"
echo "   ${SRC}/${TARBALL}"
echo "   $(du -sh "${TARBALL}" | awk '{print $1}')"
echo
echo "Upload to arxiv.org (after registering):"
echo "  1. https://arxiv.org/submit"
echo "  2. Category: cs.IR (Information Retrieval) · alt: cs.LG"
echo "  3. Upload ${TARBALL}"
echo "  4. arxiv compiles · check the auto-generated PDF matches paper2_main.pdf"
