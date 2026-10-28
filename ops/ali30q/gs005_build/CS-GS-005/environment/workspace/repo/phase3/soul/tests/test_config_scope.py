"""Tests for soul.config scope constants (L2 platform-scope).

TDD: write these first (RED), then append the constants to config.py (GREEN).
"""

from soul import config


class TestSelfImproveScope:
    def test_scope_is_nonempty_tuple(self):
        assert isinstance(config.SELF_IMPROVE_SCOPE, tuple)
        assert len(config.SELF_IMPROVE_SCOPE) > 0

    def test_scope_contains_soul_glob(self):
        assert "phase3/soul/*.py" in config.SELF_IMPROVE_SCOPE

    def test_scope_includes_engine_glob(self):
        assert any("engine" in g for g in config.SELF_IMPROVE_SCOPE)

    def test_scope_includes_soul_service_glob(self):
        assert any("soul_*" in g for g in config.SELF_IMPROVE_SCOPE)

    def test_scope_excludes_broad_services_glob(self):
        # never widen to ALL backend services — anchor #7 safety
        assert "phase3/backend/services/*.py" not in config.SELF_IMPROVE_SCOPE


class TestSelfImproveExclude:
    def test_exclude_contains_all_blacklist(self):
        for item in config.PATH_BLACKLIST:
            assert item in config.SELF_IMPROVE_EXCLUDE

    def test_exclude_contains_agent_cognitive_markers(self):
        for marker in ("agent_brain", "bicameral_mind", "autonomous_loop"):
            assert marker in config.SELF_IMPROVE_EXCLUDE


class TestPlatformLocCap:
    def test_platform_cap_is_stricter(self):
        assert config.PLATFORM_MAX_PR_DIFF_LOC < config.MAX_PR_DIFF_LOC
