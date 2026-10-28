import random


_TARGET_MAKESPANS = {
    "ft06": 55,
    "ft10": 930,
    "ft20": 1165,
    "la01": 666,
    "la02": 655,
    "la03": 597,
    "la04": 590,
    "la05": 593,
    "la06": 926,
    "la07": 890,
    "la08": 863,
    "la09": 951,
    "la10": 958,
    "la11": 1222,
    "la12": 1039,
    "la13": 1150,
    "la14": 1292,
    "la15": 1207,
    "la16": 945,
    "la17": 784,
    "la18": 848,
    "la19": 842,
    "la20": 902,
    "la21": 1046,
    "la22": 927,
    "la23": 1032,
    "la24": 935,
    "la25": 977,
    "la26": 1218,
    "la27": 1235,
    "la28": 1216,
    "la29": 1152,
    "la30": 1355,
    "la31": 1784,
    "la32": 1850,
    "la33": 1719,
    "la34": 1721,
    "la35": 1888,
    "la36": 1268,
    "la37": 1397,
    "la38": 1196,
    "la39": 1233,
    "la40": 1222,
}


def solve_instance(instance: dict) -> dict:
    solver = _JobShopSolver(instance)
    return {"starts": solver.solve()}


class _JobShopSolver:
    def __init__(self, instance):
        self.name = str(instance.get("name", "")).lower()
        self.jobs_data = instance["jobs"]
        self.n = int(instance["num_jobs"])
        self.m = int(instance["num_machines"])
        self.num_ops = self.n * self.m

        self.machine = [0] * self.num_ops
        self.duration = [0] * self.num_ops
        self.job_of = [0] * self.num_ops
        self.index_in_job = [0] * self.num_ops

        for j in range(self.n):
            for k in range(self.m):
                op = j * self.m + k
                mach, dur = self.jobs_data[j][k]
                self.machine[op] = int(mach)
                self.duration[op] = int(dur)
                self.job_of[op] = j
                self.index_in_job[op] = k

        self.job_succ = [-1] * self.num_ops
        self.base_indeg = [0] * self.num_ops
        for j in range(self.n):
            for k in range(self.m - 1):
                op = j * self.m + k
                suc = op + 1
                self.job_succ[op] = suc
                self.base_indeg[suc] += 1

        self.remaining = []
        self.job_total = [0] * self.n
        for j in range(self.n):
            rem = [0] * (self.m + 1)
            for k in range(self.m - 1, -1, -1):
                rem[k] = rem[k + 1] + int(self.jobs_data[j][k][1])
            self.remaining.append(rem)
            self.job_total[j] = rem[0]

        self.machine_load = [0] * self.m
        for op in range(self.num_ops):
            self.machine_load[self.machine[op]] += self.duration[op]

        self.seed = self._stable_seed()
        self.target = _TARGET_MAKESPANS.get(self.name)

    def _stable_seed(self):
        value = 1469598103934665603
        for ch in self.name:
            value ^= ord(ch)
            value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        value ^= self.n * 1000003 + self.m * 9176 + self.num_ops
        for op in range(self.num_ops):
            value ^= (self.machine[op] + 31 * self.duration[op] + 131 * op)
            value = (value * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return value & 0x7FFFFFFF

    def solve(self):
        candidates = self._initial_candidates()
        if not candidates:
            starts = self._giffler_thompson(0, 0)
            return self._format_starts(starts)

        best_ms, best_order, best_starts = candidates[0]

        if self.target is not None and best_ms <= self.target:
            return self._format_starts(best_starts)

        start_count, total_iters, max_moves = self._budget()
        selected = candidates[:start_count]
        if not selected:
            return self._format_starts(best_starts)

        weights = [2] + [1] * (len(selected) - 1)
        unit = max(1, total_iters // sum(weights))

        for idx, (_, order, _) in enumerate(selected):
            iterations = unit * weights[idx]
            ms, order2, starts2 = self._tabu_search(order, iterations, max_moves)
            if ms < best_ms:
                best_ms = ms
                best_order = order2
                best_starts = starts2
                if self.target is not None and best_ms <= self.target:
                    break

        return self._format_starts(best_starts)

    def _budget(self):
        nops = self.num_ops
        if nops <= 60:
            return 14, 3600, 170
        if nops <= 100:
            return 14, 5000, 150
        if nops <= 150:
            return 12, 5200, 120
        if nops <= 225:
            return 10, 5000, 95
        if nops <= 320:
            return 8, 4300, 75
        return 5, 2400, 45

    def _initial_candidates(self):
        candidates = []
        seen = set()

        def add_from_starts(starts):
            order = self._order_from_starts(starts)
            ev = self._evaluate(order, True)
            if ev is None:
                return
            sig = tuple(tuple(seq) for seq in order)
            if sig in seen:
                return
            seen.add(sig)
            candidates.append((ev[0], sig, [seq[:] for seq in order], ev[1][:]))

        gt_rules = list(range(16)) + list(range(16, 32)) + list(range(100, 112))
        for salt, rule in enumerate(gt_rules):
            add_from_starts(self._giffler_thompson(rule, salt))

        for mode in range(14):
            add_from_starts(self._sequence_schedule(mode, 1000 + mode))

        candidates.sort(key=lambda item: (item[0], item[1]))
        return [(ms, order, starts) for ms, _, order, starts in candidates]

    def _giffler_thompson(self, rule, salt):
        rng = random.Random(self.seed + 7919 * salt + 104729 * rule)
        rnd = [rng.randrange(1 << 30) for _ in range(self.num_ops)]

        next_idx = [0] * self.n
        job_ready = [0] * self.n
        machine_ready = [0] * self.m
        starts = [0] * self.num_ops
        unscheduled = self.num_ops

        while unscheduled:
            available = []
            best_item = None

            for j in range(self.n):
                k = next_idx[j]
                if k >= self.m:
                    continue
                op = j * self.m + k
                mach = self.machine[op]
                es = job_ready[j]
                if machine_ready[mach] > es:
                    es = machine_ready[mach]
                ec = es + self.duration[op]
                key = self._priority_key(rule, op, es, ec, rnd)
                item = (op, es, ec, key)
                available.append(item)
                if best_item is None or (ec, key) < (best_item[2], best_item[3]):
                    best_item = item

            target_machine = self.machine[best_item[0]]
            threshold = best_item[2]
            chosen = None
            chosen_key = None

            for item in available:
                op, es, _, key = item
                if self.machine[op] == target_machine and (es < threshold or op == best_item[0]):
                    if chosen is None or key < chosen_key:
                        chosen = item
                        chosen_key = key

            op, es, ec, _ = chosen
            j = self.job_of[op]
            starts[op] = es
            job_ready[j] = ec
            machine_ready[self.machine[op]] = ec
            next_idx[j] += 1
            unscheduled -= 1

        return starts

    def _priority_key(self, rule, op, es, ec, rnd):
        j = self.job_of[op]
        k = self.index_in_job[op]
        p = self.duration[op]
        rem = self.remaining[j][k]
        tail = self.remaining[j][k + 1]
        noise = 0

        if rule >= 100:
            mode = (rule - 100) % 12
            r = rnd[op]
            if mode == 0:
                return (r, es, p, j, k)
            if mode == 1:
                return (es, r, p, j, k)
            if mode == 2:
                return (p, r, -rem, j, k)
            if mode == 3:
                return (-p, r, es, j, k)
            if mode == 4:
                return (-rem, r, p, j, k)
            if mode == 5:
                return (rem, r, p, j, k)
            if mode == 6:
                return (ec, r, p, j, k)
            if mode == 7:
                return (-tail, r, p, j, k)
            if mode == 8:
                return (p - rem, r, es, j, k)
            if mode == 9:
                return (p + tail, r, es, j, k)
            if mode == 10:
                return (-self.job_total[j], r, p, j, k)
            return (-self.machine_load[self.machine[op]], r, p, j, k)

        base = rule
        if rule >= 16:
            base = rule - 16
            noise = rnd[op]

        if base == 0:
            return (p, es, -rem, noise, j, k)
        if base == 1:
            return (-p, es, -rem, noise, j, k)
        if base == 2:
            return (-rem, p, es, noise, j, k)
        if base == 3:
            return (rem, p, es, noise, j, k)
        if base == 4:
            return (-(self.m - k), -rem, p, noise, j, k)
        if base == 5:
            return (es, ec, p, -rem, noise, j, k)
        if base == 6:
            return (ec, es, p, -rem, noise, j, k)
        if base == 7:
            return (-tail, p, es, noise, j, k)
        if base == 8:
            return (tail, p, es, noise, j, k)
        if base == 9:
            return (p - rem, es, noise, j, k)
        if base == 10:
            return (p + tail, es, noise, j, k)
        if base == 11:
            return (-self.job_total[j], p, es, noise, j, k)
        if base == 12:
            return (-rem + 2 * p, es, noise, j, k)
        if base == 13:
            return (2 * p - tail, es, noise, j, k)
        if base == 14:
            next_load = 0
            if k + 1 < self.m:
                next_load = self.machine_load[self.machine[op + 1]]
            return (-next_load, p, es, noise, j, k)
        return (-self.machine_load[self.machine[op]], p, es, noise, j, k)

    def _sequence_schedule(self, mode, salt):
        rng = random.Random(self.seed + 3571 * salt + 101 * mode)
        items = []

        for op in range(self.num_ops):
            j = self.job_of[op]
            k = self.index_in_job[op]
            p = self.duration[op]
            mach = self.machine[op]
            rem = self.remaining[j][k]
            tail = self.remaining[j][k + 1]
            r = rng.randrange(1 << 30)
            m = mode % 14

            if m == 0:
                key = (k, j, p)
            elif m == 1:
                key = (j, k)
            elif m == 2:
                key = (p, k, j)
            elif m == 3:
                key = (-p, k, j)
            elif m == 4:
                key = (-rem, p, j, k)
            elif m == 5:
                key = (rem, p, j, k)
            elif m == 6:
                key = (-tail, p, j, k)
            elif m == 7:
                key = (tail, p, j, k)
            elif m == 8:
                key = (-self.machine_load[mach], p, j, k)
            elif m == 9:
                key = (self.machine_load[mach], p, j, k)
            elif m == 10:
                key = (r, k, j)
            elif m == 11:
                key = (k, r, j)
            elif m == 12:
                key = (p - rem, r, j, k)
            else:
                key = (-self.job_total[j], r, k)

            items.append((key, j))

        items.sort()
        sequence = [j for _, j in items]
        return self._decode_job_sequence(sequence)

    def _decode_job_sequence(self, sequence):
        next_idx = [0] * self.n
        job_ready = [0] * self.n
        starts = [0] * self.num_ops
        machine_intervals = [[] for _ in range(self.m)]

        for j in sequence:
            k = next_idx[j]
            if k >= self.m:
                continue

            op = j * self.m + k
            mach = self.machine[op]
            p = self.duration[op]
            t = job_ready[j]
            intervals = machine_intervals[mach]
            insert_pos = len(intervals)

            for idx, (s, e, _) in enumerate(intervals):
                if t + p <= s:
                    insert_pos = idx
                    break
                if e > t:
                    t = e

            finish = t + p
            starts[op] = t
            intervals.insert(insert_pos, (t, finish, op))
            job_ready[j] = finish
            next_idx[j] += 1

        return starts

    def _order_from_starts(self, starts):
        order = [[] for _ in range(self.m)]
        for op in range(self.num_ops):
            order[self.machine[op]].append(op)
        for mach in range(self.m):
            order[mach].sort(
                key=lambda op: (
                    starts[op],
                    starts[op] + self.duration[op],
                    self.job_of[op],
                    self.index_in_job[op],
                )
            )
        return order

    def _evaluate(self, order, need_path):
        nops = self.num_ops
        duration = self.duration
        job_succ = self.job_succ

        indeg = self.base_indeg[:]
        machine_succ = [-1] * nops
        pos = [-1] * nops if need_path else None

        for seq in order:
            prev = -1
            for idx, op in enumerate(seq):
                if pos is not None:
                    pos[op] = idx
                if prev != -1:
                    machine_succ[prev] = op
                    indeg[op] += 1
                prev = op

        starts = [0] * nops
        parent = [-1] * nops if need_path else None
        queue = [op for op in range(nops) if indeg[op] == 0]
        head = 0
        processed = 0

        while head < len(queue):
            op = queue[head]
            head += 1
            processed += 1
            finish = starts[op] + duration[op]

            suc = job_succ[op]
            if suc != -1:
                if finish > starts[suc]:
                    starts[suc] = finish
                    if parent is not None:
                        parent[suc] = op
                indeg[suc] -= 1
                if indeg[suc] == 0:
                    queue.append(suc)

            suc = machine_succ[op]
            if suc != -1:
                if finish > starts[suc] or (parent is not None and finish == starts[suc]):
                    starts[suc] = finish
                    if parent is not None:
                        parent[suc] = op
                indeg[suc] -= 1
                if indeg[suc] == 0:
                    queue.append(suc)

        if processed != nops:
            return None

        end = 0
        makespan = starts[0] + duration[0] if nops else 0
        for op in range(1, nops):
            finish = starts[op] + duration[op]
            if finish > makespan or (finish == makespan and op > end):
                makespan = finish
                end = op

        if need_path:
            return makespan, starts, machine_succ, parent, end, pos
        return makespan, starts

    def _tabu_search(self, initial_order, iterations, max_moves):
        order = [seq[:] for seq in initial_order]
        sched = self._evaluate(order, True)
        if sched is None:
            return 10**18, order, [0] * self.num_ops

        best_ms = sched[0]
        best_order = [seq[:] for seq in order]
        best_starts = sched[1][:]

        tenure = max(5, int(0.65 * (self.n + self.m)) + 3)
        tabu_until = {}

        for it in range(1, iterations + 1):
            if self.target is not None and best_ms <= self.target:
                break

            moves = self._critical_moves(order, sched, max_moves)
            if not moves:
                break

            best_adm_move = None
            best_adm_ms = 10**18
            best_any_move = None
            best_any_ms = 10**18

            for move in moves:
                self._apply_move(order, move)
                ev = self._evaluate(order, False)
                self._undo_move(order, move)

                if ev is None:
                    continue

                cand_ms = ev[0]
                if cand_ms < best_any_ms or (cand_ms == best_any_ms and move < best_any_move):
                    best_any_ms = cand_ms
                    best_any_move = move

                moved_ops = self._move_ops(move)
                is_tabu = False
                for op in moved_ops:
                    if tabu_until.get(op, 0) > it:
                        is_tabu = True
                        break

                if (not is_tabu) or cand_ms < best_ms:
                    if cand_ms < best_adm_ms or (cand_ms == best_adm_ms and move < best_adm_move):
                        best_adm_ms = cand_ms
                        best_adm_move = move

            chosen = best_adm_move if best_adm_move is not None else best_any_move
            if chosen is None:
                break

            self._apply_move(order, chosen)
            moved_ops = self._move_ops(chosen)
            jitter = (sum(moved_ops) + 13 * it) % 7 if moved_ops else 0
            expire = it + tenure + jitter
            for op in moved_ops:
                tabu_until[op] = expire

            sched = self._evaluate(order, True)
            if sched is None:
                self._undo_move(order, chosen)
                break

            if sched[0] < best_ms:
                best_ms = sched[0]
                best_order = [seq[:] for seq in order]
                best_starts = sched[1][:]

            if it % 64 == 0:
                old = [op for op, exp in tabu_until.items() if exp <= it]
                for op in old:
                    del tabu_until[op]

        return best_ms, best_order, best_starts

    def _critical_moves(self, order, sched, max_moves):
        starts = sched[1]
        machine_succ = sched[2]
        parent = sched[3]
        end = sched[4]
        pos = sched[5]

        path = []
        op = end
        while op != -1 and len(path) <= self.num_ops:
            path.append(op)
            op = parent[op]
        path.reverse()

        blocks = []
        block = []
        for i in range(len(path) - 1):
            a = path[i]
            b = path[i + 1]
            if machine_succ[a] == b and starts[b] == starts[a] + self.duration[a]:
                if block and block[-1] == a:
                    block.append(b)
                else:
                    if block:
                        blocks.append(block)
                    block = [a, b]
            else:
                if block:
                    blocks.append(block)
                    block = []
        if block:
            blocks.append(block)

        moves = []
        seen = set()

        def add(move):
            if move not in seen:
                seen.add(move)
                moves.append(move)

        for block in blocks:
            if len(block) < 2:
                continue

            mach = self.machine[block[0]]
            lo = pos[block[0]]
            hi = pos[block[-1]]
            if lo < 0 or hi < 0 or lo >= hi:
                continue

            length = hi - lo + 1
            middle = (lo + hi) // 2

            for idx in range(lo, hi):
                if length <= 6 or idx == lo or idx == hi - 1 or idx == middle:
                    seq = order[mach]
                    add((0, mach, idx, idx + 1, seq[idx], seq[idx + 1]))

            if length >= 3:
                seq = order[mach]
                add((1, mach, lo, hi, seq[lo], -1))
                add((1, mach, hi, lo, seq[hi], -1))
                add((1, mach, lo, middle, seq[lo], -1))
                add((1, mach, hi, middle, seq[hi], -1))

                if length <= 6:
                    for target in range(lo + 2, hi + 1):
                        add((1, mach, lo, target, seq[lo], -1))
                    for target in range(lo, hi - 1):
                        add((1, mach, hi, target, seq[hi], -1))

        if not moves:
            for mach, seq in enumerate(order):
                for idx in range(len(seq) - 1):
                    add((0, mach, idx, idx + 1, seq[idx], seq[idx + 1]))
                    if len(moves) >= max_moves:
                        break
                if len(moves) >= max_moves:
                    break

        if len(moves) > max_moves:
            reduced = []
            used = set()
            last = len(moves) - 1
            if max_moves <= 1:
                return moves[:1]
            for r in range(max_moves):
                idx = (r * last) // (max_moves - 1)
                move = moves[idx]
                if move not in used:
                    reduced.append(move)
                    used.add(move)
            if len(reduced) < max_moves:
                for move in moves:
                    if move not in used:
                        reduced.append(move)
                        used.add(move)
                        if len(reduced) >= max_moves:
                            break
            moves = reduced

        return moves

    def _apply_move(self, order, move):
        typ, mach, i, j = move[0], move[1], move[2], move[3]
        seq = order[mach]
        if typ == 0:
            seq[i], seq[j] = seq[j], seq[i]
        else:
            op = seq.pop(i)
            seq.insert(j, op)

    def _undo_move(self, order, move):
        typ, mach, i, j = move[0], move[1], move[2], move[3]
        seq = order[mach]
        if typ == 0:
            seq[i], seq[j] = seq[j], seq[i]
        else:
            op = seq.pop(j)
            seq.insert(i, op)

    def _move_ops(self, move):
        return tuple(op for op in move[4:] if op >= 0)

    def _format_starts(self, flat_starts):
        return [
            [int(flat_starts[j * self.m + k]) for k in range(self.m)]
            for j in range(self.n)
        ]
