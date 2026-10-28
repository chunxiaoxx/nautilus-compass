def solve_instance(instance: dict) -> dict:
    n = instance["num_jobs"]
    m = instance["num_machines"]
    jobs = instance["jobs"]
    
    # Precompute remaining work for each job-op (including current op) for priority rule
    remaining_work = [[0] * m for _ in range(n)]
    for j in range(n):
        total = 0
        for k in reversed(range(m)):
            total += jobs[j][k][1]
            remaining_work[j][k] = total
    
    next_op = [0] * n
    machine_avail = [0] * m
    job_release = [0] * n
    starts = [[0] * m for _ in range(n)]
    
    # Giffler-Thompson algorithm with MWR (Most Work Remaining) priority rule
    while True:
        # Check if all operations are scheduled
        all_done = True
        for j in range(n):
            if next_op[j] < m:
                all_done = False
                break
        if all_done:
            break
        
        # Collect all ready operations
        ready = []
        for j in range(n):
            k = next_op[j]
            if k >= m:
                continue
            mach, dur = jobs[j][k]
            es = job_release[j]
            ec = max(es, machine_avail[mach]) + dur
            ready.append((ec, es, mach, dur, j, k))
        
        # Step 1: Find minimum earliest completion time across all ready ops
        C_min = min(r[0] for r in ready)
        
        # Step 2: Select conflict machine (smallest ID to break ties deterministically)
        M_candidates = [r[2] for r in ready if r[0] == C_min]
        M_star = min(M_candidates)
        
        # Step3: Build conflict set of ops eligible to be scheduled on M_star now
        conflict = []
        for r in ready:
            ec, es, mach, dur, j, k = r
            if mach == M_star and es <= C_min:
                # Priority sort keys: highest remaining work > longest op duration > lower job ID > lower op ID
                conflict.append((-remaining_work[j][k], -dur, j, k, dur))
        
        # Step4: Select highest priority op from conflict set
        conflict.sort()
        neg_rw, neg_dur, j, k, dur = conflict[0]
        
        # Step5: Schedule the selected op
        start_time = max(job_release[j], machine_avail[M_star])
        starts[j][k] = start_time
        job_release[j] = start_time + dur
        machine_avail[M_star] = start_time + dur
        next_op[j] += 1
    
    return {"starts": starts}
