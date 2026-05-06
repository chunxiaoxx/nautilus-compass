#!/usr/bin/env node
/**
 * @nautilus/compass-mcp · Node.js wrapper for compass MCP server.
 *
 * 实际 MCP server 是 Python (mcp_server.py · 已写好 · stdio JSON-RPC).
 * 本 wrapper 做 4 件事:
 *   1. 检查 Python 3.9+ 可用
 *   2. 检查 nautilus-compass python package 装了 (没装就引导 pip install)
 *   3. 转发 stdio (本进程 stdin/stdout ↔ python subprocess)
 *   4. 透传 env vars (COMPASS_USER_ID · COMPASS_AGENT_TYPE · 等)
 *
 * 这样 npm-first 用户 (Cursor / Cline / Claude Desktop user) 不用懂 Python.
 */

const { spawn, spawnSync } = require('node:child_process');

function findPython() {
  for (const cmd of ['python3', 'python']) {
    try {
      const r = spawnSync(cmd, ['--version'], { encoding: 'utf-8' });
      if (r.status === 0) {
        const ver = (r.stdout + r.stderr).trim();
        const m = ver.match(/Python (\d+)\.(\d+)/);
        if (m && (parseInt(m[1]) > 3 || (parseInt(m[1]) === 3 && parseInt(m[2]) >= 9))) {
          return cmd;
        }
      }
    } catch (_) {}
  }
  return null;
}

function checkCompassInstalled(python) {
  const r = spawnSync(python, ['-c', 'import nautilus_compass; print("OK")'], { encoding: 'utf-8' });
  if (r.status === 0 && r.stdout.includes('OK')) return true;
  // fallback: detect via plugin dir
  const r2 = spawnSync(python, ['-c',
    'import os, sys; p = os.path.expanduser("~/.claude/plugins/nautilus-compass/mcp_server.py"); ' +
    'sys.exit(0 if os.path.exists(p) else 1)'
  ]);
  return r2.status === 0;
}

function findMcpServer(python) {
  // 1. installed package
  const r1 = spawnSync(python, ['-c',
    'import importlib.util; s = importlib.util.find_spec("nautilus_compass.mcp_server"); ' +
    'print(s.origin if s else "")'
  ], { encoding: 'utf-8' });
  if (r1.status === 0 && r1.stdout.trim()) return { python, args: ['-m', 'nautilus_compass.mcp_server'] };

  // 2. plugin dir
  const r2 = spawnSync(python, ['-c',
    'import os; print(os.path.expanduser("~/.claude/plugins/nautilus-compass/mcp_server.py"))'
  ], { encoding: 'utf-8' });
  const path = (r2.stdout || '').trim();
  if (path) {
    const r3 = spawnSync(python, ['-c', `import os, sys; sys.exit(0 if os.path.exists("${path.replace(/\\/g, '/')}") else 1)`]);
    if (r3.status === 0) return { python, args: [path] };
  }
  return null;
}

function main() {
  if (process.argv.includes('--selftest')) {
    const python = findPython();
    if (!python) { console.error('FAIL: no Python 3.9+ found'); process.exit(1); }
    if (!checkCompassInstalled(python)) {
      console.error('FAIL: nautilus-compass not installed · pip install nautilus-compass');
      process.exit(1);
    }
    console.log('OK: ' + python + ' + nautilus-compass found');
    process.exit(0);
  }

  const python = findPython();
  if (!python) {
    console.error('compass-mcp: Python 3.9+ required · install from python.org');
    process.exit(1);
  }

  const target = findMcpServer(python);
  if (!target) {
    console.error('compass-mcp: nautilus-compass not found · install:');
    console.error('  pip install nautilus-compass');
    console.error('  # or: uv tool install nautilus-compass');
    console.error('  # or: clone repo to ~/.claude/plugins/nautilus-compass');
    process.exit(1);
  }

  const child = spawn(target.python, target.args, {
    stdio: 'inherit',
    env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUTF8: '1' },
  });
  child.on('exit', (code) => process.exit(code ?? 0));
  child.on('error', (err) => {
    console.error('compass-mcp spawn error:', err.message);
    process.exit(1);
  });
}

main();
