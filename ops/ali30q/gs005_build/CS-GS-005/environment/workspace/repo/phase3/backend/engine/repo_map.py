"""Repository Map for Nautilus Engine cycle 2.

Lightweight code-context extraction · Python stdlib `ast` only ·
no tree-sitter / networkx dependencies.

Pipeline:
    scan() → parse_file() per .py → rank_files(task) → render(task, budget)

Designed to fit in NautilusEngine.generate() context within a token budget
so the LLM sees relevant class/function signatures instead of full files.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# Chars-per-token approximation for budget enforcement.
# OK for prose · code averages ~3.5 chars/token but we err on the side of
# under-filling rather than overflowing.
CHARS_PER_TOKEN = 4

DEFAULT_EXCLUDE = frozenset({
    "__pycache__", ".git", "node_modules", "venv", ".venv",
    "build", "dist", ".next", "coverage", ".cache",
    "_siblings", ".claude", ".pytest_cache", "egg-info",
})


@dataclass
class Symbol:
    name: str
    kind: str  # "class" | "function"
    signature: str
    lineno: int
    docstring: str = ""


@dataclass
class FileSymbols:
    rel_path: str
    classes: list[Symbol] = field(default_factory=list)
    functions: list[Symbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


def _identifier_terms(text: str) -> set[str]:
    """Tokenize text into lowercase identifier terms."""
    if not text:
        return set()
    return {t.lower() for t in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]+", text)}


class RepoMap:
    """Scan a Python project · extract top-level symbols · rank by task relevance."""

    def __init__(
        self,
        root_dir: str,
        exclude_dirs: Iterable[str] | None = None,
    ) -> None:
        self.root = Path(root_dir).resolve()
        self.exclude = set(DEFAULT_EXCLUDE) | set(exclude_dirs or [])
        self._files: dict[str, FileSymbols] = {}
        self._scanned = False

    # ---------- public API ----------

    def scan(self) -> dict[str, FileSymbols]:
        """Walk root · parse every .py file · cache results."""
        self._files.clear()
        for path in self._walk_py():
            try:
                fs = self.parse_file(path)
                self._files[fs.rel_path] = fs
            except Exception:
                # Never blow up scan on a single bad file.
                continue
        self._scanned = True
        return self._files

    def parse_file(self, abs_path: Path) -> FileSymbols:
        """Extract top-level symbols from a single .py file."""
        rel = self._to_rel(abs_path)
        fs = FileSymbols(rel_path=rel)
        try:
            source = abs_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError, OSError):
            return fs

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                fs.classes.append(self._sym_from_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fs.functions.append(self._sym_from_func(node))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                fs.imports.extend(self._extract_imports(node))
        return fs

    def rank_files(self, task: str) -> list[tuple[float, FileSymbols]]:
        """Score each scanned file by lexical match against task terms."""
        if not self._scanned:
            self.scan()
        task_terms = _identifier_terms(task)
        if not task_terms:
            return []

        scored: list[tuple[float, FileSymbols]] = []
        for fs in self._files.values():
            score = self._score_file(fs, task_terms)
            if score > 0:
                scored.append((score, fs))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def render(self, task: str, token_budget: int = 1000) -> str:
        """Render top-ranked files + symbols into a context string within budget."""
        ranked = self.rank_files(task)
        if not ranked:
            return ""

        char_budget = max(token_budget, 0) * CHARS_PER_TOKEN
        header = "Repository Map (lexically-ranked · top symbols):"
        chunks: list[str] = [header]
        used = len(header)

        for score, fs in ranked:
            file_line = f"\n- {fs.rel_path}  (score={score:.1f})"
            if used + len(file_line) > char_budget:
                break
            chunks.append(file_line)
            used += len(file_line)

            for sym in fs.classes + fs.functions:
                first = sym.docstring.split("\n", 1)[0].strip() if sym.docstring else ""
                suffix = f"  # {first}" if first else ""
                sym_line = f"\n    - {sym.signature}{suffix}"
                if used + len(sym_line) > char_budget:
                    return "".join(chunks)
                chunks.append(sym_line)
                used += len(sym_line)

        return "".join(chunks)

    # ---------- helpers ----------

    def _walk_py(self) -> Iterable[Path]:
        for path in self.root.rglob("*.py"):
            try:
                rel = path.relative_to(self.root)
            except ValueError:
                continue
            # Only check parts BELOW root · prevents false positives when
            # self.root itself lives under a path like .claude/worktrees/...
            if set(rel.parts) & self.exclude:
                continue
            yield path

    def _to_rel(self, abs_path: Path) -> str:
        try:
            return str(abs_path.relative_to(self.root)).replace("\\", "/")
        except ValueError:
            return str(abs_path).replace("\\", "/")

    def _sym_from_class(self, node: ast.ClassDef) -> Symbol:
        bases = [ast.unparse(b) for b in node.bases]
        sig = f"class {node.name}" + (f"({', '.join(bases)})" if bases else "")
        return Symbol(
            name=node.name,
            kind="class",
            signature=sig,
            lineno=node.lineno,
            docstring=ast.get_docstring(node) or "",
        )

    def _sym_from_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Symbol:
        args = ast.unparse(node.args)
        ret = ast.unparse(node.returns) if node.returns else "None"
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        sig = f"{prefix} {node.name}({args}) -> {ret}"
        return Symbol(
            name=node.name,
            kind="function",
            signature=sig,
            lineno=node.lineno,
            docstring=ast.get_docstring(node) or "",
        )

    def _extract_imports(self, node: ast.Import | ast.ImportFrom) -> list[str]:
        if isinstance(node, ast.Import):
            return [n.name for n in node.names]
        # ImportFrom
        mod = node.module or ""
        if not mod:
            return [n.name for n in node.names]
        return [f"{mod}.{n.name}" for n in node.names]

    def _score_file(self, fs: FileSymbols, task_terms: set[str]) -> float:
        score = 0.0
        # Path lexical match (weight 2.0 per overlap term)
        path_terms = _identifier_terms(fs.rel_path)
        score += len(task_terms & path_terms) * 2.0
        # Symbol name match (weight 3.0 exact · 1.0 substring)
        for sym in fs.classes + fs.functions:
            name_lc = sym.name.lower()
            if name_lc in task_terms:
                score += 3.0
            else:
                for term in task_terms:
                    if len(term) > 3 and term in name_lc:
                        score += 1.0
        # Popularity acts as a tiebreaker · not a baseline (skip if no lexical match).
        if score > 0:
            score += min(len(fs.imports), 10) * 0.1
        return score