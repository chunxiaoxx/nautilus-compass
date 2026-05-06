# Paper 2 · Figures (TikZ source)

## Files

| File | Description |
|---|---|
| `pipeline_v08.tex` | Figure 1 · 5-stage pipeline diagram with ssu rewrite annotated |
| `trajectory_v08.tex` | Figure 2 · cumulative accuracy trajectory (V-shape) · pgfplots |
| `fusion_diagram.tex` | Figure 3 · 8 platform fusion points (Nautilus × compass) |

## Render to PDF

```bash
# pdflatex (most distros)
pdflatex pipeline_v08.tex
pdflatex trajectory_v08.tex
pdflatex fusion_diagram.tex

# or via tectonic (cleaner)
tectonic pipeline_v08.tex
tectonic trajectory_v08.tex
tectonic fusion_diagram.tex
```

Output: 3 standalone PDFs · ready to `\includegraphics` into the main paper.

## Render to PNG (for README / blog)

```bash
pdftoppm -r 200 pipeline_v08.pdf pipeline_v08 -png
pdftoppm -r 200 trajectory_v08.pdf trajectory_v08 -png
pdftoppm -r 200 fusion_diagram.pdf fusion_diagram -png
```

## Use in main paper

```latex
% In main_paper.tex
\begin{figure}[t]
  \centering
  \input{figures/pipeline_v08}
  \caption{Compass v0.8 5-stage pipeline. Multi-angle query rewriting (Stage 1.5)
    is conditional on question type, applied only to single-session-user, where
    it yields the largest single gain (+27 pts).}
  \label{fig:pipeline}
\end{figure}

\begin{figure}[t]
  \centering
  \input{figures/trajectory_v08}
  \caption{Cumulative accuracy by question index. The V-shape reflects
    per-type difficulty differences (ssu peak, temporal-reasoning trough,
    ssa rebound) rather than model degradation.}
  \label{fig:trajectory}
\end{figure}

\begin{figure}[t]
  \centering
  \input{figures/fusion_diagram}
  \caption{Eight deep-fusion points between compass and the Nautilus platform.
    See Section~\ref{sec:platform_fusion} for details.}
  \label{fig:fusion}
\end{figure}
```

## Source data

Figures derive from:

- `paper/RESULTS_v0.8.md` (trajectory data points)
- `paper/results/experiments_20260505.csv` (per-type accuracy)
- `paper/PLATFORM_FUSION.md` (8 fusion points)
- `paper/sections/paper2_03_method.tex` (pipeline stages)

If you change any source · regenerate the figures (regenerate is manual ·
no auto-build hook yet).
