"""R7 ProactiveEngine smoke test · priority + rate + cooldown 三道闸"""
from __future__ import annotations
import time
from nautilus_core.proactive import (
    ProactiveEngine, ProactiveTrigger, TokenBucket,
)


def test_offer_and_take_basic():
    e = ProactiveEngine(rate_capacity=10, rate_refill_per_sec=10, cooldown_sec=0.0)
    t = ProactiveTrigger(kind="evt", priority=5, payload={"x": 1})
    assert e.offer(t)
    assert e.has_pending()
    out = e.take()
    assert out is not None
    assert out.kind == "evt"
    assert out.payload == {"x": 1}
    assert not e.has_pending()


def test_take_max_priority_first():
    e = ProactiveEngine(rate_capacity=10, rate_refill_per_sec=10, cooldown_sec=0.0)
    e.offer(ProactiveTrigger(kind="low", priority=1))
    e.offer(ProactiveTrigger(kind="high", priority=99))
    e.offer(ProactiveTrigger(kind="mid", priority=50))
    assert e.take().kind == "high"
    assert e.take().kind == "mid"
    assert e.take().kind == "low"


def test_cooldown_blocks_same_kind():
    e = ProactiveEngine(rate_capacity=10, rate_refill_per_sec=10, cooldown_sec=999.0)
    assert e.offer(ProactiveTrigger(kind="dup", priority=5))
    e.take()  # take 标记 cooldown
    # 同 kind 立即 offer 必拒
    assert not e.offer(ProactiveTrigger(kind="dup", priority=5))
    # 不同 kind 仍接
    assert e.offer(ProactiveTrigger(kind="other", priority=5))


def test_rate_limit_blocks_burst():
    # capacity=2 · refill 0 · 第三次必拒
    e = ProactiveEngine(rate_capacity=2, rate_refill_per_sec=0, cooldown_sec=0.0)
    assert e.offer(ProactiveTrigger(kind="a", priority=1))
    assert e.offer(ProactiveTrigger(kind="b", priority=1))
    assert not e.offer(ProactiveTrigger(kind="c", priority=1))


def test_take_empty_returns_none():
    e = ProactiveEngine()
    assert e.take() is None
    assert not e.has_pending()


def test_reset_cooldown_allows_reoffer():
    e = ProactiveEngine(rate_capacity=10, rate_refill_per_sec=10, cooldown_sec=999.0)
    e.offer(ProactiveTrigger(kind="x", priority=1))
    e.take()
    assert not e.offer(ProactiveTrigger(kind="x", priority=1))
    e.reset_cooldown("x")
    assert e.offer(ProactiveTrigger(kind="x", priority=1))


def test_token_bucket_refill():
    tb = TokenBucket(capacity=2, refill_per_sec=100)
    assert tb.try_take(1)
    assert tb.try_take(1)
    assert not tb.try_take(1)
    time.sleep(0.05)  # ~5 tokens 应已 refill (capped to 2)
    assert tb.try_take(1)


def test_pending_count():
    e = ProactiveEngine(rate_capacity=10, rate_refill_per_sec=10, cooldown_sec=0.0)
    assert e.pending_count() == 0
    e.offer(ProactiveTrigger(kind="a", priority=1))
    e.offer(ProactiveTrigger(kind="b", priority=2))
    assert e.pending_count() == 2
    e.take()
    assert e.pending_count() == 1
