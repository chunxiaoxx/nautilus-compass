# GitHub 跟进回复草稿

> 2026-11-19 整理。以下内容只保存为草稿，未调用 GitHub 发帖工具。总体口径是积极开放、共同复算、先建立合作入口。每条发送前再次读取 issue 当前状态。

## MemTensor/MemOS #2534

Hi — following up on our open offer for a free, independent recompute of the published memory benchmark claims.

If this is still useful, we would be glad to work with you on a small, transparent recompute. Could you point us to the current release or commit, the benchmark artifacts, and the configuration you consider fair? We will preregister the criteria before the first run, publish the harness and raw readout, and report agree, disagree, or not computable.

If there is a maintainer or benchmark owner we should coordinate with, please tag them here. If the offer is no longer relevant, a short close is also helpful. Either way, we would appreciate the chance to stay connected.

## supermemoryai/supermemory #1831

Hi — checking in on the independent verification offer. We saw the Linear linkback to ENG-1321 and would be glad to coordinate with whoever owns that evaluation. We would be happy to adapt the pilot to your current workflow.

We can use the latest public release and your recommended configuration, or freeze a version and dataset that you specify. The criteria and recompute commands will be public, and the result will be reported regardless of direction. Please let us know whether ENG-1321 is the right coordination path.

## Mirix-AI/MIRIX #141

Hi — checking whether a free, independent recompute of the published memory benchmark claims is still useful for MIRIX. We would be happy to work with the current maintainer and keep the first step small.

We can start from the latest public release, freeze the criteria before running, and publish the complete readout and commands. Please point us to the preferred version, benchmark, and configuration, or tag the maintainer who should coordinate it.

## getzep/graphiti #1950

Hi — following up on the independent verification proposal. We would be glad to work with Graphiti or Zep on a small recompute pilot. Please share the current release, the benchmark artifacts, and any configuration you consider representative.

We will preregister the measurement rule, keep agree, disagree, and not computable as separate outcomes, and publish the reproduction path. A short confirmation or a close is enough for us to route this correctly.

## mem0ai/mem0 #7514

Hi — checking whether the controlled three-arm write-compression experiment and DolphinBench recompute offer are still useful to the mem0 team. We would be glad to align the experiment with your current research priorities.

We can restate the arms, inputs, and scoring criteria in a compact preregistration and run the public artifacts independently. Please point us to the current branch or release and the maintainer who should coordinate, or let us know if this issue should be closed.

## xiaowu0162/LongMemEval-V2 #13

Hi — following up on the certification-track proposal for LongMemEval-V2. We would be glad to co-design a small first pilot with the maintainers.

We would be happy to start with a small public pilot. The proposed flow is a preregistered criteria file, a self-contained input pack, a three-state verdict, and a signed receipt that anyone can recompute. Please let us know whether this fits the project and which version of the benchmark should be frozen.

## google-agentic-commerce/a2a-x402 #198

Hi Alan — thank you for the detailed questions, and for offering a live endpoint for comparison. We are checking the exact current platform implementation before answering so that we do not describe a design intention as a production guarantee.

The short version from the public design is that settlement is recorded as durable ledger events with duplicate protection, and a stake is released only after the delivery path records the required evidence and the outcome is graded. The grading path uses the recorded before/after outcome and the no-revert signal. We will link the exact implementation and a redacted trace in a follow-up once we have re-read the current platform code.

We would also like to inspect the `settlement.*` tools using a non-destructive read-only probe and compare the two ledgers. If there is a preferred test account or fixture, please share it.
