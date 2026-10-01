One mem0 config flag costs 7 points on our AI memory audit benchmark.

Same backbone. Same 30 questions. Only the memory path changed:

→ Direct access: 16/18
→ mem0 default (semantic compression ON): 11/18
→ mem0 with compression OFF: 18/18

The compression rewrites structured logs into prose — dropping the exact machine-checkable fields that audits need.

If your agents run in compliance/forensics: turn it off.

(3-arm controlled experiment, full artifacts linked in bio)
