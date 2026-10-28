# Job-Shop Scheduling: Minimize Makespan (Lawrence 15 jobs x 10 machines)

## Problem
Minimize the makespan on OR-Library JSSP instances: la21, la22, la23, la24, la25.
Each instance has jobs with an ordered sequence of (machine, duration) operations.
Precedence + machine-capacity + no-preemption constraints apply.

## What to implement
Edit `baseline/init.py`, keep `solve_instance(instance) -> {"starts": [[int]]}`.
`starts[j][k]` = start time of op k of job j. Minimize the makespan.

## Verify current score
`python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py`
Score per instance = 100 * optimum / makespan; combined = mean over feasible instances; any infeasible => valid=0.
