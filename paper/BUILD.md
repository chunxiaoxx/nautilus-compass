# Building the arXiv preprint PDF

## Option A · Overleaf (recommended for first build)

1. Go to https://www.overleaf.com → New Project → Upload Project
2. Zip the entire `paper/` directory (including `figures/*.pdf`) and upload
3. Set `nautilus-compass.tex` as the main document
4. Compile: pdfLaTeX (default works)
5. Download generated PDF

Estimated time: 5 minutes including upload.

## Option B · Local TeX Live / MiKTeX

```bash
cd paper
pdflatex nautilus-compass.tex
bibtex nautilus-compass
pdflatex nautilus-compass.tex
pdflatex nautilus-compass.tex   # second pass for cross-refs
```

Required packages: `geometry`, `inputenc`, `fontenc`, `microtype`, `graphicx`,
`booktabs`, `hyperref`, `xcolor`, `listings`, `url`, `caption`, `cite`,
`amsmath`. All are in standard TeX Live distribution.

## Option C · GitHub Actions (automated on every push)

The repository ships with `.github/workflows/build-paper.yml`. Every push
that touches `paper/**` triggers a LaTeX compile, and the resulting PDF
is published as a workflow artifact (downloadable from the Actions tab).

To trigger manually:

```bash
gh workflow run build-paper.yml
gh run list --workflow=build-paper.yml --limit=1
gh run download <run-id>   # downloads paper-pdf artifact
```

## arXiv submission

1. Compile PDF locally or via Overleaf/Actions
2. Bundle source: `tar czf nautilus-compass-arxiv.tar.gz paper/nautilus-compass.tex paper/sections/ paper/figures/*.pdf paper/refs.bib`
3. Go to https://arxiv.org/submit
4. Category: `cs.CL` primary, `cs.AI` secondary
5. License: CC BY 4.0 recommended
6. Paste abstract from `paper/sections/00_abstract.tex` (strip LaTeX formatting)
7. Endorsement may be required for first-time submitters in cs.CL — see https://arxiv.org/help/endorsement
