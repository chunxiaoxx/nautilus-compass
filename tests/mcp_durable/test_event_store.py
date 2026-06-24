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
