# Compass S4 Experience Packet v0 Design

## Goal

Introduce the smallest durable representation of one Agent Harness experience without
wiring it into storage, daemons, ingestion, PoI reranking, policy mutation, or capsule
generation.

## Strategic role

An Experience Packet is the SFT-like atomic sample in the Compass S4 post-training
flywheel. It records what task was attempted, what action and tools were used, what
happened, and which route or future policy hint may be relevant. Reward and impact
signals can be attached later. Repeated high-value packets may eventually be distilled
into memory capsules, but that distillation is deliberately outside this change.

## Schema

`ExperiencePacket` is a frozen dataclass. Every field defaults to `None` so producers can
adopt the schema incrementally and old call sites remain unaffected. `tool_chain` is held
as an immutable tuple inside the packet and serialized as a list for frontmatter.

Fields:

- Identity: `episode_id`, `parent_episode_id`
- Experience: `task`, `action_kind`, `tool_chain`, `outcome`, `failure_mode`
- Signals: `reward_delta`, `impact`
- Policy and distillation hints: `route_key`, `capsule_candidate`, `policy_hint`

## Helpers

- `from_args(args=None, **overrides)` reads only schema fields from an argparse namespace
  or mapping, ignores unrelated arguments, applies explicit overrides, and normalizes the
  tool chain.
- `to_frontmatter(packet)` returns a plain dictionary, omits fields that are `None`, keeps
  explicit false and zero values, and converts the tool-chain tuple to a list.

## Compatibility and non-goals

This module has no side effects and changes no existing interface. It does not alter the
database, daemon, governance plan, `ingest_obs`, capsule generation, PoI ordering, or model
weights. Those integrations require separate evidence and promotion gates.
