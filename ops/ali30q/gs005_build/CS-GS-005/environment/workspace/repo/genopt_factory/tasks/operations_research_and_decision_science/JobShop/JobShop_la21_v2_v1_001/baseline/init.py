"""Baseline solver: naive job-order list scheduling.

Feasible but clearly suboptimal starting point. Operations are dispatched
job-by-job in input order; each operation starts as soon as both its job
predecessor and its machine are free. No look-ahead, no prioritization,
no local search.
"""


def solve_instance(instance: dict) -> dict:
    num_jobs = instance["num_jobs"]
    num_machines = instance["num_machines"]
    jobs = instance["jobs"]

    machine_ready = [0] * num_machines
    starts = []
    for j in range(num_jobs):
        job_ready = 0
        job_starts = []
        for machine_id, duration in jobs[j]:
            s = max(job_ready, machine_ready[machine_id])
            job_starts.append(s)
            job_ready = s + duration
            machine_ready[machine_id] = s + duration
        starts.append(job_starts)

    return {"starts": starts}
