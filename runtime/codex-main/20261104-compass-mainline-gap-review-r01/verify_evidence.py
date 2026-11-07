"""Read saved evidence and write only this review's EVIDENCE.json.

No project imports, model calls, network requests, configuration or credential reads.
Rerunning refreshes observations of the separately progressing D2 pilot.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import subprocess

ROOT = Path('/Users/chunxiao.wang/Projects/nautilus-compass')
OUT = ROOT / 'runtime/codex-main/20261104-compass-mainline-gap-review-r01'
AUDIT = Path('/Users/chunxiao.wang/Documents/Codex/2026-11-03/task-4')
DELIVERY = AUDIT.parent / 'task-3'
OLD = ROOT / 'runtime/codex-main/20261103-history'
D2 = ROOT / 'runtime/scratch_distill_pilot_20261104'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def binding(path):
    path = Path(path)
    data = path.read_bytes()
    return {'path': str(path), 'sha256': sha(data), 'bytes': len(data)}


baseline = read_json(OUT / 'BASELINE.json')
sources = [ROOT / item for item in [
    'AGENTS.md', 'docs/agent-memory.index.md',
    'docs/soul/COMPASS_PAST_PRESENT_FUTURE_20261103.md',
    'docs/soul/TASK_MEMORY_FUEL_20261101.md',
    'docs/soul/MAINLINE_ROADMAP_20261101.md',
    'docs/soul/SESSION_DISTILL_PILOT_20261104.md',
    'mcp_server.py', 'mcp_http_local.py', 'mcp_access.py', 'daemon.py',
    'assay/submit.py', 'sdks/jev-trust/jev_trust/trust.py',
    'sdks/jev-trust/jev_trust/calib.py',
    'tools/distill_pilot/anchor_check.py', 'tools/distill_pilot/compress_arm.py',
    'outputs/recall_usefulness_baseline_20260823.json',
    'outputs/recall_usefulness_20260823.json',
]]
sources += [OLD / 'ADDENDUM_20261103_R2_EVIDENCE.json',
            ROOT.parent / 'nautilus-core/docs/org/agent_catalog.json']
for name in ['CV_eta_engineering_spec_v3.md',
             'training_blueprint_cv_arch_20261001.md',
             'CV_falsification_core_20261001.md']:
    sources.append(ROOT.parent / 'verification-learning-papers/docs' / name)
saved_ops = Path('/Users/chunxiao.wang/nautilus-audit/2026-11-02')
sources += [saved_ops / 'phase3/config-restoration/fresh-session-validation.json',
            saved_ops / 'phase4/mcp-import-collision-fix.json',
            DELIVERY / 'compass-resource-connectivity-20261104-r01/REPORT.txt',
            DELIVERY / 'compass-resource-connectivity-20261104-r01/config-and-route.json',
            ROOT.parent / 'nautilus-core/tools/compass_codex_entry.py']

audit_manifests = []
for revision in range(1, 5):
    folder = AUDIT / f'compass-m4-independent-audit-20261104-r0{revision}'
    name = 'AUDIT_DELIVERY_MANIFEST.json' if revision == 1 else 'DELIVERY_MANIFEST.json'
    manifest = read_json(folder / name)
    mismatches = [filename for filename, expected in manifest['files'].items()
                  if sha((folder / filename).read_bytes()) != expected]
    audit_manifests.append({'revision': revision, 'files': len(manifest['files']),
                            'mismatches': mismatches, 'manifest': binding(folder / name)})
    sources.append(folder / 'REPORT.txt')
for folder in ['compass-m4-pilot-20261104-r01',
               'compass-m4-contract-20261104-r04']:
    sources.append(DELIVERY / folder / 'REPORT.txt')
engine = DELIVERY / 'compass-m4-contract-20261104-r04/contract_engine.py'
sources.append(engine)
assert sha(engine.read_bytes()) == read_json(
    AUDIT / 'compass-m4-independent-audit-20261104-r04/SUMMARY.json')['target_code_sha256']

old = read_json(OLD / 'ADDENDUM_20261103_R2_EVIDENCE.json')
reused_code_checks = [
    {'path': row['path'], 'matches_previous': sha((ROOT / row['path']).read_bytes()) == row['worktree_sha256']}
    for row in old['code_bindings']]
assert all(row['matches_previous'] for row in reused_code_checks)
raw_records = []
for record in old['original_records']:
    if record['id'] not in ['U01', 'U12', 'U14', 'U18', 'U19']:
        continue
    with Path(record['path']).open('rb') as stream:
        line = next(line for number, line in enumerate(stream, 1) if number == record['line'])
    raw_records.append({key: record[key] for key in [
        'id', 'path', 'line', 'event_time_utc', 'event_time_new_york', 'excerpt']})
    raw_records[-1].update(record_sha256=sha(line),
                           matches_previous=sha(line) == record['record_sha256'])
new_session = Path.home() / '.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/e8fea918-0b0f-4c0e-8bc8-e043079ce344.jsonl'
with new_session.open('rb') as stream:
    for number, line in enumerate(stream, 1):
        if number not in [36, 112, 156, 297]:
            continue
        record = json.loads(line)
        content = record['message']['content']
        text = content if isinstance(content, str) else '\n'.join(
            item.get('text', '') for item in content
            if isinstance(item, dict) and item.get('type') == 'text')
        assert record['type'] == 'user' and not record.get('isMeta') and not record.get('isSidechain')
        raw_records.append({'id': f'NOV04-L{number}', 'path': str(new_session), 'line': number,
                            'event_time_utc': record['timestamp'],
                            'event_time_new_york': datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')).astimezone(ZoneInfo('America/New_York')).isoformat(),
                            'record_sha256': sha(line), 'excerpt': text,
                            'authority': 'original_user_historical_scope_only'})

r01 = []
for arm in ['bm25', 'bge_m3']:
    path = AUDIT / 'compass-m4-independent-audit-20261104-r01' / f'{arm}-challenge-results.json'
    rows = read_json(path)['rows']
    result = {'arm': arm, 'file': binding(path)}
    for label, subset in [('frozen_18', rows), ('posthoc_without_H04', [r for r in rows if r['id'] != 'H04'])]:
        subset = [row for row in subset if row['scope'] == 'in_corpus']
        all3 = sum(set(row['all_required_evidence_ids']).issubset(row['ranked_ids'][:3]) for row in subset)
        result[label] = {'n': len(subset), 'all_required_at3': all3}
    r01.append(result)
r02 = []
for mode in ['baseline', 'full']:
    path = AUDIT / 'compass-m4-independent-audit-20261104-r02' / f'NEW-{mode}.json'
    rows = read_json(path)['rows']
    scored = [row for row in rows if row['score']['all_evidence3'] is not None]
    t11 = next(row for row in rows if row['id'] == 'T11')
    r02.append({'mode': mode, 'n': len(scored),
                'all_required_at3': sum(row['score']['all_evidence3'] for row in scored),
                'T11_selected_ids': t11['processing']['selected_ids'], 'file': binding(path)})
cases = read_json(AUDIT / 'compass-m4-independent-audit-20261104-r04/CASE_RESULTS.json')
r04 = {'cases': len(cases), 'by_group': dict(Counter(row['group'] for row in cases)),
       'pass': sum(row['contract_pass'] is True for row in cases),
       'fail': sum(row['contract_pass'] is False for row in cases),
       'observation': [row['id'] for row in cases if row['contract_pass'] is None]}

d2_stats_bytes = (D2 / 'compress_stats.jsonl').read_bytes()
d2_rows = [json.loads(line) for line in d2_stats_bytes.splitlines() if line.strip()]
j1_bytes = (D2 / 'j1_results_partial.json').read_bytes()
j1 = json.loads(j1_bytes)
anchor_counts = []
for row in j1['results']:
    eligible = [anchor for anchor in row['anchors'] if 'note' not in anchor]
    matched = sum(bool(anchor['matched']) for anchor in eligible)
    assert len(eligible) == row['n_valid'] and matched == row['n_matched']
    anchor_counts.append({'session_id': row['session_id'], 'n': len(eligible), 'matched': matched})
total = sum(row['n'] for row in anchor_counts)
matched = sum(row['matched'] for row in anchor_counts)
mean = sum(row['matched'] / row['n'] for row in anchor_counts) / len(anchor_counts)
d2 = {'observation_time_ny': datetime.now(ZoneInfo('America/New_York')).isoformat(),
      'stats_path': str(D2 / 'compress_stats.jsonl'), 'stats_sha256': sha(d2_stats_bytes),
      'rows': len(d2_rows), 'unique_sessions': len({row['session_id'] for row in d2_rows}),
      'groups': dict(Counter(row['group'] for row in d2_rows)),
      'summary_files': len(list((D2 / 'summaries_local').glob('*.md'))),
      'total_source_bytes_from_stats': sum(row['source_bytes'] for row in d2_rows),
      'total_summary_bytes_from_stats': sum(row['summary_bytes'] for row in d2_rows),
      'j1': {'path': str(D2 / 'j1_results_partial.json'), 'sha256': sha(j1_bytes),
             'n': len(anchor_counts), 'anchors': total, 'matched': matched,
             'all_raw_anchors': sum(row['n_anchors'] for row in j1['results']),
             'excluded_noted_anchors': sum(row['n_anchors'] for row in j1['results']) - total,
             'micro_rate': matched / total, 'macro_rate': mean,
             'below_95': sum(row['matched'] / row['n'] < .95 for row in anchor_counts),
             'per_session': anchor_counts,
             'boundary': 'Recomputed saved boolean counts only; not semantic matching or full-batch acceptance'},
      'j5': read_json(D2 / 'j5_prefilter_probe.json'),
      'boundary': 'Concurrent pilot snapshot; no process/service/model inspected or controlled; bytes are not tokens'}
for name in ['D1_LOG.md', 'D2_LOG.md', 'j5_prefilter_probe.json', 'sample_manifest.json']:
    sources.append(D2 / name)

code_bindings = []
for filename in ['mcp_server.py', 'mcp_http_local.py', 'mcp_access.py', 'daemon.py',
                 'assay/submit.py', 'sdks/jev-trust/jev_trust/trust.py',
                 'tools/distill_pilot/anchor_check.py', 'tools/distill_pilot/compress_arm.py']:
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'log', '-1', '--format=%H', '--', filename], text=True).strip()
    committed = subprocess.run(['git', '-C', str(ROOT), 'show', f'HEAD:{filename}'], capture_output=True)
    code_bindings.append({**binding(ROOT / filename), 'last_file_commit': commit or None,
                           'matches_HEAD_blob': committed.returncode == 0 and sha(committed.stdout) == sha((ROOT / filename).read_bytes())})
preservation = [{**item, 'sha256_now': sha(Path(item['path']).read_bytes()),
                 'unchanged': sha(Path(item['path']).read_bytes()) == item['sha256']}
                for item in baseline['files']]
result = {'task_id': 'COMPASS-MAINLINE-GAP-REVIEW-20261104-R01',
          'at_new_york': datetime.now(ZoneInfo('America/New_York')).isoformat(),
          'scope': 'Bounded saved-evidence review; writes only current review directory',
          'preflight': {'goal': None, 'previous_own_turn': 'completed',
                        'current_thread': '01a19fd4-024d-7f31-8d8a-aec21d8d828d',
                        'equivalent_review_in_codex_main': False,
                        'other_pilot': 'D2 artifacts observed; no duplicate execution'},
          'sources': [binding(path) for path in sources], 'original_records': raw_records,
          'audit_delivery_binding_checks': audit_manifests,
          'saved_result_recomputation': {'r01': r01, 'r02': r02, 'r04': r04},
          'D2_snapshot': d2, 'code_bindings': code_bindings, 'preservation': preservation,
          'reused_code_checks': reused_code_checks,
          'HEAD_at_start': baseline['head'],
          'HEAD_at_end': subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
          'limitations': ['No current service or GUI connectivity probe',
                         'Current unified-MCP decision taken from this delegation; historical raw decision not located',
                         'M4 r04 is single-process engineering evidence',
                         'No new retrieval/contract cases or semantic/consumer acceptance run',
                         'D2 and historical raw sessions may continue to append']}
assert all(item['unchanged'] for item in preservation)
assert not any(item['mismatches'] for item in audit_manifests)
assert all(item.get('matches_previous', True) for item in raw_records)
target = OUT / 'EVIDENCE.json'
target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'evidence': str(target), 'sources': len(sources), 'raw_records': len(raw_records),
                  'r01': r01, 'r02': r02, 'r04': r04, 'D2': d2['j1'],
                  'all_preserved': True}, ensure_ascii=False))
