"""skills_pkg/job_queue smoke tests · SQLite-backed."""
import sys
import os
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills_pkg.job_queue import (
    register_worker, enqueue, claim_due, complete, fail,
    reap_stale_claims, list_jobs, stats, process_due,
    STATUS_PENDING, STATUS_CLAIMED, STATUS_COMPLETED, STATUS_FAILED,
    STATUS_RETRY_PENDING, VALID_STATUSES,
)


def _db(t):
    return Path(t) / "queue.db"


def test_1_register_and_enqueue():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        r = register_worker("test-w", spec_type="cron", db_path=db)
        assert r["ok"]
        jid = enqueue("test-w", {"task": "hello"}, db_path=db)
        assert jid > 0
        jobs = list_jobs(db_path=db)
        assert len(jobs) == 1
        assert jobs[0]["status"] == STATUS_PENDING
    print("OK 1 register + enqueue")


def test_2_claim_due():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        enqueue("w", {"k": "v"}, db_path=db)
        claimed = claim_due(db_path=db)
        assert len(claimed) == 1
        assert claimed[0]["status"] == STATUS_CLAIMED
        assert claimed[0]["payload"] == {"k": "v"}
        assert claimed[0]["attempts"] == 1
    print("OK 2 claim_due")


def test_3_complete():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        enqueue("w", db_path=db)
        c = claim_due(db_path=db)
        ok = complete(c[0]["id"], {"output": "done"}, db_path=db)
        assert ok
        jobs = list_jobs(db_path=db)
        assert jobs[0]["status"] == STATUS_COMPLETED
        assert jobs[0]["result"] == {"output": "done"}
    print("OK 3 complete")


def test_4_fail_retry_then_final():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        enqueue("w", max_attempts=2, db_path=db)
        # Claim 1 · fail → retry
        c = claim_due(db_path=db)
        r = fail(c[0]["id"], error="first attempt", retry_after_sec=0, db_path=db)
        assert r["status"] == STATUS_RETRY_PENDING
        # Claim 2 · fail → final fail
        c2 = claim_due(db_path=db)
        assert len(c2) == 1
        r2 = fail(c2[0]["id"], error="second attempt", db_path=db)
        assert r2["status"] == STATUS_FAILED
        assert r2["final"]
    print("OK 4 fail retry then final")


def test_5_scheduled_at_future():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        future = time.time() + 3600  # 1h ahead
        enqueue("w", scheduled_at=future, db_path=db)
        c = claim_due(db_path=db)
        assert len(c) == 0  # not due yet
    print("OK 5 future scheduled not due")


def test_6_list_jobs_filter():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        enqueue("w1", db_path=db)
        enqueue("w2", db_path=db)
        all_jobs = list_jobs(db_path=db)
        w1_only = list_jobs(worker_name="w1", db_path=db)
        assert len(all_jobs) == 2
        assert len(w1_only) == 1
        assert w1_only[0]["worker_name"] == "w1"
    print("OK 6 list_jobs filter")


def test_7_stats():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        enqueue("w", db_path=db)
        enqueue("w", db_path=db)
        c = claim_due(db_path=db)
        complete(c[0]["id"], db_path=db)
        s = stats(db_path=db)
        assert s.get(STATUS_COMPLETED) == 1
        assert s.get(STATUS_CLAIMED, 0) + s.get(STATUS_PENDING, 0) == 1
    print("OK 7 stats")


def test_8_process_due_handler_success():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        enqueue("w", {"task": "a"}, db_path=db)
        enqueue("w", {"task": "b"}, db_path=db)
        def handler(job):
            return {"echo": job["payload"]["task"]}
        r = process_due(handler, db_path=db)
        assert r["claimed"] == 2
        assert r["completed"] == 2
        assert r["failed"] == 0
    print("OK 8 process_due all complete")


def test_9_process_due_handler_raises_marks_failed():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        enqueue("w", max_attempts=1, db_path=db)
        def bad_handler(job):
            raise RuntimeError("boom")
        r = process_due(bad_handler, db_path=db)
        assert r["claimed"] == 1
        assert r["failed"] == 1
        jobs = list_jobs(db_path=db)
        assert jobs[0]["status"] == STATUS_FAILED
        assert "boom" in (jobs[0]["error"] or "")
    print("OK 9 handler exception → job failed")


def test_10_reap_stale_claims():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        enqueue("w", db_path=db)
        claim_due(db_path=db)
        # Reap with 0 timeout · should reap immediately
        time.sleep(0.01)
        reaped = reap_stale_claims(claim_timeout_sec=0.0, db_path=db)
        assert reaped == 1
        jobs = list_jobs(status=STATUS_RETRY_PENDING, db_path=db)
        assert len(jobs) == 1
    print("OK 10 reap stale claims")


def test_11_idempotent_register():
    with tempfile.TemporaryDirectory() as t:
        db = _db(t)
        register_worker("w", spec_type="cron", db_path=db)
        r = register_worker("w", spec_type="http", db_path=db)  # re-register
        assert r["ok"]
        # No exception · second call updates spec_type
    print("OK 11 register idempotent (upsert)")


def test_12_valid_statuses_complete_set():
    assert set(VALID_STATUSES) == {STATUS_PENDING, STATUS_CLAIMED,
                                     STATUS_COMPLETED, STATUS_FAILED,
                                     STATUS_RETRY_PENDING}
    print("OK 12 status state machine complete")


if __name__ == "__main__":
    tests = [test_1_register_and_enqueue, test_2_claim_due, test_3_complete,
             test_4_fail_retry_then_final, test_5_scheduled_at_future,
             test_6_list_jobs_filter, test_7_stats, test_8_process_due_handler_success,
             test_9_process_due_handler_raises_marks_failed, test_10_reap_stale_claims,
             test_11_idempotent_register, test_12_valid_statuses_complete_set]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} job_queue smoke pass")
