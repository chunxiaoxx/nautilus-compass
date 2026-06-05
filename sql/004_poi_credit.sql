-- 004 · PoI central credit table (Option C · MVP single-table)
-- Apply on cloud (nautilus_production) AFTER 003.
-- Reference: docs/plans/2026-06-03-poi-central-ledger-design.md §4.1
--
-- Phase 1: credit source of truth migrates from memory-file frontmatter to this
-- table. memory_key (the memory filename) is the cross-agent join key, so file
-- location no longer pins credit to one host.

CREATE TABLE IF NOT EXISTS compass.poi_credit (
    memory_key        text             PRIMARY KEY,
    cumulative_impact double precision NOT NULL DEFAULT 0,
    event_count       int              NOT NULL DEFAULT 0,
    last_impact_at    timestamptz
);

-- Phase 1: reuse the existing writable account. Phase 2 introduces a dedicated
-- poi_writer role and tightens this grant. TODO(Phase 2): move write to poi_writer.
-- compass_sub needs USAGE on the schema to reference objects in it · table-level
-- grants alone are insufficient (compass_sub did not previously touch compass.*).
GRANT USAGE ON SCHEMA compass TO compass_sub;
GRANT SELECT, INSERT, UPDATE ON compass.poi_credit TO compass_sub;
