import time

import pytest

from mcp_durable.event_store import EventStore


def test_append_assigns_monotonic_ids():
    es = EventStore(max_events=100, ttl_seconds=300)
    a = es.append({"method": "notifications/message", "params": {"x": 1}})
    b = es.append({"method": "notifications/message", "params": {"x": 2}})
    assert b > a == 1  # ids start at 1, strictly increasing


def test_replay_since_returns_only_newer():
    es = EventStore(max_events=100, ttl_seconds=300)
    for i in range(5):
        es.append({"i": i})
    got = es.replay_since(2)            # client saw up to id=2
    assert [e["id"] for e in got] == [3, 4, 5]


def test_replay_since_zero_returns_all():
    es = EventStore(max_events=100, ttl_seconds=300)
    es.append({"i": 0})
    assert len(es.replay_since(0)) == 1


def test_bounded_by_max_events_drops_oldest():
    es = EventStore(max_events=3, ttl_seconds=300)
    for i in range(5):
        es.append({"i": i})
    ids = [e["id"] for e in es.replay_since(0)]
    assert ids == [3, 4, 5]            # oldest two evicted


def test_replay_below_window_floor_signals_gap():
    # client's last id fell out of the retained window -> caller must full-resync
    es = EventStore(max_events=2, ttl_seconds=300)
    for i in range(5):
        es.append({"i": i})
    assert es.replay_since(1) is None   # None = "too old, resync"


def test_ttl_evicts_old_events_using_injected_clock():
    t = {"now": 1000.0}
    es = EventStore(max_events=100, ttl_seconds=10, now_fn=lambda: t["now"])
    es.append({"i": 0})            # ts=1000
    t["now"] = 1005.0
    es.append({"i": 1})            # ts=1005
    t["now"] = 1012.0             # id=1 (ts=1000) now older than ttl=10
    es.append({"i": 2})            # append triggers ttl eviction of id=1
    ids = [e["id"] for e in es.replay_since(0)]
    assert 1 not in ids and 3 in ids


def test_negative_max_events_rejected():
    with pytest.raises(ValueError):
        EventStore(max_events=-1, ttl_seconds=300)


def test_max_events_zero_allowed_retains_nothing():
    es = EventStore(max_events=0, ttl_seconds=300)
    es.append({"i": 0})
    assert es.replay_since(0) == []


def test_replay_does_not_alias_internal_store():
    es = EventStore(max_events=100, ttl_seconds=300)
    es.append({"x": 0})
    r = es.replay_since(0)
    r[0]["frame"]["x"] = 999          # mutate the returned event
    again = es.replay_since(0)
    assert again[0]["frame"]["x"] == 0  # store must be untouched


def test_ttl_evicted_last_seen_id_signals_gap():
    t = {"now": 1000.0}
    es = EventStore(max_events=100, ttl_seconds=10, now_fn=lambda: t["now"])
    es.append({"i": 0})            # id=1, ts=1000
    es.append({"i": 1})            # id=2, ts=1000
    t["now"] = 1012.0             # ttl=10 -> ids 1,2 (ts=1000) now expired
    es.append({"i": 2})            # id=3, append evicts 1 and 2
    # client last saw id=1, which has been ttl-evicted -> unfillable gap
    assert es.replay_since(1) is None


def test_concurrent_appends_yield_unique_contiguous_ids():
    """A session-scoped store is shared across OS threads (same session_key on
    parallel connections). `append` must be atomic: no duplicate / non-monotonic
    ids, and — with a large enough window so nothing evicts — a contiguous set
    1..N. Also hammer `replay_since` concurrently to surface list races.
    """
    import threading

    n_threads = 8
    per_thread = 500
    total = n_threads * per_thread

    # now_fn yields the GIL (time.sleep(0)) on every append. append reads
    # self._now_fn() to timestamp the event; if the read-modify-write of the id
    # is NOT lock-protected, this yield lets another thread interleave between
    # `event_id = self._next_id` and `self._next_id += 1`, handing out a
    # duplicate id. With a proper lock the whole append body is atomic and ids
    # stay unique even though now_fn yields. Window > total so eviction never
    # fires → ids must be exactly 1..total. now_fn injection stays intact.
    def yielding_clock() -> float:
        time.sleep(0)
        return 1000.0
    es = EventStore(max_events=total + 10, ttl_seconds=10_000,
                    now_fn=yielding_clock)

    collected: list[list[int]] = [[] for _ in range(n_threads)]
    start = threading.Event()

    def worker(idx: int) -> None:
        start.wait()
        local = collected[idx]
        for j in range(per_thread):
            local.append(es.append({"t": idx, "j": j}))
            if j % 50 == 0:
                # Concurrent reader: must never raise mid-eviction/iteration.
                es.replay_since(0)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    start.set()
    for t in threads:
        t.join()

    all_ids = [i for sub in collected for i in sub]
    assert len(all_ids) == total
    # No duplicates (atomic id allocation).
    assert len(set(all_ids)) == total, "duplicate _eid handed out across threads"
    # Contiguous monotonic set 1..total (no gaps since nothing evicted).
    assert set(all_ids) == set(range(1, total + 1))
    # Store's own view is internally consistent and ascending.
    store_ids = [e["id"] for e in es.replay_since(0)]
    assert store_ids == sorted(store_ids)
    assert len(set(store_ids)) == len(store_ids)
