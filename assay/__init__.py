# -*- coding: utf-8 -*-
"""nautilus_compass.assay — 判分机构产品面(schema 校验器+提交接口)。

正本迁移自 tools/verdict_schema_v2.py(3.3.0 起,tools CLI 为薄壳)。
设计正本:docs/protocol/VERDICT_SCHEMA_V2.md + docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md。
"""
from nautilus_compass.assay.schema_v2 import STATES, TIERS, migrate, parse_state, validate
from nautilus_compass.assay.submit import (
    CAUSE_TAGS,
    ERRATA_REQUIRED,
    CHALLENGE_REQUIRED,
    validate_errata,
    validate_challenge,
)

__all__ = [
    "TIERS", "STATES", "parse_state", "migrate", "validate",
    "CAUSE_TAGS", "CHALLENGE_REQUIRED", "ERRATA_REQUIRED",
    "validate_challenge", "validate_errata",
]
