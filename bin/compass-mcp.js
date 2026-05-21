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

// v1.7.1 · Layer 5 · npx init subcommand (v2 spec S2)
// Usage: npx nautilus-compass init
// Creates .compass/ workspace · .env template · sample anchors · Claude Code hooks
if (argv[0] === 'init') {
  const cwd = process.cwd();
  const compassDir = path.join(cwd, '.compass');

  if (fs.existsSync(compassDir)) {
    console.log(`compass-mcp · ${compassDir} already exists · skipping init`);
    console.log(`compass-mcp · remove .compass/ first if you want to re-init`);
    process.exit(0);
  }
  fs.mkdirSync(compassDir, { recursive: true });
  console.log(`✓ created ${compassDir}/`);

  const envTemplate = [
    '# nautilus-compass · environment template (v1.7.1)',
    '# See https://github.com/chunxiaoxx/nautilus-compass#configuration',
    '',
    '# Embedding provider · default local BGE-m3 (no API key needed)',
    'COMPASS_EMBEDDING_PROVIDER=local',
    '# COMPASS_OPENAI_API_KEY=sk-...',
    '# COMPASS_GEMINI_API_KEY=...',
    '',
    '# Agent identity (auto-detected if blank)',
    'COMPASS_AGENT_TYPE=claude-code',
    'COMPASS_USER_ID=u_local',
    '',
    '# Daemon (auto-managed)',
    'COMPASS_DAEMON_HOST=127.0.0.1',
    'COMPASS_DAEMON_PORT=9876',
    '',
    '# Lifecycle (v1.7.1 · llm-wiki2 fuse · default values)',
    'COMPASS_LIFECYCLE_DEFAULT_TIER=working',
    'COMPASS_LIFECYCLE_FORGET_ENABLED=false',
    '',
    '# Chain recall (v1.7 · MEME-extension cascade closure)',
    '# COMPASS_CHAIN_RECALL=1',
    ''
  ].join('\n');
  fs.writeFileSync(path.join(compassDir, '.env.template'), envTemplate);
  console.log(`✓ wrote ${compassDir}/.env.template`);

  const anchorTemplate = JSON.stringify([
    {
      id: 'verify-before-claim',
      task: 'Run actual verification (curl/test/log) before claiming completion',
      trigger_keywords: ['deploy', 'verify', 'ship', 'complete', 'done', '完成'],
      evidence_count: 0,
      source: 'user-template'
    },
    {
      id: 'no-llm-at-ingest',
      task: 'Never call LLM at memory write time · use schema-declared fields',
      trigger_keywords: ['ingest', 'store', 'memory', 'write'],
      evidence_count: 0,
      source: 'user-template'
    },
    {
      id: 'lifecycle-tier-deterministic',
      task: 'Use tier/decay_rate/forget_at frontmatter · no LLM tier promotion',
      trigger_keywords: ['tier', 'lifecycle', 'forget', 'decay', 'promote'],
      evidence_count: 0,
      source: 'user-template'
    }
  ], null, 2) + '\n';
  fs.writeFileSync(path.join(compassDir, 'anchors.json'), anchorTemplate);
  console.log(`✓ wrote ${compassDir}/anchors.json`);

  const hooksConfig = {
    description: 'compass · v1.7.1 Claude Code hook templates',
    instructions: 'Merge contents into ~/.claude/settings.json hooks section',
    hooks: {
      Stop: [
        {
          command: 'python <COMPASS_REPO>/stop_hook.py',
          description: 'compass · auto-distill session + drift check'
        }
      ],
      SessionStart: [
        {
          command: 'python <COMPASS_REPO>/stop_hook.py --hook SessionStart',
          description: 'compass · v1.7.1 lifecycle SessionStart emit'
        }
      ],
      PostToolUse: [
        {
          command: 'python <COMPASS_REPO>/stop_hook.py --hook PostToolUse',
          description: 'compass · v1.7.1 lifecycle PostToolUse emit'
        }
      ],
      SessionEnd: [
        {
          command: 'python <COMPASS_REPO>/stop_hook.py --hook SessionEnd',
          description: 'compass · v1.7.1 lifecycle SessionEnd promotion candidate'
        }
      ]
    }
  };
  fs.writeFileSync(
    path.join(compassDir, 'claude-code-hooks.json'),
    JSON.stringify(hooksConfig, null, 2) + '\n'
  );
  console.log(`✓ wrote ${compassDir}/claude-code-hooks.json`);

  const projectReadme = [
    '# compass project workspace',
    '',
    'Created by `npx nautilus-compass init` (v1.7.1 · Layer 5 adoption).',
    '',
    '## Files',
    '',
    '- `.env.template` · copy to `.env` and fill in',
    '- `anchors.json` · sample anchor strategy set',
    '- `claude-code-hooks.json` · hook configuration template',
    '',
    '## Next steps',
    '',
    '1. `cp .env.template .env` and configure',
    '2. Replace `<COMPASS_REPO>` in claude-code-hooks.json with your compass install path',
    '3. Merge into `~/.claude/settings.json` hooks section',
    '4. Restart Claude Code · verify with `compass-mcp --self-check`',
    '5. Full docs: https://github.com/chunxiaoxx/nautilus-compass',
    ''
  ].join('\n');
  fs.writeFileSync(path.join(compassDir, 'README.md'), projectReadme);
  console.log(`✓ wrote ${compassDir}/README.md`);

  console.log('');
  console.log('✓ compass init complete · .compass/ workspace created');
  console.log('');
  console.log('Next:');
  console.log('  cp .compass/.env.template .compass/.env  # then edit');
  console.log('  see .compass/README.md for hooks wiring');
  process.exit(0);
}

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
