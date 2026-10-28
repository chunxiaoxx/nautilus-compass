"""Nautilus coding engine · cycle 1 main module.

Minimal pipeline:
    generate(task) → parse_file_blocks(text) → write_file(path, content)

Reuses agent_engine.llm.client.LLMClient (MiniMax / Gemini / Anthropic fallback).
Defaults to dry_run=True · pass dry_run=False (or use --apply via CLI cycle 4)
to actually write files.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DEFAULT_SYSTEM_PROMPT = """You are Nautilus Engine, a focused code-generation assistant.

Output convention (strict):
- For each file to create or replace, emit a fenced code block with this header:
    ```LANG:relative/path/to/file
    <full file content>
    ```
- LANG matches the file (python, typescript, markdown, sql, yaml, etc.)
- Emit the COMPLETE final file content · do NOT use diff format
- Prose outside code blocks is allowed only as brief commentary
- Keep functions short (<50 LOC) and files focused (<400 LOC)

MINIMAL CHANGE MODE (treat the original file as ground truth):
- When task says "keep ALL other code identical" OR "only add" OR
  "only change line N" OR "minimal diff" OR "do not refactor":
  emit the complete file with ONLY the explicit change applied ·
  preserve ALL other lines byte-for-byte (imports, function names,
  signatures, control flow, comments, blank lines, whitespace)
- For small targeted edits (single docstring · single import · 1-line fix):
  do NOT rewrite logic that was not asked to change · do NOT rename
  variables · do NOT reorder statements · do NOT add error handling
  that was not requested
- Your job is the explicit ask · NOT refactoring or improving unrelated code
- When in doubt · change LESS rather than MORE · under-shipping a 1-line
  edit is recoverable · over-rewriting a working file is not

EXAMPLE · MINIMAL CHANGE applied correctly to a 6-line file:

Original `count.py`:
    import sys

    def main():
        print(sys.argv[1])

    main()

Task: "add a module docstring · keep ALL other code identical"

Correct output (emit the COMPLETE file · only docstring added):
    ```python:count.py
    \"\"\"CLI · prints the first argument.\"\"\"
    import sys

    def main():
        print(sys.argv[1])

    main()
    ```

WRONG outputs to avoid:
- Emitting only the docstring line (under-shipping · breaks the full-file convention)
- Rewriting `main` to use argparse (over-rewriting · spec said keep identical)
- Removing `import sys` because the new code doesn't need it (you did NOT
  rewrite the code · the `import sys` is still used by the unchanged `main`)
- Renaming `main` to `entry` (out of scope · not requested)
- Adding `if __name__ == "__main__":` guard (out of scope · not requested)
- Adding error handling for missing argv (out of scope · not requested)
"""

# ```LANG:PATH\n...content...\n```
_FILE_BLOCK_RE = re.compile(
    r"```(?P<lang>[a-zA-Z0-9_+\-]+):(?P<path>[^\n`]+)\n(?P<content>.*?)\n```",
    re.DOTALL,
)


class NautilusEngine:
    """Cycle 1 engine: LLM call + parse + dry-run-safe file write."""

    def __init__(
        self,
        llm_client: Any = None,
        dry_run: bool = True,
        base_dir: str = ".",
        system_prompt: str | None = None,
        repo_map: Any = None,
        repo_context_budget: int = 1000,
    ) -> None:
        self.llm = llm_client
        self.dry_run = bool(dry_run)
        self.base_dir = Path(base_dir).resolve()
        self.system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        self.repo_map = repo_map
        self.repo_context_budget = repo_context_budget

    def _ensure_llm(self) -> None:
        if self.llm is not None:
            return
        # Lazy import so unit tests can run without LLM credentials.
        from agent_engine.llm.client import get_llm_client
        self.llm = get_llm_client()

    def generate(
        self,
        task: str,
        context: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> str:
        """Call the LLM with task + optional context · return raw text.

        If no explicit context is given and a RepoMap is attached, falls back
        to repo_map.render(task) within self.repo_context_budget tokens.
        """
        self._ensure_llm()
        if not context and self.repo_map is not None:
            try:
                context = self.repo_map.render(task, token_budget=self.repo_context_budget)
            except Exception:
                context = ""
        if context:
            prompt = f"Context:\n{context}\n\nTask:\n{task}"
        else:
            prompt = task
        return self.llm.chat(
            prompt,
            system=self.system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def parse_file_blocks(self, text: str) -> list[dict]:
        """Extract file blocks from LLM output · returns list of {lang, path, content}."""
        if not text:
            return []
        return [
            {
                "lang": m.group("lang").strip(),
                "path": m.group("path").strip(),
                "content": m.group("content"),
            }
            for m in _FILE_BLOCK_RE.finditer(text)
        ]

    def write_file(self, rel_path: str, content: str) -> dict:
        """Write file under base_dir · honors dry_run · rejects path escapes."""
        target = (self.base_dir / rel_path).resolve()
        try:
            target.relative_to(self.base_dir)
        except ValueError:
            return {
                "written": False,
                "dry_run": self.dry_run,
                "error": "path_escape",
                "path": str(target),
            }

        if self.dry_run:
            return {
                "written": False,
                "dry_run": True,
                "path": str(target),
                "size": len(content),
                "preview": content[:200],
            }

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "written": True,
            "dry_run": False,
            "path": str(target),
            "size": len(content),
        }

    def run(self, task: str, context: str = "") -> dict:
        """End-to-end: generate → parse → write all blocks · returns summary."""
        raw = self.generate(task, context=context)
        blocks = self.parse_file_blocks(raw)
        results = [self.write_file(b["path"], b["content"]) for b in blocks]
        return {
            "task": task,
            "raw_response_chars": len(raw),
            "files_planned": len(blocks),
            "files_written": sum(1 for r in results if r["written"]),
            "dry_run": self.dry_run,
            "files": results,
        }
