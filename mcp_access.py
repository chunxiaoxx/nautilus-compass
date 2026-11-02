"""Shared fail-closed policy for the Mac MCP ingress (no credential material)."""
from pathlib import Path

READ_TOOLS = {'recall', 'thread_recall', 'drift_check', 'session_search', 'profile',
              'drift_history', 'proof_of_impact', 'governance_audit', 'governance_lock_check'}
WRITE_TOOLS = {'ingest_obs', 'feedback_log', 'long_task', 'submit_platform_task',
               'ingest_platform_task_result', 'governance_dispatch', 'governance_plan', 'add_worker'}
PUBLIC_TOOLS = {'recall', 'thread_recall', 'drift_check', 'session_search', 'profile',
                'drift_history', 'ingest_obs', 'feedback_log'}
# These implementations scan global state, irrespective of a supplied project.
GLOBAL_READ = READ_TOOLS - {'recall', 'thread_recall', 'drift_check'}
GLOBAL_WRITE = WRITE_TOOLS - {'ingest_obs'}
ALIASES = {
    'C--Users-chunx': '-Users-chunxiao-wang',
    'C--Users-chunx-nautilus-v5': '-Users-chunxiao-wang-Projects-nautilus-v5',
    **{'C--Users-chunx-Projects-' + n: '-Users-chunxiao-wang-Projects-' + n
       for n in ['nautilus-core', 'nautilus-v5', 'nautilus-compass', 'nautilusflywheel', 'caishen-ai']},
}

def parse_scopes(value):
    if isinstance(value, dict):
        value = value.get('scopes', [])
    if not isinstance(value, list) or not all(isinstance(s, str) for s in value):
        return frozenset()
    # Unknown formats must never silently turn into full access.
    return frozenset(s for s in value if s in {'*', 'admin', 'tools.read', 'tools.write', 'resources.read'}
                     or s.startswith(('read:', 'write:')))

def internal(scopes):
    return bool(scopes & {'*', 'admin', 'tools.read', 'tools.write'})

def canonical_project(name):
    if not isinstance(name, str) or not name or name in {'.', '..'} or any(c in name for c in '/\\\x00'):
        raise ValueError('project must be a single memory namespace')
    return ALIASES.get(name, name)

def has_project(scopes, kind, project):
    if scopes & {'*', 'admin', kind + ':*'}:
        return True
    for scope in scopes:
        if scope.startswith(kind + ':'):
            try:
                if canonical_project(scope.split(':', 1)[1]) == project:
                    return True
            except ValueError:
                continue
    return False

def visible(scopes, name):
    if name not in READ_TOOLS | WRITE_TOOLS:
        return False
    if name not in PUBLIC_TOOLS and not internal(scopes):
        return False
    if scopes & {'*', 'admin'}:
        return True
    kind = 'read' if name in READ_TOOLS else 'write'
    if name in GLOBAL_READ:
        return 'read:*' in scopes
    if name in GLOBAL_WRITE:
        return 'write:*' in scopes or (internal(scopes) and 'tools.write' in scopes
                                       and any(s.startswith('write:') for s in scopes))
    return any(s.startswith(kind + ':') for s in scopes)

def authorize(scopes, name, arguments, default_project, projects_dir):
    """Return a normalized args copy; reject before any tool implementation runs."""
    if not visible(scopes, name):
        raise PermissionError('forbidden: tool not granted by token scopes')
    args = dict(arguments or {})
    if name in GLOBAL_READ | GLOBAL_WRITE:
        # Global implementations must never be exposed via a project-only grant.
        return args
    kind = 'read' if name in READ_TOOLS else 'write'
    if args.get('scope') == 'user':
        if not scopes & {'*', 'admin', 'read:*'} or kind != 'read':
            raise PermissionError('forbidden: scope=user requires read:*')
        return args
    project = args.get('project')
    if not project:
        grants = {canonical_project(s.split(':', 1)[1]) for s in scopes
                  if s.startswith(kind + ':') and s != kind + ':*'}
        project = next(iter(grants)) if len(grants) == 1 else default_project()
    project = canonical_project(project)
    if not has_project(scopes, kind, project):
        raise PermissionError('forbidden: project not granted by token scopes')
    base = Path(projects_dir).resolve()
    if not (base / project).resolve().is_relative_to(base):
        raise PermissionError('forbidden: project resolves outside memory root')
    args['project'] = project
    return args
