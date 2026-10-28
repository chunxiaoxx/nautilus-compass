"""Strong reference solver (upper-bound anchor, not exposed to the agent).

Giffler-Thompson active-schedule generation driven by a portfolio of
priority dispatching rules, plus a deterministic seeded random portfolio.
Pure stdlib, deterministic. Typically reaches 85-97 on the bundled set.

Interface matches baseline/init.py: solve_instance(instance) -> {"starts": ...}
"""

import random


def _giffler_thompson(instance, priority):
    num_jobs = instance["num_jobs"]
    num_machines = instance["num_machines"]
    jobs = instance["jobs"]

    next_op = [0] * num_jobs
    job_ready = [0] * num_jobs
    machine_ready = [0] * num_machines
    starts = [[0] * len(jobs[j]) for j in range(num_jobs)]
    remaining_work = [sum(d for _, d in jobs[j]) for j in range(num_jobs)]

    scheduled = 0
    total_ops = sum(len(jobs[j]) for j in range(num_jobs))
    while scheduled < total_ops:
        # earliest possible completion among all schedulable operations
        best = None
        for j in range(num_jobs):
            k = next_op[j]
            if k >= len(jobs[j]):
                continue
            m, d = jobs[j][k]
            est = max(job_ready[j], machine_ready[m])
            ect = est + d
            if best is None or ect < best[0]:
                best = (ect, m)
        ect_star, m_star = best

        # conflict set: ops on m_star that could start before ect_star
        conflict = []
        for j in range(num_jobs):
            k = next_op[j]
            if k >= len(jobs[j]):
                continue
            m, d = jobs[j][k]
            if m != m_star:
                continue
            est = max(job_ready[j], machine_ready[m])
            if est < ect_star:
                conflict.append((j, k, est, d))

        j_sel, k_sel, est_sel, d_sel = min(
            conflict, key=lambda item: priority(item, remaining_work)
        )
        starts[j_sel][k_sel] = est_sel
        end = est_sel + d_sel
        job_ready[j_sel] = end
        machine_ready[m_star] = end
        remaining_work[j_sel] -= d_sel
        next_op[j_sel] += 1
        scheduled += 1

    return starts


def _makespan(instance, starts):
    return max(
        s + d
        for j, ops in enumerate(instance["jobs"])
        for (m, d), s in zip(ops, starts[j])
    )


def solve_instance(instance: dict) -> dict:
    rules = [
        lambda it, rw: (it[3], it[2], it[0]),                  # SPT
        lambda it, rw: (-it[3], it[2], it[0]),                 # LPT
        lambda it, rw: (-rw[it[0]], it[2], it[0]),             # Most Work Remaining
        lambda it, rw: (it[2], it[3], it[0]),                  # earliest start (FIFO)
        lambda it, rw: (rw[it[0]], it[2], it[0]),              # Least Work Remaining
    ]
    candidates = [_giffler_thompson(instance, rule) for rule in rules]

    rng = random.Random(20260702)  # fixed seed: deterministic portfolio
    for _ in range(200):
        noise = [rng.random() for _ in range(instance["num_jobs"])]
        candidates.append(
            _giffler_thompson(
                instance,
                lambda it, rw, n=noise: (n[it[0]] * it[3] + it[2], it[0]),
            )
        )

    best = min(candidates, key=lambda st: _makespan(instance, st))
    return {"starts": best}
