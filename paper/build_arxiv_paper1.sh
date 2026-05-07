#!/usr/bin/env bash
# Build arxiv-ready submission tarball for paper 1 (drift detection).
#
# Usage:  cd paper && ./build_arxiv_paper1.sh
# Output: arxiv_paper1_YYYYMMDD.tar.gz · upload to arxiv.org
#
# Paper 1 = nautilus-compass.tex  (sections/0X_*.tex · refs.bib)
# Paper 2 = paper2_main.tex       (sections/paper2_*.tex · paper2_refs.bib)
# Use build_arxiv.sh for paper 2.
#
# Requires: pdflatex · bibtex · tar · pdfinfo
# Tested with TeXLive 2023+.

set -euo pipefail

DATE=$(date +%Y%m%d)
TARBALL="arxiv_paper1_${DATE}.tar.gz"
WORKDIR=$(mktemp -d)
trap 'rm -rf "${WORKDIR}"' EXIT

cd "$(dirname "$0")"
SRC=$(pwd)
LATEX=${LATEX:-pdflatex}

echo "[arxiv-paper1] copying sources to ${WORKDIR}"
cp nautilus-compass.tex     "${WORKDIR}/"
cp refs.bib                 "${WORKDIR}/"
mkdir -p                    "${WORKDIR}/sections"
cp sections/0[0-7]_*.tex    "${WORKDIR}/sections/"

# Optional figures
if [ -d figures ]; then
    cp -r figures "${WORKDIR}/" 2>/dev/null || true
fi

cd "${WORKDIR}"

echo "[arxiv-paper1] running ${LATEX} (1/3)"
${LATEX} -interaction=nonstopmode nautilus-compass.tex > /dev/null 2>&1 || true

echo "[arxiv-paper1] running bibtex"
bibtex nautilus-compass > /dev/null 2>&1 || true

echo "[arxiv-paper1] running ${LATEX} (2/3, 3/3)"
${LATEX} -interaction=nonstopmode nautilus-compass.tex > /dev/null 2>&1
${LATEX} -interaction=nonstopmode nautilus-compass.tex > /dev/null 2>&1

if [ ! -f nautilus-compass.pdf ]; then
    echo "[arxiv-paper1] FAILED · nautilus-compass.pdf missing"
    tail -30 nautilus-compass.log
    exit 1
fi

PAGES=$(pdfinfo nautilus-compass.pdf 2>/dev/null | awk '/^Pages:/ {print $2}')
SIZE=$(du -sh nautilus-compass.pdf | awk '{print $1}')
echo "[arxiv-paper1] PDF built · ${PAGES} pages · ${SIZE}"

# Save the PDF for review
cp nautilus-compass.pdf "${SRC}/"
echo "[arxiv-paper1] PDF copied to ${SRC}/nautilus-compass.pdf"

# Generate .bbl from bibtex (arxiv prefers it pre-built)
if [ -f nautilus-compass.bbl ]; then
    cp nautilus-compass.bbl "${SRC}/"
    echo "[arxiv-paper1] .bbl copied to ${SRC}/"
fi

# Build tarball: include .tex + .bbl + .bib + figures
echo "[arxiv-paper1] building ${TARBALL}"
tar czf "${SRC}/${TARBALL}" \
    nautilus-compass.tex \
    refs.bib \
    nautilus-compass.bbl \
    sections/ \
    $([ -d figures ] && echo figures/)

cd "${SRC}"
echo
echo "✅ ARXIV PAPER 1 TARBALL READY:"
echo "   ${SRC}/${TARBALL}"
echo "   $(du -sh "${TARBALL}" | awk '{print $1}')"
echo
echo "Upload to arxiv.org (after endorsement):"
echo "  1. https://arxiv.org/submit"
echo "  2. Primary category: cs.CL (Computation and Language)"
echo "     Cross-list: cs.LG · cs.AI"
echo "  3. Upload ${TARBALL}"
echo "  4. arxiv compiles · check the auto-generated PDF matches nautilus-compass.pdf"
