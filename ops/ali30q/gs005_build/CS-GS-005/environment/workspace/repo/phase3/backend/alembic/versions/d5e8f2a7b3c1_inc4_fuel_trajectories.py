"""inc4 fuel_trajectories table(轨迹→燃料采集器·涡轮增压第一环)

Revision ID: d5e8f2a7b3c1
Revises: f3a9b1c8d2e4
Create Date: 2026-10-04

v5 FUEL_ORDER_SPEC_V1 §二 交付物落库表。判据主权在 v5 四验门:平台只做 schema
级校验+存档,gates/status 由 v5 侧回填(received→gated→in_pool)。
Safe to apply multiple times (IF NOT EXISTS guards).
Cloud may apply via raw SQL bypass per inc2 先例(c1b8d4f7e2a3)。
"""
from alembic import op


revision = 'd5e8f2a7b3c1'
down_revision = 'f3a9b1c8d2e4'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fuel_trajectories (
            traj_id       VARCHAR PRIMARY KEY,
            bounty_id     VARCHAR,
            submitter     VARCHAR NOT NULL,
            qid           VARCHAR NOT NULL,
            context       TEXT NOT NULL,
            trajectory    JSONB NOT NULL,
            verdict       VARCHAR NOT NULL,
            label_origin  VARCHAR NOT NULL,
            failure_tag   VARCHAR,
            gates         JSONB,
            status        VARCHAR NOT NULL DEFAULT 'received',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fuel_traj_status ON fuel_trajectories (status)"
    )


def downgrade():
    op.execute("DROP TABLE IF EXISTS fuel_trajectories")
