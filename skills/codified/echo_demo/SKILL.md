---
name: echo_demo
status: codified
version: 0.1.0
description: Tiny demo skill for 5-step cycle verification · echoes input · concept stage starting point.
inputs:
  - message (str)
outputs:
  - echo (str): same as input
---

# echo_demo

A minimal skill at the concept stage. Used to verify that
`skill_registry.promote()` correctly moves files between
`skills/concepts/` → `skills/prototypes/` → `skills/codified/`.

Real intent: validate the 5-step cycle wiring works end-to-end.
