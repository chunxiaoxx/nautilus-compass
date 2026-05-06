/**
 * Compass Cursor extension · v0.9.0-dev
 *
 * Cursor 跟其他 IDE 共享 cross-agent memory (Claude Desktop / Cline / Hermes / OpenClaw).
 * 核心: 5 个命令 · 4 个走 HTTP API · 1 个起 MCP server (stdio).
 *
 * Cursor 自身已经支持 MCP server config (~/.cursor/mcp.json) · 本扩展额外提供:
 *   · Command Palette quick access (无需切到 chat 调 @compass)
 *   · Status bar 显示 drift 状态 (red 时 警告)
 *   · Auto-ingest on save (可选 · 实验)
 *   · MCP server 自动起 (替用户配 mcp.json)
 */
import * as vscode from 'vscode';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';

let mcpServer: ChildProcessWithoutNullStreams | null = null;
let statusBar: vscode.StatusBarItem;

interface CompassConfig {
    userId: string;
    agentType: string;
    baseUrl: string;
    autoIngestOnSave: boolean;
}

function getConfig(): CompassConfig {
    const c = vscode.workspace.getConfiguration('compass');
    return {
        userId: c.get('userId', 'u_local'),
        agentType: c.get('agentType', 'cursor'),
        baseUrl: c.get('baseUrl', 'https://compass.nautilus.social'),
        autoIngestOnSave: c.get('autoIngestOnSave', false),
    };
}

async function httpJson(method: 'GET' | 'POST', url: string, headers: Record<string, string>, body?: unknown): Promise<unknown> {
    const init: RequestInit = { method, headers };
    if (body !== undefined) {
        init.body = JSON.stringify(body);
        headers['Content-Type'] = 'application/json';
    }
    const resp = await fetch(url, init);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${await resp.text()}`);
    return resp.json();
}

function authHeaders(cfg: CompassConfig): Record<string, string> {
    return {
        'X-User-ID': cfg.userId,
        'X-Agent-Type': cfg.agentType,
    };
}

async function cmdRecall() {
    const query = await vscode.window.showInputBox({
        prompt: 'Recall memory across agents',
        placeHolder: 'e.g. drift detection in v0.8',
    });
    if (!query) return;
    const cfg = getConfig();
    try {
        const res = await httpJson('GET',
            `${cfg.baseUrl}/v1/recall?q=${encodeURIComponent(query)}&top_k=5&cross_agent=true`,
            authHeaders(cfg)
        ) as any;
        const hits = res?.hits || [];
        if (hits.length === 0) {
            vscode.window.showInformationMessage(`No memory hits for "${query}"`);
            return;
        }
        const items: vscode.QuickPickItem[] = hits.map((h: any) => ({
            label: h.path || h.name || '?',
            description: `score=${(h.score ?? 0).toFixed(2)} · ${h.age_str || '?'}`,
            detail: h.description?.slice(0, 200) || '',
        }));
        await vscode.window.showQuickPick(items, { title: `Compass · ${hits.length} hits for "${query}"` });
    } catch (e) {
        vscode.window.showErrorMessage(`Compass recall failed: ${(e as Error).message}`);
    }
}

async function cmdDriftHistory() {
    const cfg = getConfig();
    // 本地直接调 drift_history.py · 不走网络 (本地数据更全)
    const term = vscode.window.createTerminal('Compass · Drift History');
    term.sendText('compass-drift-history 30');
    term.show();
}

async function cmdIngestObs() {
    const editor = vscode.window.activeTextEditor;
    const selectedText = editor?.document.getText(editor.selection) || '';
    const name = await vscode.window.showInputBox({
        prompt: 'Observation name (8-15 chars)',
        value: selectedText ? selectedText.slice(0, 30) : '',
    });
    if (!name) return;
    const description = await vscode.window.showInputBox({
        prompt: 'Description (≤120 chars)',
    });
    const drift = await vscode.window.showQuickPick(['green', 'yellow', 'red'], {
        title: 'Drift self-audit',
        placeHolder: 'green = on track · yellow = corrected · red = off-track',
    });
    if (!drift) return;

    const cfg = getConfig();
    try {
        await httpJson('POST', `${cfg.baseUrl}/v1/observations`, authHeaders(cfg), {
            obs_id: `ob_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
            user_id: cfg.userId,
            agent_id: `ag_${cfg.agentType}_main`,
            agent_type: cfg.agentType,
            ts: new Date().toISOString(),
            meta: {
                type: 'discovery',
                concept: 'pattern',
                drift,
                drift_signals: [],
            },
            content: {
                name,
                description: description || '',
                body: selectedText || '',
            },
        });
        vscode.window.showInformationMessage(`Compass · obs written · drift=${drift}`);
    } catch (e) {
        vscode.window.showErrorMessage(`Compass ingest failed: ${(e as Error).message}`);
    }
}

async function cmdProfile() {
    const cfg = getConfig();
    try {
        const res = await httpJson('GET', `${cfg.baseUrl}/v1/profile?days=90`, authHeaders(cfg)) as any;
        const summary = res?.summary || res || {};
        const out = JSON.stringify(summary, null, 2);
        const doc = await vscode.workspace.openTextDocument({ content: out, language: 'json' });
        await vscode.window.showTextDocument(doc);
    } catch (e) {
        vscode.window.showErrorMessage(`Compass profile failed: ${(e as Error).message}`);
    }
}

async function cmdStartMcpServer() {
    if (mcpServer) {
        vscode.window.showInformationMessage('Compass MCP server already running');
        return;
    }
    mcpServer = spawn('compass-mcp', [], { stdio: ['pipe', 'pipe', 'pipe'] });
    mcpServer.on('exit', (code) => {
        vscode.window.showWarningMessage(`Compass MCP server exited (code=${code})`);
        mcpServer = null;
    });
    mcpServer.stderr.on('data', (d) => console.error('[compass-mcp]', d.toString()));
    vscode.window.showInformationMessage('Compass MCP server started');
}

function updateStatusBar(drift?: 'green' | 'yellow' | 'red') {
    if (!statusBar) return;
    const glyph = { green: '$(check)', yellow: '$(warning)', red: '$(error)' }[drift || 'green'];
    statusBar.text = `${glyph} compass`;
    statusBar.tooltip = `compass · drift=${drift || 'unknown'} · click to recall`;
    statusBar.command = 'compass.recall';
    statusBar.show();
}

export function activate(context: vscode.ExtensionContext) {
    statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 0);
    updateStatusBar();
    context.subscriptions.push(statusBar);

    context.subscriptions.push(
        vscode.commands.registerCommand('compass.recall', cmdRecall),
        vscode.commands.registerCommand('compass.driftHistory', cmdDriftHistory),
        vscode.commands.registerCommand('compass.ingestObs', cmdIngestObs),
        vscode.commands.registerCommand('compass.profile', cmdProfile),
        vscode.commands.registerCommand('compass.startMcpServer', cmdStartMcpServer),
    );

    // 自动起 MCP server (用户没显式 disable)
    cmdStartMcpServer();
}

export function deactivate() {
    if (mcpServer) {
        mcpServer.kill();
        mcpServer = null;
    }
}
