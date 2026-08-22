import json
import sqlite3
from itertools import permutations

import pytest

from gep.flywheel_event import (
    canonical_event_bytes,
    event_from_mapping,
    hash_payload,
    hash_payload_for_kind,
)
from gep.flywheel_log import (
    AppendReceipt,
    EpisodeState,
    FlywheelEventLog,
    reduce_episode_states,
)


SECRET = "s4secret-x9"


def episode_mapping(**overrides):
    payload = overrides.pop(
        "payload",
        {
            "episode_id": overrides.get("episode_id", "episode-1"),
            "task": "verify a fix",
        },
    )
    payload_hash = overrides.pop("payload_hash", hash_payload(payload))
    event = {
        "schema_version": "compass.flywheel.event.v1",
        "event_kind": "episode",
        "source_event_id": "episode-source-1",
        "episode_id": "episode-1",
        "parent_event_id": None,
        "agent_id": 7,
        "occurred_at": "2026-08-01T01:00:00Z",
        "payload_schema": "compass.experience_packet.v0",
        "payload": payload,
        "payload_hash": payload_hash,
    }
    event.update(overrides)
    return event


def verdict_mapping(episode_event_hash, **overrides):
    episode_id = overrides.get("episode_id", "episode-1")
    payload_overrides = overrides.pop("payload_overrides", {})
    payload = overrides.pop(
        "payload",
        {
            "episode_id": episode_id,
            "episode_event_hash": episode_event_hash,
            "outcome": "success",
            "verifier_kind": "software_test",
            "verifier_version": "pytest-8.4",
            "verifier_policy_hash": "sha256:" + "2" * 64,
            "evidence_hash": "sha256:" + "3" * 64,
            "environment_fingerprint_hash": "sha256:" + "4" * 64,
            "failure_class": None,
        },
    )
    payload.update(payload_overrides)
    payload_hash = overrides.pop(
        "payload_hash",
        hash_payload_for_kind("verdict", payload),
    )
    event = {
        "schema_version": "compass.flywheel.event.v1",
        "event_kind": "verdict",
        "source_event_id": "verdict-source-1",
        "episode_id": episode_id,
        "parent_event_id": "episode-source-1",
        "agent_id": 8,
        "occurred_at": "2026-08-01T01:01:00Z",
        "payload_schema": "compass.verdict_packet.v0",
        "payload": payload,
        "payload_hash": payload_hash,
    }
    event.update(overrides)
    return event


def admit_episode(event_log, **overrides):
    raw = episode_mapping(**overrides)
    event = event_from_mapping(raw)
    assert event_log.append(raw).status == "accepted"
    return raw, event


def admit_verdict(event_log, episode, **overrides):
    raw = verdict_mapping(episode.event_hash, **overrides)
    event = event_from_mapping(raw)
    assert event_log.append(raw).status == "accepted"
    return raw, event


def assert_secret_is_absent(path, event_log):
    encoded_secret = SECRET.encode("utf-8")
    for database_artifact in path.parent.glob(f"{path.name}*"):
        assert encoded_secret not in database_artifact.read_bytes()

    accepted_rows = tuple(
        canonical_event_bytes(event) for event in event_log.list_events()
    )
    assert all(encoded_secret not in row for row in accepted_rows)
    quarantine_projection = json.dumps(
        event_log.list_quarantine(),
        sort_keys=True,
    )
    assert SECRET not in quarantine_projection


def assert_admission_rejection(
    event_log,
    path,
    raw,
    *,
    status,
    reason_code,
):
    event = event_from_mapping(raw)
    before = event_log.list_events()

    receipt = event_log.append(raw)

    assert receipt == AppendReceipt(
        status=status,
        source_event_id=event.source_event_id,
        episode_id=event.episode_id,
        event_hash=event.event_hash,
        reason_code=reason_code,
    )
    assert event_log.list_events() == before
    assert event_log.list_quarantine()[-1]["reason_code"] == reason_code
    assert_secret_is_absent(path, event_log)
    return receipt


