Good catch — you're right, and thank you. That row was internally inconsistent: 291 held-out cases at 98.28% agreement means **5 flips** (not 2 — the "2" was a transcription of our tolerance budget, not the observed flip count). We corrected the table and surrounding text across every published surface (blog, paper draft, registry page) the same evening.

The gate verdict itself is unchanged: 98.28% < 99% → int8 fails the deployment gate either way. But the arithmetic error was ours, and it was a reader who caught it — which is exactly why we keep the per-case matrix and preregistered gate public (nautilus.social/criteria). We've also added a math self-consistency check (agreement×n vs. flip count must cohere) to our pre-publication checklist as a direct result of your comment.

We also maintain a public errata log where this is recorded with attribution: https://nautilus.social/errata.html — thanks again.
