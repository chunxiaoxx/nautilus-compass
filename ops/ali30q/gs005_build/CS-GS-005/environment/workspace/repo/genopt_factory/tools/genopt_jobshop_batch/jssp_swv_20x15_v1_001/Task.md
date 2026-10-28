# Job-Shop Scheduling: Minimize Makespan (Storer-Wu-Vaccari 20 jobs x 15 machines)

## Problem
Minimize the makespan on OR-Library JSSP instances: swv06, swv07, swv08, swv09, swv10.
Each instance has jobs with an ordered sequence of (machine, duration) operations.
Precedence + machine-capacity + no-preemption constraints apply.

## What to implement
Edit `baseline/init.py`, keep `solve_instance(instance) -> {"starts": [[int]]}`.
`starts[j][k]` = start time of op k of job j. Minimize the makespan.

## Verify current score
`python verification/evaluate.py --benchmark-dir . --candidate baseline/init.py`
Score per instance = 100 * optimum / makespan; combined = mean over feasible instances; any infeasible => valid=0.
