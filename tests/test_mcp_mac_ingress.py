"""Mac transport regressions; all tool implementations are spies, never production IO."""
import json
import pytest
import mcp_access as a

@pytest.mark.parametrize('value', ['garbage', {'scopes': 'read:*'}, ['unknown'], []])
def test_unknown_scope_formats_fail_closed(value):
    assert not a.parse_scopes(value)

def test_project_and_global_boundaries(tmp_path):
    scopes = frozenset({'read:A'})
    assert a.authorize(scopes, 'recall', {'project': 'A'}, lambda: 'A', tmp_path)['project'] == 'A'
    for name, args in [('recall', {'project': 'B'}), ('recall', {'project': 'A', 'scope': 'user'}),
                       ('ingest_obs', {'project': 'A'}), ('profile', {'project': 'A'}),
                       ('session_search', {'project': 'A'}), ('add_worker', {}), ('unknown', {})]:
        with pytest.raises(PermissionError):
            a.authorize(scopes, name, args, lambda: 'A', tmp_path)

@pytest.mark.parametrize('project', ['../B', '/absolute', 'A/B', 'A\\B', '..'])
def test_traversal_denied_even_for_admin(tmp_path, project):
    with pytest.raises(ValueError):
        a.authorize(frozenset({'*'}), 'recall', {'project': project}, lambda: 'A', tmp_path)

def test_symlink_escape_denied(tmp_path):
    (tmp_path / 'escape').symlink_to(tmp_path.parent, target_is_directory=True)
    with pytest.raises(PermissionError):
        a.authorize(frozenset({'*'}), 'recall', {'project': 'escape'}, lambda: 'A', tmp_path)

def test_windows_grant_normalizes_only_known_alias(tmp_path):
    scopes = frozenset({'read:C--Users-chunx-Projects-nautilus-core'})
    args = a.authorize(scopes, 'recall', {}, lambda: 'wrong-default', tmp_path)
    assert args['project'] == '-Users-chunxiao-wang-Projects-nautilus-core'
    with pytest.raises(PermissionError):
        a.authorize(scopes, 'recall', {'project': '-Users-chunxiao-wang-Projects-nautilus-v5'}, lambda: 'A', tmp_path)

def test_existing_operator_and_owner_compatibility(tmp_path):
    operator = frozenset({'tools.read', 'tools.write', 'read:*', 'write:C--Users-chunx'})
    assert a.authorize(operator, 'profile', {}, lambda: 'A', tmp_path) == {}
    assert a.authorize(operator, 'add_worker', {}, lambda: 'A', tmp_path) == {}
    assert a.authorize(operator, 'ingest_obs', {}, lambda: 'A', tmp_path)['project'] == '-Users-chunxiao-wang'
    assert a.visible(frozenset({'*'}), 'governance_dispatch')
    assert not a.visible(frozenset({'tools.read', 'read:*'}), 'governance_dispatch')

def test_http_scopes_reach_dispatch_and_reload(tmp_path, monkeypatch):
    from starlette.testclient import TestClient
    import mcp_http_local as m
    tokens = tmp_path / 'tokens.json'
    tokens.write_text(json.dumps({'reader': {'scopes': ['read:A']}, 'owner': {'scopes': ['*']}}))
    monkeypatch.setenv('COMPASS_TOKENS_FILE', str(tokens))
    calls = []
    def spy(args):
        calls.append(dict(args))
        return {'ok': True, 'project': args.get('project')}
    monkeypatch.setattr(m.cmp, 'TOOLS', {name: {'fn': spy, 'schema': {
        'name': name, 'description': 'isolated spy', 'inputSchema': {'type': 'object'}}}
        for name in ['recall', 'ingest_obs', 'profile', 'add_worker']})
    monkeypatch.setattr(m.cmp, 'PROJECTS_DIR', tmp_path)
    monkeypatch.setattr(m.cmp, 'resolve_project', lambda _: 'A')
    def call(client, token, method, params=None):
        return client.post('/mcp/', headers={'Authorization': 'Bearer ' + token,
            'Accept': 'application/json, text/event-stream'}, json={
            'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})
    with TestClient(m.app) as client:
        assert call(client, 'invalid', 'tools/list').status_code == 401
        listed = call(client, 'reader', 'tools/list').json()['result']['tools']
        assert [t['name'] for t in listed] == ['recall']
        for name, args in [('ingest_obs', {'project': 'A'}), ('recall', {'project': 'B'}),
                           ('profile', {'project': 'A'}), ('add_worker', {})]:
            response = call(client, 'reader', 'tools/call', {'name': name, 'arguments': args})
            assert 'forbidden' in response.text
            assert not calls
        good = call(client, 'reader', 'tools/call', {'name': 'recall', 'arguments': {'project': 'A'}})
        assert good.status_code == 200 and calls == [{'project': 'A'}]
        # A preceding owner request must not leak authority to the next reader.
        assert len(call(client, 'owner', 'tools/list').json()['result']['tools']) == 4
        assert len(call(client, 'reader', 'tools/list').json()['result']['tools']) == 1
        tokens.write_text('{}')
        assert call(client, 'reader', 'tools/list').status_code == 401