class VerdictInsertRaceConnection:
    def __init__(self, connection, competing_event):
        self._connection = connection
        self._competing_event = competing_event
        self._injected = False

    def execute(self, statement, parameters=()):
        compact_statement = " ".join(statement.split())
        if (
            not self._injected
            and compact_statement.startswith("INSERT INTO flywheel_events")
            and len(parameters) == 8
            and parameters[1] == "verdict"
        ):
            event = self._competing_event
            self._connection.execute(
                """
                INSERT INTO flywheel_events
                    (source_event_id, event_kind, episode_id, parent_event_id,
                     agent_id, event_hash, envelope_json, accepted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.source_event_id,
                    event.event_kind,
                    event.episode_id,
                    event.parent_event_id,
                    event.agent_id,
                    event.event_hash,
                    sqlite3.Binary(canonical_event_bytes(event)),
                    "2026-08-01T01:02:00.000000Z",
                ),
            )
            self._injected = True
        return self._connection.execute(statement, parameters)

    def __getattr__(self, name):
        return getattr(self._connection, name)


def test_independent_verdict_is_durable_and_duplicate_after_reopen(tmp_path):
    path = tmp_path / "verdict-flow.sqlite3"
    episode_raw = episode_mapping()
    episode = event_from_mapping(episode_raw)
    verdict_raw = verdict_mapping(episode.event_hash)
    verdict = event_from_mapping(verdict_raw)

    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        assert event_log.append(episode_raw) == AppendReceipt(
            status="accepted",
            source_event_id=episode.source_event_id,
            episode_id=episode.episode_id,
            event_hash=episode.event_hash,
            reason_code=None,
        )
        assert event_log.append(verdict_raw) == AppendReceipt(
            status="accepted",
            source_event_id=verdict.source_event_id,
            episode_id=verdict.episode_id,
            event_hash=verdict.event_hash,
            reason_code=None,
        )
        assert event_log.count_events() == 2
        assert event_log.get(episode.source_event_id) == episode
        assert event_log.get(verdict.source_event_id) == verdict
        assert event_log.list_events() == (episode, verdict)
        assert event_log.list_quarantine() == ()
    finally:
        event_log.close()

    reopened = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        assert reopened.list_events() == (episode, verdict)
        assert reopened.append(verdict_raw) == AppendReceipt(
            status="duplicate",
            source_event_id=verdict.source_event_id,
            episode_id=verdict.episode_id,
            event_hash=verdict.event_hash,
            reason_code=None,
        )
        assert reopened.count_events() == 2
        assert reopened.list_events() == (episode, verdict)
        assert reopened.list_quarantine() == ()
    finally:
        reopened.close()


def test_unregistered_verifier_precedes_parent_checks_and_is_quarantined(tmp_path):
    path = tmp_path / "unregistered-verifier.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids=(),
    )
    try:
        raw = verdict_mapping(
            "sha256:" + "0" * 64,
            parent_event_id="missing-parent",
            payload_overrides={"failure_class": SECRET},
        )

        assert_admission_rejection(
            event_log,
            path,
            raw,
            status="quarantined",
            reason_code="unregistered_verifier",
        )
    finally:
        event_log.close()


def test_orphan_parent_precedes_lineage_hash_and_self_checks(tmp_path):
    path = tmp_path / "orphan-parent.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7},
        registered_verifier_ids={7},
    )
    try:
        raw = verdict_mapping(
            "sha256:" + "0" * 64,
            parent_event_id="missing-parent",
            agent_id=7,
            payload_overrides={"failure_class": SECRET},
        )

        assert_admission_rejection(
            event_log,
            path,
            raw,
            status="conflict",
            reason_code="orphan_parent",
        )
    finally:
        event_log.close()


def test_invalid_parent_kind_precedes_parent_episode_and_hash_checks(tmp_path):
    path = tmp_path / "invalid-parent-kind.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8, 9},
        registered_verifier_ids={8, 9},
    )
    try:
        _, episode = admit_episode(event_log)
        _, parent_verdict = admit_verdict(event_log, episode)
        raw = verdict_mapping(
            "sha256:" + "0" * 64,
            source_event_id="verdict-source-2",
            parent_event_id=parent_verdict.source_event_id,
            episode_id="episode-2",
            agent_id=9,
            payload_overrides={"failure_class": SECRET},
        )

        assert_admission_rejection(
            event_log,
            path,
            raw,
            status="conflict",
            reason_code="invalid_parent_kind",
        )
    finally:
        event_log.close()


def test_parent_episode_mismatch_precedes_hash_and_self_checks(tmp_path):
    path = tmp_path / "parent-episode-mismatch.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7},
        registered_verifier_ids={7},
    )
    try:
        _, episode = admit_episode(event_log)
        raw = verdict_mapping(
            "sha256:" + "0" * 64,
            source_event_id="verdict-source-2",
            episode_id="episode-2",
            agent_id=7,
            payload_overrides={"failure_class": SECRET},
        )

        assert_admission_rejection(
            event_log,
            path,
            raw,
            status="conflict",
            reason_code="parent_episode_mismatch",
        )
        assert event_log.get(episode.source_event_id) == episode
    finally:
        event_log.close()


def test_episode_event_hash_mismatch_precedes_self_verdict(tmp_path):
    path = tmp_path / "episode-event-hash-mismatch.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7},
        registered_verifier_ids={7},
    )
    try:
        admit_episode(event_log)
        raw = verdict_mapping(
            "sha256:" + "0" * 64,
            agent_id=7,
            payload_overrides={"failure_class": SECRET},
        )

        assert_admission_rejection(
            event_log,
            path,
            raw,
            status="conflict",
            reason_code="episode_event_hash_mismatch",
        )
    finally:
        event_log.close()


def test_self_verdict_is_rejected_after_valid_parent_hash(tmp_path):
    path = tmp_path / "self-verdict.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7},
        registered_verifier_ids={7},
    )
    try:
        _, episode = admit_episode(event_log)
        raw = verdict_mapping(
            episode.event_hash,
            agent_id=7,
            payload_overrides={"failure_class": SECRET},
        )

        assert_admission_rejection(
            event_log,
            path,
            raw,
            status="conflict",
            reason_code="self_verdict",
        )
    finally:
        event_log.close()


def test_one_verdict_per_verifier_and_episode_is_enforced_explicitly(tmp_path):
    path = tmp_path / "verifier-episode-conflict.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        _, episode = admit_episode(event_log)
        admit_verdict(event_log, episode)
        raw = verdict_mapping(
            episode.event_hash,
            source_event_id="verdict-source-2",
            occurred_at="2026-08-01T01:02:00Z",
            payload_overrides={
                "outcome": "failure",
                "evidence_hash": "sha256:" + "5" * 64,
                "failure_class": SECRET,
            },
        )

        assert_admission_rejection(
            event_log,
            path,
            raw,
            status="conflict",
            reason_code="verifier_episode_conflict",
        )
    finally:
        event_log.close()


@pytest.mark.parametrize("unknown_location", ["envelope", "payload"])
def test_unknown_verdict_keys_never_persist_raw_input(tmp_path, unknown_location):
    path = tmp_path / f"unknown-{unknown_location}-key.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        _, episode = admit_episode(event_log)
        raw = verdict_mapping(episode.event_hash)
        if unknown_location == "envelope":
            raw["raw_evidence"] = SECRET
        else:
            raw["payload"]["raw_evidence"] = SECRET

        receipt = event_log.append(raw)

        assert receipt == AppendReceipt(
            status="quarantined",
            source_event_id="verdict-source-1",
            episode_id="episode-1",
            event_hash=None,
            reason_code="invalid_schema",
        )
        assert event_log.list_events() == (episode,)
        assert event_log.get("verdict-source-1") is None
        assert event_log.list_quarantine()[-1]["reason_code"] == "invalid_schema"
        assert_secret_is_absent(path, event_log)
    finally:
        event_log.close()


def test_altered_evidence_without_payload_rehash_is_quarantined(tmp_path):
    path = tmp_path / "altered-evidence-hash.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        _, episode = admit_episode(event_log)
        raw = verdict_mapping(
            episode.event_hash,
            payload_overrides={"verifier_version": SECRET},
        )
        raw["payload"]["evidence_hash"] = "sha256:" + "5" * 64

        receipt = event_log.append(raw)

        assert receipt == AppendReceipt(
            status="quarantined",
            source_event_id="verdict-source-1",
            episode_id="episode-1",
            event_hash=None,
            reason_code="payload_hash_mismatch",
        )
        assert event_log.list_events() == (episode,)
        assert event_log.get("verdict-source-1") is None
        assert event_log.list_quarantine()[-1]["reason_code"] == (
            "payload_hash_mismatch"
        )
        assert_secret_is_absent(path, event_log)
    finally:
        event_log.close()


def test_same_source_with_changed_evidence_and_rehash_conflicts(tmp_path):
    path = tmp_path / "same-source-changed-evidence.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        _, episode = admit_episode(event_log)
        _, original_verdict = admit_verdict(event_log, episode)
        changed = verdict_mapping(
            episode.event_hash,
            payload_overrides={
                "evidence_hash": "sha256:" + "5" * 64,
                "failure_class": SECRET,
            },
        )

        assert_admission_rejection(
            event_log,
            path,
            changed,
            status="conflict",
            reason_code="source_event_conflict",
        )
        assert event_log.get(original_verdict.source_event_id) == original_verdict
    finally:
        event_log.close()


def test_rejected_verdict_deduplicates_quarantine_after_restart(tmp_path):
    path = tmp_path / "rejected-restart.sqlite3"
    raw = verdict_mapping(
        "sha256:" + "0" * 64,
        parent_event_id="missing-parent",
        payload_overrides={"failure_class": SECRET},
    )
    event = event_from_mapping(raw)
    expected = AppendReceipt(
        status="conflict",
        source_event_id=event.source_event_id,
        episode_id=event.episode_id,
        event_hash=event.event_hash,
        reason_code="orphan_parent",
    )

    first_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        assert first_log.append(raw) == expected
        assert len(first_log.list_quarantine()) == 1
        assert_secret_is_absent(path, first_log)
    finally:
        first_log.close()

    reopened = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        assert reopened.count_events() == 0
        assert len(reopened.list_quarantine()) == 1
        assert reopened.append(raw) == expected
        assert len(reopened.list_quarantine()) == 1
        assert_secret_is_absent(path, reopened)
    finally:
        reopened.close()


def test_partial_unique_index_race_returns_verifier_episode_conflict(tmp_path):
    path = tmp_path / "verdict-index-race.sqlite3"
    event_log = FlywheelEventLog(
        path,
        registered_agent_ids={7, 8},
        registered_verifier_ids={8},
    )
    try:
        _, episode = admit_episode(event_log)
        candidate_raw = verdict_mapping(
            episode.event_hash,
            payload_overrides={"failure_class": SECRET},
        )
        candidate = event_from_mapping(candidate_raw)
        competing = event_from_mapping(
            verdict_mapping(
                episode.event_hash,
                source_event_id="verdict-race-winner",
                occurred_at="2026-08-01T01:01:30Z",
                payload_overrides={
                    "outcome": "failure",
                    "evidence_hash": "sha256:" + "5" * 64,
                },
            )
        )
        event_log._connection = VerdictInsertRaceConnection(
            event_log._connection,
            competing,
        )

        receipt = event_log.append(candidate_raw)

        assert receipt == AppendReceipt(
            status="conflict",
            source_event_id=candidate.source_event_id,
            episode_id=candidate.episode_id,
            event_hash=candidate.event_hash,
            reason_code="verifier_episode_conflict",
        )
        assert event_log.list_events() == (episode, competing)
        assert event_log.get(candidate.source_event_id) is None
        assert event_log.list_quarantine()[-1]["reason_code"] == (
            "verifier_episode_conflict"
        )
        assert_secret_is_absent(path, event_log)
    finally:
        event_log.close()


def reducer_verdict(episode, outcome, position):
    hash_digit = format(position + 5, "x")
    return event_from_mapping(
        verdict_mapping(
            episode.event_hash,
            source_event_id=f"verdict-source-{position}",
            agent_id=7 + position,
            occurred_at=f"2026-08-01T01:01:{position:02d}Z",
            payload_overrides={
                "outcome": outcome,
                "evidence_hash": "sha256:" + hash_digit * 64,
            },
        )
    )


@pytest.mark.parametrize(
    ("outcomes", "expected_state", "expected_outcome"),
    [
        pytest.param((), "awaiting_verdict", None, id="episode-only"),
        pytest.param(
            ("inconclusive", "inconclusive"),
            "awaiting_verdict",
            None,
            id="only-inconclusive",
        ),
        pytest.param(("success",), "verified", "success", id="one-success"),
        pytest.param(("failure",), "verified", "failure", id="one-failure"),
        pytest.param(("partial",), "verified", "partial", id="one-partial"),
        pytest.param(
            ("success", "success"),
            "verified",
            "success",
            id="independent-successes",
        ),
        pytest.param(
            ("success", "inconclusive"),
            "verified",
            "success",
            id="success-and-inconclusive",
        ),
        pytest.param(
            ("success", "failure"),
            "verdict_conflict",
            None,
            id="success-and-failure",
        ),
    ],
)
def test_reducer_derives_verdict_backed_episode_state(
    outcomes,
    expected_state,
    expected_outcome,
):
    episode = event_from_mapping(episode_mapping())
    verdicts = tuple(
        reducer_verdict(episode, outcome, position)
        for position, outcome in enumerate(outcomes, start=1)
    )

    state = reduce_episode_states((episode, *verdicts))[episode.episode_id]

    assert state == EpisodeState(
        episode_id=episode.episode_id,
        state=expected_state,
        source_event_id=episode.source_event_id,
        event_hash=episode.event_hash,
        verified_outcome=expected_outcome,
        verdict_event_hashes=tuple(sorted(verdict.event_hash for verdict in verdicts)),
    )


def test_reducer_is_order_independent_for_every_event_permutation():
    episode = event_from_mapping(episode_mapping())
    verdicts = (
        reducer_verdict(episode, "success", 1),
        reducer_verdict(episode, "failure", 2),
        reducer_verdict(episode, "inconclusive", 3),
    )
    events = (episode, *verdicts)
    expected = EpisodeState(
        episode_id=episode.episode_id,
        state="verdict_conflict",
        source_event_id=episode.source_event_id,
        event_hash=episode.event_hash,
        verified_outcome=None,
        verdict_event_hashes=tuple(sorted(verdict.event_hash for verdict in verdicts)),
    )

    results = tuple(reduce_episode_states(order) for order in permutations(events))

    assert all(result == {episode.episode_id: expected} for result in results)


def test_reducer_materializes_a_single_pass_iterable_once():
    episode = event_from_mapping(episode_mapping())
    verdict = reducer_verdict(episode, "success", 1)

    class SinglePassEvents:
        def __init__(self):
            self.iterations = 0

        def __iter__(self):
            self.iterations += 1
            if self.iterations > 1:
                raise AssertionError("events were iterated more than once")
            yield verdict
            yield episode

    events = SinglePassEvents()

    state = reduce_episode_states(events)[episode.episode_id]

    assert events.iterations == 1
    assert state.state == "verified"
    assert state.verified_outcome == "success"


def test_reducer_rejects_orphan_verdict():
    episode = event_from_mapping(episode_mapping())
    orphan = event_from_mapping(
        verdict_mapping(
            episode.event_hash,
            parent_event_id="missing-episode-source",
        )
    )

    with pytest.raises(ValueError, match="orphan verdict"):
        reduce_episode_states((episode, orphan))


def test_reducer_rejects_verdict_whose_parent_is_not_an_episode():
    episode = event_from_mapping(episode_mapping())
    first_verdict = reducer_verdict(episode, "success", 1)
    wrong_kind_parent = event_from_mapping(
        verdict_mapping(
            episode.event_hash,
            source_event_id="verdict-source-2",
            parent_event_id=first_verdict.source_event_id,
            agent_id=9,
            occurred_at="2026-08-01T01:01:02Z",
            payload_overrides={"evidence_hash": "sha256:" + "7" * 64},
        )
    )

    with pytest.raises(ValueError, match="parent is not an episode"):
        reduce_episode_states((episode, first_verdict, wrong_kind_parent))


def test_reducer_rejects_verdict_for_wrong_episode_id():
    episode = event_from_mapping(episode_mapping())
    wrong_episode = event_from_mapping(
        verdict_mapping(
            episode.event_hash,
            episode_id="episode-2",
        )
    )

    with pytest.raises(ValueError, match="episode_id does not match parent"):
        reduce_episode_states((episode, wrong_episode))


def test_reducer_rejects_verdict_with_wrong_episode_event_hash():
    episode = event_from_mapping(episode_mapping())
    wrong_hash = event_from_mapping(
        verdict_mapping("sha256:" + "0" * 64)
    )

    with pytest.raises(ValueError, match="episode_event_hash does not match parent"):
        reduce_episode_states((episode, wrong_hash))
