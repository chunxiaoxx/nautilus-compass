"""fde_attention queue table for human-in-loop handoff.

Revision ID: f3a9b1c8d2e4
Revises: c4f8a1b6d3e9
Create Date: 2026-07-24

This migration creates the shared attention queue used by S1/S2/S3 failure hooks.
It is paired with model import side effects from models.fde_attention and allows
deployment environments that do not run Base.metadata.create_all() (e.g. strict
migrations-only workflows).
"""
from alembic import op
import sqlalchemy as sa


revision = "f3a9b1c8d2e4"
down_revision = "c4f8a1b6d3e9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fde_attention",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_uid", sa.String(length=120), nullable=True),
        sa.Column("stage", sa.String(length=12), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=12), nullable=False, server_default="warning"),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("suggested_actions", sa.JSON(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("resolution", sa.String(length=80), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_fde_attention_task_uid", "fde_attention", ["task_uid"])
    op.create_index("ix_fde_attention_stage", "fde_attention", ["stage"])
    op.create_index("ix_fde_attention_code", "fde_attention", ["code"])
    op.create_index("ix_fde_attention_status", "fde_attention", ["status"])
    op.create_index("ix_fde_attention_created_at", "fde_attention", ["created_at"])
    op.create_index(
        "idx_fde_attention_status_stage",
        "fde_attention",
        ["status", "stage", "created_at"],
    )


def downgrade():
    op.drop_index("idx_fde_attention_status_stage", table_name="fde_attention")
    op.drop_index("ix_fde_attention_created_at", table_name="fde_attention")
    op.drop_index("ix_fde_attention_status", table_name="fde_attention")
    op.drop_index("ix_fde_attention_code", table_name="fde_attention")
    op.drop_index("ix_fde_attention_stage", table_name="fde_attention")
    op.drop_index("ix_fde_attention_task_uid", table_name="fde_attention")
    op.drop_table("fde_attention")
