from soul import goal_selector


def test_loads_pending_external_first(tmp_path, monkeypatch):
    g = tmp_path / "goals.yaml"
    g.write_text(
        "goals:\n"
        "  - id: low\n    priority: 10\n    category: internal\n    description: x\n    status: pending\n"
        "  - id: high\n    priority: 100\n    category: external\n    description: y\n    status: pending\n"
        "  - id: done1\n    priority: 200\n    category: external\n    description: z\n    status: done\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(goal_selector, "GOALS_FILE", g)
    goal = goal_selector.next_yaml_goal()
    assert goal is not None
    assert goal["id"] == "high"  # highest priority among pending


def test_returns_none_when_all_done(tmp_path, monkeypatch):
    g = tmp_path / "goals.yaml"
    g.write_text("goals:\n  - id: a\n    priority: 5\n    category: external\n    description: x\n    status: done\n", encoding="utf-8")
    monkeypatch.setattr(goal_selector, "GOALS_FILE", g)
    assert goal_selector.next_yaml_goal() is None


def test_docs_scrape_finds_marker(tmp_path, monkeypatch):
    d = tmp_path / "README.md"
    d.write_text("line1\n<!-- TODO: wire up the foo endpoint -->\nline3\n", encoding="utf-8")
    monkeypatch.setattr(goal_selector, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(goal_selector, "DOCS_SCRAPE_GLOBS", ("README.md",))
    goal = goal_selector.next_docs_goal()
    assert goal is not None
    assert "foo endpoint" in goal["description"]


def test_select_prefers_yaml_over_fallback(tmp_path, monkeypatch):
    g = tmp_path / "goals.yaml"
    g.write_text("goals:\n  - id: y1\n    priority: 50\n    category: external\n    description: yaml-task\n    status: pending\n", encoding="utf-8")
    monkeypatch.setattr(goal_selector, "GOALS_FILE", g)
    chosen = goal_selector.select_goal(reflection_done_today=0)
    assert chosen["source"] == "yaml"
    assert chosen["id"] == "y1"


def test_mark_done_sets_status_and_is_idempotent(tmp_path, monkeypatch):
    import yaml
    g = tmp_path / "goals.yaml"
    g.write_text(
        "# top comment must survive\n"
        "goals:\n"
        "  - id: a\n    priority: 5\n    category: external\n    description: x\n    status: pending\n"
        "  - id: b\n    priority: 3\n    category: internal\n    description: y\n    status: pending\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(goal_selector, "GOALS_FILE", g)
    assert goal_selector.mark_done("a") is True
    raw = g.read_text(encoding="utf-8")
    assert "# top comment must survive" in raw  # surgical edit preserves comments
    data = yaml.safe_load(raw)
    by_id = {x["id"]: x for x in data["goals"]}
    assert by_id["a"]["status"] == "done"
    assert by_id["b"]["status"] == "pending"  # untouched
    # idempotent: already done → no change
    assert goal_selector.mark_done("a") is False
    # unknown id → no change
    assert goal_selector.mark_done("zzz") is False
