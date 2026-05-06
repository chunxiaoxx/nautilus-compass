#!/usr/bin/env node
// compass-mcp · npm wrapper that spawns the Python MCP server over stdio.
// Lets users install via:  npm i -g @nautilus/compass-mcp
// Then add to Claude Desktop / Cursor / Cline mcp.json:
//   { "compass": { "command": "compass-mcp" } }

const { spawn, spawnSync } = require('node:child_process');
const path = require('node:path');
const fs = require('node:fs');

const PKG_ROOT = path.resolve(__dirname, '..');
const SERVER_PY = path.join(PKG_ROOT, 'mcp_server.py');

function findPython() {
  const candidates = process.platform === 'win32'
    ? ['python', 'python3', 'py']
    : ['python3', 'python'];
  for (const cmd of candidates) {
    const r = spawnSync(cmd, ['--version'], { stdio: 'ignore' });
    if (r.status === 0) return cmd;
  }
  return null;
}

const argv = process.argv.slice(2);

if (argv.includes('--self-check')) {
  const py = findPython();
  if (!py) {
    console.error('compass-mcp · ERROR: no Python 3.x found in PATH');
    process.exit(1);
  }
  if (!fs.existsSync(SERVER_PY)) {
    console.error(`compass-mcp · ERROR: ${SERVER_PY} missing from package`);
    process.exit(1);
  }
  console.log(`compass-mcp · ok · python=${py} · server=${SERVER_PY}`);
  process.exit(0);
}

if (argv.includes('--postinstall')) {
  const py = findPython();
  if (!py) {
    console.warn('compass-mcp · WARN: Python 3.x not found · install Python first');
    process.exit(0);
  }
  console.log(`compass-mcp · ready · python=${py}`);
  process.exit(0);
}

const py = findPython();
if (!py) {
  console.error('compass-mcp · FATAL: Python 3.x required but not found in PATH');
  process.exit(1);
}

const child = spawn(py, [SERVER_PY, ...argv], {
  stdio: 'inherit',
  windowsHide: true,
});

child.on('exit', (code, signal) => {
  if (signal) process.kill(process.pid, signal);
  else process.exit(code ?? 0);
});

process.on('SIGINT', () => child.kill('SIGINT'));
process.on('SIGTERM', () => child.kill('SIGTERM'));
