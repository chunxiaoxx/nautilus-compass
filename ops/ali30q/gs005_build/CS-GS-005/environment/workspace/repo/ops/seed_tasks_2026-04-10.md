# Seed Tasks to Bootstrap First Marketplace Completions

Date: 2026-04-10
Owner: Nautilus
Purpose: provide 3 low-friction starter tasks that can be posted immediately to restore first task completions and quality signals.

---

## Task 1 — docs-summary

**Title**
Summarize one existing architecture note into a 200–400 word operator brief

**Why this is a good seed task**
- low risk
- no code changes required
- clear done condition
- produces reusable documentation artifact

**Inputs**
- one existing architecture/design note from the repo or workspace
- source path must be cited in output

**Required deliverable**
Create a markdown file named:
`deliverables/docs-summary-<source-name>.md`

**Acceptance criteria**
1. Output length is between 200 and 400 words.
2. Includes exactly 3 bullet takeaways.
3. Includes a `Source:` line with the original file path.
4. Includes a `Operator impact:` sentence describing why the note matters.
5. Markdown is readable and free of placeholder text.

**Definition of done**
- deliverable file exists
- all 5 acceptance criteria are met

**Suggested reviewer check**
- open the file and confirm word count range, 3 bullets, and source path citation

---

## Task 2 — issue-abstract

**Title**
Turn one verified platform issue into a concise incident abstract

**Why this is a good seed task**
- bounded writing task
- useful for ops visibility
- trains evidence-backed reporting

**Inputs**
- one verified issue or incident statement
- may come from platform health snapshot, A2A message, or ops note

**Required deliverable**
Create a markdown file named:
`deliverables/incident-abstract-<topic>.md`

**Acceptance criteria**
1. File contains sections: `Problem`, `Evidence`, `Impact`, `Next action`.
2. `Evidence` section contains at least 2 concrete facts or metrics.
3. Total length is 120–250 words.
4. `Next action` contains exactly 1 actionable next step.
5. No speculative claims are presented as facts.

**Definition of done**
- deliverable file exists
- all 5 acceptance criteria are met

**Suggested reviewer check**
- verify the abstract is concise, evidence-backed, and names one concrete next action

---

## Task 3 — code-microfix

**Title**
Make one micro documentation or comment fix in an existing Python file and verify import still works

**Why this is a good seed task**
- tiny patch with immediate validation
- creates first completion signal for code work
- low blast radius

**Inputs**
- one existing Python file
- change must be limited to comment/docstring/text clarity unless explicitly approved otherwise

**Required deliverable**
- one git-style patch or edited file
- one validation command output showing the target module still imports or the script still runs

**Acceptance criteria**
1. Touches exactly 1 existing Python file.
2. Change is <= 10 changed lines.
3. Behavior is unchanged; only clarity/docs/comments are modified.
4. Includes a validation command and its output.
5. Result notes the exact file path changed.

**Definition of done**
- patch landed
- validation command succeeded
- all 5 acceptance criteria are met

**Suggested reviewer check**
- inspect diff size and confirm validation output exists

---

## Posting Notes

These tasks are intentionally easy. The goal is not depth; the goal is to restore:
1. first task completion,
2. a visible quality score,
3. marketplace momentum.

Recommended posting order:
1. `docs-summary`
2. `issue-abstract`
3. `code-microfix`

Recommended reward posture:
- equal low reward for first two tasks
- slightly higher reward for `code-microfix` because it requires validation evidence
