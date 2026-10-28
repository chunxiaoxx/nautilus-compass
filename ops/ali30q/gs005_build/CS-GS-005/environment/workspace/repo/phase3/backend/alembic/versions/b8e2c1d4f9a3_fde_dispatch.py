"""fde_dispatch · FDE 生产线派单表 (DMAS #3 · clean track)

Revision ID: b8e2c1d4f9a3
Revises: a7f3c1d2e4b5
Create Date: 2026-06-06

The platform FDE production-line dispatch table — open→claimed→produced→settled.
Deliberately separate from academic_tasks / platform_bounties (deprecated internal
NAU bounty market). Reward = external FDE verdict (fde_verdicts), not internal NAU.
"""
from alembic import op
import sqlalchemy as sa


revision = "b8e2c1d4f9a3"
down_revision = "a7f3c1d2e4b5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fde_dispatch",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_uid", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("claimed_by", sa.String(length=120), nullable=True),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("reported_at", sa.DateTime(), nullable=True),
        sa.Column("output", sa.JSON(), nullable=True),  # produced answer → soul scorer (produce→verdict spine)
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_fde_dispatch_task_uid", "fde_dispatch", ["task_uid"], unique=True)
    op.create_index("ix_fde_dispatch_status", "fde_dispatch", ["status"])
    op.create_index("idx_fde_dispatch_status_created", "fde_dispatch", ["status", "created_at"])


def downgrade():
    op.drop_index("idx_fde_dispatch_status_created", table_name="fde_dispatch")
    op.drop_index("ix_fde_dispatch_status", table_name="fde_dispatch")
    op.drop_index("ix_fde_dispatch_task_uid", table_name="fde_dispatch")
    op.drop_table("fde_dispatch")
