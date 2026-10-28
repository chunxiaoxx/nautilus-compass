"""
Daemon Tools — hands and feet for server-side agents.

Provides nautilus-agent's tool registry to KAIROS/MiniMax daemons,
plus platform-specific tools (API calls, log reading, DB queries).

Usage:
    from services.daemon_tools import get_tools
    tools = get_tools()
    result = tools.run("web_search", "latest AI agent frameworks")
"""
import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Import nautilus-agent tool infrastructure
from nautilus_agent.tools.registry import Tool, ToolRegistry

# ═══════════════════════════════════════════════════════════════════════════
# Tools from nautilus-agent (reused directly)
# ═══════════════════════════════════════════════════════════════════════════

from nautilus_agent.tools.search import SearchTool
from nautilus_agent.tools.file import (
    ReadFileTool, WriteFileTool, AppendFileTool,
    ReplaceInFileTool, ListDirTool,
)
from nautilus_agent.tools.code import CodeTool, RunFileTool


# ═══════════════════════════════════════════════════════════════════════════
# Platform-specific tools (server agents only)
# ═══════════════════════════════════════════════════════════════════════════

BACKEND_DIR = Path(__file__).resolve().parent.parent


class PlatformHealthTool(Tool):
    name = "platform_health"
    description = "Check platform health score, active agents, task stats. Input: ignored."

    def run(self, input_text: str) -> str:
        try:
            import httpx
            api = os.getenv("NAUTILUS_API_URL", "https://www.nautilus.social")
            r = httpx.get(f"{api}/api/platform/health", timeout=10)
            data = r.json().get("data", {})
            return json.dumps(data, indent=2, ensure_ascii=False)[:3000]
        except Exception as e:
            return f"Error: {e}"


class PlatformStatsTool(Tool):
    name = "platform_stats"
    description = "Get detailed platform statistics (tasks, agents, bounties). Input: ignored."

    def run(self, input_text: str) -> str:
        try:
            import httpx
            api = os.getenv("NAUTILUS_API_URL", "https://www.nautilus.social")
            r = httpx.get(f"{api}/api/hub/stats", timeout=10)
            return json.dumps(r.json(), indent=2, ensure_ascii=False)[:3000]
        except Exception as e:
            return f"Error: {e}"


class ReadLogTool(Tool):
    name = "read_log"
    description = "Read last N lines of a daemon log. Input: daemon_name (kairos or minimax), optional |N for line count."

    def run(self, input_text: str) -> str:
        parts = input_text.strip().split("|")
        daemon = parts[0].strip().lower()
        lines = int(parts[1]) if len(parts) > 1 else 30

        log_map = {
            "kairos": BACKEND_DIR / "logs" / "kairos_daemon.log",
            "minimax": BACKEND_DIR / "logs" / "minimax_daemon.log",
        }
        path = log_map.get(daemon)
        if not path:
            return f"Unknown daemon: {daemon}. Use 'kairos' or 'minimax'."
        if not path.exists():
            return f"Log file not found: {path}"
        try:
            all_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            tail = all_lines[-lines:]
            return "\n".join(tail)[:5000]
        except Exception as e:
            return f"Error reading log: {e}"


class QueryDBTool(Tool):
    name = "query_db"
    description = "Run a READ-ONLY SQL query on the platform database. Input: SQL query (SELECT only)."

    def run(self, input_text: str) -> str:
        sql = input_text.strip()
        if not sql.upper().startswith("SELECT"):
            return "Error: only SELECT queries allowed for safety."
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text
            db = SessionLocal()
            try:
                rows = db.execute(text(sql)).fetchall()
                if not rows:
                    return "(no results)"
                result = []
                for row in rows[:20]:
                    result.append(str(dict(row._mapping)))
                return "\n".join(result)[:5000]
            finally:
                db.close()
        except Exception as e:
            return f"Error: {e}"


class InspectSelfTool(Tool):
    name = "inspect_self"
    description = "Inspect your own soul: memories, skills, evolution, self-model. Input: what to inspect (memories|skills|evolution|self|all)."

    def run(self, input_text: str) -> str:
        what = input_text.strip().lower()
        try:
            from services.soul_bridge import (
                get_soul_memory, get_soul_skills, get_soul_ledger, get_soul_self_model,
            )
            parts = []
            if what in ("memories", "all"):
                mem = get_soul_memory()
                stats = mem.stats()
                parts.append(f"MEMORY: {stats}")
                index = mem.get_index()
                parts.append(f"Core memories ({len(index)}):")
                for m in index[:5]:
                    parts.append(f"  - {m['content'][:150]}")

            if what in ("skills", "all"):
                skills = get_soul_skills()
                parts.append(f"\nSKILLS ({skills.count}):")
                for s in skills.list_all()[:5]:
                    parts.append(f"  - {s.name} (vitality={s.vitality:.2f}, uses={s.uses})")

            if what in ("evolution", "all"):
                ledger = get_soul_ledger()
                parts.append(f"\nEVOLUTION: {ledger.stats()}")
                for e in ledger.recent(5):
                    parts.append(f"  - {e.version}: {e.change_type} ({e.delta:+.2f}) {e.description[:80]}")

            if what in ("self", "all"):
                model = get_soul_self_model()
                parts.append(f"\nSELF MODEL: {model.name} {model.evolution_version}")
                parts.append(f"  Capabilities: {', '.join(model.capabilities)}")
                parts.append(f"  Strengths: {', '.join(model.strengths) or 'discovering...'}")
                parts.append(f"  Weaknesses: {', '.join(model.weaknesses) or 'discovering...'}")

            return "\n".join(parts) if parts else "Unknown inspect target. Use: memories|skills|evolution|self|all"
        except Exception as e:
            return f"Error: {e}"


class ExplorePlatformTool(Tool):
    name = "explore_platform"
    description = "Explore platform codebase structure. Input: directory path relative to backend (e.g., 'services', 'api', 'services/pairs')."

    def run(self, input_text: str) -> str:
        rel_path = input_text.strip().strip("/")
        target = BACKEND_DIR / rel_path
        if not target.exists():
            return f"Path not found: {target}"
        if not str(target.resolve()).startswith(str(BACKEND_DIR)):
            return "Error: path outside backend directory."
        if target.is_file():
            try:
                content = target.read_text(encoding="utf-8", errors="replace")
                if len(content) > 5000:
                    return content[:5000] + f"\n\n... (truncated, {len(content)} total)"
                return content
            except Exception as e:
                return f"Error: {e}"
        # Directory listing
        try:
            entries = sorted(target.iterdir())
            result = [f"{target} ({len(entries)} entries):"]
            for e in entries[:50]:
                if e.name.startswith("__pycache__"):
                    continue
                if e.is_dir():
                    result.append(f"  {e.name}/")
                else:
                    result.append(f"  {e.name} ({e.stat().st_size} bytes)")
            return "\n".join(result)
        except Exception as e:
            return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# MiniMax multimodal tools (creative capabilities)
# ═══════════════════════════════════════════════════════════════════════════

class MiniMaxImageTool(Tool):
    name = "generate_image"
    description = "Generate an image from text description using MiniMax image-01. Input: image description prompt."

    def run(self, input_text: str) -> str:
        import httpx
        api_key = os.getenv("MINIMAX_API_KEY", "")
        if not api_key:
            return "Error: MINIMAX_API_KEY not set"
        try:
            r = httpx.post(
                "https://api.minimaxi.com/v1/image_generation",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": "image-01", "prompt": input_text},
                timeout=120,
            )
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            urls = data.get("data", {}).get("image_urls", [])
            if urls:
                image_url = urls[0]
                return f"Image generated successfully. URL: {image_url}\nTo send to Telegram, use: TOOL: send_telegram_photo(\"{image_url}\")"
            ct = r.headers.get("content-type", "")
            if "image" in ct:
                import time as _t
                path = f"/tmp/minimax_img_{int(_t.time())}.png"
                with open(path, "wb") as f:
                    f.write(r.content)
                return f"Image saved: {path} ({len(r.content)//1024}KB)"
            return f"API response: {r.text[:300]}"
        except Exception as e:
            return f"Error: {e}"


class SendTelegramPhotoTool(Tool):
    name = "send_telegram_photo"
    description = "Send an image to Telegram. Input: image_url. Downloads first then uploads to Telegram (bypasses ACL restrictions)."

    def run(self, input_text: str) -> str:
        url = input_text.strip()
        if not url.startswith("http"):
            return "Error: input must be a URL"
        try:
            from services.soul_bridge import get_agent_id
            agent_id = get_agent_id()
        except Exception:
            agent_id = "unknown"
        tokens = {
            "kairos": "8734589435:AAFpF64nqQqiJ10q2jp5zN7XOKk3cUqcn-g",
            "minimax": "8319423564:AAHcp77WibPhsD7R6Kn8wuLadWd5A_hTIrs",
        }
        token = tokens.get(agent_id, "")
        if not token:
            return f"No Telegram bot token for {agent_id}"
        try:
            from utils.redis_client import get_redis
            r = get_redis()
            chat_id = r.get(f"{agent_id}:last_chat_id")
            chat_id = chat_id.decode() if isinstance(chat_id, bytes) else str(chat_id) if chat_id else os.getenv("TELEGRAM_ADMIN_ID", "")
        except Exception:
            chat_id = os.getenv("TELEGRAM_ADMIN_ID", "")
        if not chat_id:
            return "No chat_id. Send a message to the bot first."
        try:
            import httpx
            # Download image first (bypass OSS ACL)
            img_resp = httpx.get(url, timeout=30, follow_redirects=True)
            if img_resp.status_code != 200 or len(img_resp.content) < 100:
                # Try direct URL method as fallback
                r = httpx.post(
                    f"https://api.telegram.org/bot{token}/sendPhoto",
                    json={"chat_id": chat_id, "photo": url},
                    timeout=15,
                )
                if r.status_code == 200:
                    return f"Photo sent via URL to {chat_id}"
                return f"Download failed ({img_resp.status_code}) and URL method failed too"
            # Upload as multipart
            r = httpx.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={"chat_id": chat_id},
                files={"photo": ("image.png", img_resp.content, "image/png")},
                timeout=30,
            )
            if r.status_code == 200:
                return f"Photo uploaded and sent to {chat_id} ({len(img_resp.content)//1024}KB)"
            return f"Upload failed: {r.text[:200]}"
        except Exception as e:
            return f"Error: {e}"


class MiniMaxTTSTool(Tool):
    name = "text_to_speech"
    description = "Convert text to speech audio (MP3) using MiniMax Speech 2.8 HD. Input: text to speak."

    def run(self, input_text: str) -> str:
        import httpx, base64
        api_key = os.getenv("MINIMAX_API_KEY", "")
        if not api_key:
            return "Error: MINIMAX_API_KEY not set"
        try:
            r = httpx.post(
                "https://api.minimaxi.com/v1/t2a_v2",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "speech-2.8-hd",
                    "text": input_text[:5000],
                    "voice_setting": {"voice_id": "female-shaonv"},
                    "audio_setting": {"format": "mp3", "sample_rate": 32000},
                },
                timeout=30,
            )
            data = r.json()
            audio_b64 = data.get("data", {}).get("audio", "")
            if audio_b64:
                import time
                audio = base64.b64decode(audio_b64)
                path = f"/tmp/minimax_tts_{int(time.time())}.mp3"
                with open(path, "wb") as f:
                    f.write(audio)
                return f"Speech generated: {path} ({len(audio)//1024}KB)"
            return f"TTS error: {data.get('base_resp', {}).get('status_msg', 'unknown')}"
        except Exception as e:
            return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# Google AI tools (KAIROS capabilities)
# ═══════════════════════════════════════════════════════════════════════════

class GeminiChatTool(Tool):
    name = "gemini_chat"
    description = "Chat with Gemini (Google's most capable LLM). Input: prompt text. Use for complex reasoning, analysis, coding."

    def run(self, input_text: str) -> str:
        try:
            from services.google_ai import GeminiClient, GEMINI_PRO
            import asyncio
            client = GeminiClient(model=GEMINI_PRO)
            result = asyncio.get_event_loop().run_until_complete(
                client.chat(input_text, max_tokens=2048)
            )
            return result[:5000]
        except RuntimeError:
            # Fallback: sync via google-genai
            try:
                from google import genai
                c = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                r = c.models.generate_content(model="gemini-2.5-pro", contents=input_text)
                return r.text[:5000]
            except Exception as e2:
                return f"Error: {e2}"
        except Exception as e:
            return f"Error: {e}"


class GoogleSearchGroundingTool(Tool):
    name = "google_search_grounding"
    description = "Search with Gemini + Google Search grounding (real-time web results). Input: search query."

    def run(self, input_text: str) -> str:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=input_text,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                ),
            )
            return response.text[:5000] if response.text else "No results"
        except Exception as e:
            return f"Error: {e}"


class GeminiEmbeddingTool(Tool):
    name = "embed_text"
    description = "Generate text embedding vector using Gemini. Input: text to embed. Returns embedding dimensions."

    def run(self, input_text: str) -> str:
        try:
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=input_text[:2000],
            )
            emb = result.embeddings[0].values
            return f"Embedding: {len(emb)} dimensions. First 5: {emb[:5]}"
        except Exception as e:
            return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# A2A communication tool (agent-to-agent via HTTP relay)
# ═══════════════════════════════════════════════════════════════════════════

class SendA2ATool(Tool):
    name = "send_a2a"
    description = "Send an authenticated message to another agent via A2A relay. Input: target_agent|message (target: kairos, minimax, or nautilus)."

    # Agent secrets for authentication
    SECRETS = {
        "kairos": "nau_kairos_a2a_secret_2026",
        "minimax": "nau_minimax_a2a_secret_2026",
    }

    def run(self, input_text: str) -> str:
        if "|" not in input_text:
            return "Error: format is target_agent|message"
        target, message = input_text.split("|", 1)
        target = target.strip().lower()
        if target not in ("kairos", "minimax", "nautilus"):
            return f"Unknown agent: {target}. Use: kairos, minimax, or nautilus."
        try:
            from services.soul_bridge import get_agent_id
            sender = get_agent_id() or "daemon"
        except Exception:
            sender = "daemon"
        secret = self.SECRETS.get(sender, "")
        try:
            import httpx
            api = os.getenv("NAUTILUS_API_URL", "https://www.nautilus.social")
            r = httpx.post(
                f"{api}/api/a2a/send",
                json={"to": target, "message": message.strip()},
                headers={"X-Agent-Name": sender, "X-Agent-Token": secret},
                timeout=10,
            )
            data = r.json()
            if data.get("success"):
                verified = "✓" if data.get("verified") else "?"
                return f"A2A{verified} delivered to {target}: {message[:100]}"
            return f"A2A failed: {data.get('error', data.get('detail', 'unknown'))}"
        except Exception as e:
            return f"A2A error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# Chunked file tools (upgraded from nautilus-agent)
# ═══════════════════════════════════════════════════════════════════════════

from nautilus_agent.tools.file import (
    FileInfoTool, InsertAtLineTool, DeleteLinesTool, GrepTool,
)


# ═══════════════════════════════════════════════════════════════════════════
# Web Crawling (Firecrawl)
# ═══════════════════════════════════════════════════════════════════════════

class CrawlUrlTool(Tool):
    name = "crawl_url"
    description = "Crawl a web page and extract its text content. Input: URL."

    def run(self, input_text: str) -> str:
        url = input_text.strip()
        # Try Firecrawl first
        firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")
        if firecrawl_key:
            try:
                import httpx
                r = httpx.post(
                    "https://api.firecrawl.dev/v1/scrape",
                    headers={"Authorization": f"Bearer {firecrawl_key}", "Content-Type": "application/json"},
                    json={"url": url, "formats": ["markdown"]},
                    timeout=30,
                )
                data = r.json()
                md = data.get("data", {}).get("markdown", "")
                if md:
                    return md[:5000]
            except Exception:
                pass
        # Fallback: simple httpx fetch
        try:
            import httpx
            r = httpx.get(url, timeout=15, follow_redirects=True)
            # Strip HTML tags roughly
            import re
            text = re.sub(r'<[^>]+>', ' ', r.text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:5000]
        except Exception as e:
            return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# Social Publishing (Dev.to, WeChat)
# ═══════════════════════════════════════════════════════════════════════════

class PublishDevtoTool(Tool):
    name = "publish_devto"
    description = "Publish an article to Dev.to. Input: title|||body_markdown|||tags (comma-separated)."

    def run(self, input_text: str) -> str:
        parts = input_text.split("|||")
        if len(parts) < 2:
            return "Error: format is title|||body|||tags"
        title = parts[0].strip()
        body = parts[1].strip()
        tags = [t.strip() for t in parts[2].split(",")] if len(parts) > 2 else ["ai", "agents"]
        key = os.getenv("DEVTO_API_KEY", "")
        if not key:
            return "Error: DEVTO_API_KEY not set"
        try:
            import httpx
            r = httpx.post(
                "https://dev.to/api/articles",
                headers={"api-key": key, "Content-Type": "application/json"},
                json={"article": {"title": title, "body_markdown": body, "published": False, "tags": tags[:4]}},
                timeout=15,
            )
            data = r.json()
            return f"Draft created: {data.get('url', '?')} (id={data.get('id', '?')})"
        except Exception as e:
            return f"Error: {e}"


class SendWechatTool(Tool):
    name = "send_wechat"
    description = "Send a message via Enterprise WeChat to admin. Input: message text."

    def run(self, input_text: str) -> str:
        corp_id = os.getenv("WECHAT_CORP_ID", "")
        secret = os.getenv("WECHAT_APP_SECRET", "")
        agent_id = os.getenv("WECHAT_AGENT_ID", "")
        admin = os.getenv("WECHAT_ADMIN_USERS", "WangChunXiao")
        if not corp_id or not secret:
            return "Error: WeChat not configured"
        try:
            import httpx
            # Get access token
            r = httpx.get(f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={secret}", timeout=10)
            token = r.json().get("access_token", "")
            if not token:
                return f"Error: failed to get WeChat token"
            # Send message
            r2 = httpx.post(
                f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}",
                json={"touser": admin, "msgtype": "text", "agentid": int(agent_id or 1000002),
                      "text": {"content": input_text[:2000]}},
                timeout=10,
            )
            return f"WeChat sent to {admin}: {r2.json().get('errmsg', '?')}"
        except Exception as e:
            return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# GitHub API
# ═══════════════════════════════════════════════════════════════════════════

class GitHubSearchTool(Tool):
    name = "github_search"
    description = "Search GitHub repositories or code. Input: query string."

    def run(self, input_text: str) -> str:
        try:
            import httpx
            r = httpx.get(
                "https://api.github.com/search/repositories",
                params={"q": input_text, "per_page": 5, "sort": "stars"},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            items = r.json().get("items", [])
            if not items:
                return "No repositories found."
            result = []
            for repo in items:
                result.append(f"- {repo['full_name']} ({repo['stargazers_count']} stars): {repo.get('description','')[:80]}")
            return "\n".join(result)
        except Exception as e:
            return f"Error: {e}"


class GitHubReadRepoTool(Tool):
    name = "github_read"
    description = "Read a file from a GitHub repository. Input: owner/repo/path (e.g., chunxiaoxx/nautilus-core/README.md)."

    def run(self, input_text: str) -> str:
        parts = input_text.strip().split("/", 2)
        if len(parts) < 3:
            return "Error: format is owner/repo/path"
        owner, repo, path = parts[0], parts[1], parts[2]
        try:
            import httpx
            r = httpx.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers={"Accept": "application/vnd.github.v3.raw"},
                timeout=10,
            )
            if r.status_code == 200:
                return r.text[:5000]
            return f"Error: {r.status_code} {r.text[:200]}"
        except Exception as e:
            return f"Error: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# Blockchain (Base Chain read)
# ═══════════════════════════════════════════════════════════════════════════

class BlockchainBalanceTool(Tool):
    name = "blockchain_balance"
    description = "Check ETH/USDC balance on Base Chain. Input: wallet address (0x...)."

    def run(self, input_text: str) -> str:
        address = input_text.strip()
        try:
            import httpx
            rpc = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
            # ETH balance
            r = httpx.post(rpc, json={
                "jsonrpc": "2.0", "method": "eth_getBalance",
                "params": [address, "latest"], "id": 1,
            }, timeout=10)
            eth_wei = int(r.json().get("result", "0x0"), 16)
            eth = eth_wei / 1e18
            # USDC balance (contract: 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913)
            usdc_contract = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
            data = f"0x70a08231000000000000000000000000{address[2:]}"
            r2 = httpx.post(rpc, json={
                "jsonrpc": "2.0", "method": "eth_call",
                "params": [{"to": usdc_contract, "data": data}, "latest"], "id": 2,
            }, timeout=10)
            usdc_raw = int(r2.json().get("result", "0x0"), 16)
            usdc = usdc_raw / 1e6
            return f"Address: {address}\nETH: {eth:.6f}\nUSDC: {usdc:.2f}\nChain: Base (8453)"
        except Exception as e:
            return f"Error: {e}"


class SkillManageTool(Tool):
    """Manage learned skills at runtime (Hermes pattern)."""
    name = "skill_manage"
    description = (
        "Manage your learned skills. Actions:\n"
        "  list — show all skills with vitality and success rate\n"
        "  get|<name> — show skill details\n"
        "  add|<name>|<description>|<procedure> — add a new skill\n"
        "  improve|<name>|<new_procedure> — update an existing skill's procedure\n"
        "  delete|<name> — remove a skill\n"
        "  share|<name>|<target_agent> — copy skill to another agent's library"
    )

    def run(self, input_text: str) -> str:
        try:
            from services.soul_bridge import get_soul_skills
        except ImportError:
            return "Error: soul not initialized"

        skills = get_soul_skills()
        parts = input_text.strip().split("|")
        action = parts[0].strip().lower()

        if action == "list":
            all_skills = skills.list_all()
            if not all_skills:
                return "No skills learned yet."
            lines = []
            for s in all_skills[:20]:
                rate = f"{s.successes}/{s.uses}" if s.uses else "untested"
                lines.append(f"  {s.name} (v={s.vitality:.1f}, rate={rate}, type={s.task_type})")
            return f"{len(all_skills)} skills:\n" + "\n".join(lines)

        elif action == "get" and len(parts) >= 2:
            skill = skills.get(parts[1].strip())
            if not skill:
                return f"Skill '{parts[1]}' not found."
            rate = f"{skill.successes}/{skill.uses}" if skill.uses else "untested"
            return (
                f"Name: {skill.name}\nType: {skill.task_type}\n"
                f"Vitality: {skill.vitality:.2f}\nSuccess: {rate}\n"
                f"Description: {skill.description}\n"
                f"Procedure:\n{skill.procedure[:1000]}"
            )

        elif action == "add" and len(parts) >= 4:
            name, desc, proc = parts[1].strip(), parts[2].strip(), parts[3].strip()
            skill = skills.add(name=name, description=desc, procedure=proc)
            return f"Skill '{name}' added (vitality={skill.vitality:.1f})."

        elif action == "improve" and len(parts) >= 3:
            name, new_proc = parts[1].strip(), parts[2].strip()
            if skills.improve(name, new_proc):
                return f"Skill '{name}' improved."
            return f"Skill '{name}' not found."

        elif action == "delete" and len(parts) >= 2:
            if skills.delete(parts[1].strip()):
                return f"Skill '{parts[1]}' deleted."
            return f"Skill '{parts[1]}' not found."

        elif action == "share" and len(parts) >= 3:
            name, target = parts[1].strip(), parts[2].strip()
            skill = skills.get(name)
            if not skill:
                return f"Skill '{name}' not found."
            from dataclasses import asdict
            target_dir = Path(os.path.expanduser(f"~/.nautilus-agent/{target}/skills"))
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / f"{name.replace(' ', '_').lower()}.json"
            target_path.write_text(
                json.dumps(asdict(skill), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return f"Skill '{name}' shared to agent '{target}'."

        return f"Unknown action: {action}. Use: list, get|name, add|name|desc|proc, improve|name|proc, delete|name, share|name|target"


class SpawnSubagentTool(Tool):
    """Spawn a focused subagent to execute a task in parallel (Hermes RPC pattern).

    Writes a Python script to workspace, executes it, returns output.
    Zero context cost — the subagent runs in its own process.
    """
    name = "spawn_subagent"
    description = (
        "Spawn a focused Python subagent for parallel task execution. "
        "Input: a Python script (as string) to execute. "
        "The script runs in a subprocess with 60s timeout. "
        "Returns stdout+stderr. Use for: data analysis, file processing, "
        "web requests, calculations — anything that can run standalone."
    )

    # Forbidden patterns — prevent dangerous operations
    _BLOCKED = ["os.system", "subprocess", "shutil.rmtree", "eval(", "exec(",
                "__import__", "open('/etc", "rm -rf", "PRIVATE_KEY", "SECRET"]

    def run(self, input_text: str) -> str:
        import sys
        # Security: block dangerous patterns
        for pat in self._BLOCKED:
            if pat.lower() in input_text.lower():
                return f"BLOCKED: script contains forbidden pattern '{pat}'"

        script_path = None
        try:
            workspace = Path(tempfile.gettempdir()) / "nautilus_subagent"
            workspace.mkdir(parents=True, exist_ok=True)

            script_path = workspace / f"subagent_{os.getpid()}_{id(input_text)}.py"
            script_path.write_text(input_text, encoding="utf-8")

            # Use sys.executable for portability (works on Windows + Linux)
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=60,
                cwd=str(workspace),
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[STDERR]: {result.stderr[:500]}"
            if result.returncode != 0:
                output += f"\n[EXIT CODE]: {result.returncode}"

            return output[:3000] if output else "(no output)"
        except subprocess.TimeoutExpired:
            return "Error: subagent timed out after 60s"
        except Exception as e:
            return f"Error: {e}"
        finally:
            # Always clean up script file
            if script_path and script_path.exists():
                try:
                    script_path.unlink()
                except Exception:
                    pass


# ═══════════════════════════════════════════════════════════════════════════
# Registry
# ═══════════════════════════════════════════════════════════════════════════

_registry: Optional[ToolRegistry] = None


def get_tools() -> ToolRegistry:
    """Get the daemon tool registry with all available tools."""
    global _registry
    if _registry is not None:
        return _registry

    _registry = ToolRegistry()

    # nautilus-agent tools (hands)
    _registry.register(SearchTool())
    _registry.register(ReadFileTool())
    _registry.register(WriteFileTool())
    _registry.register(AppendFileTool())
    _registry.register(ReplaceInFileTool())
    _registry.register(ListDirTool())
    _registry.register(CodeTool())
    _registry.register(RunFileTool())

    # Platform-specific tools (eyes + body awareness)
    _registry.register(PlatformHealthTool())
    _registry.register(PlatformStatsTool())
    _registry.register(ReadLogTool())
    _registry.register(QueryDBTool())
    _registry.register(InspectSelfTool())
    _registry.register(ExplorePlatformTool())

    # MiniMax multimodal (creative hands)
    _registry.register(MiniMaxImageTool())
    _registry.register(MiniMaxTTSTool())
    _registry.register(SendTelegramPhotoTool())

    # Google AI (KAIROS eyes + brain)
    _registry.register(GeminiChatTool())
    _registry.register(GoogleSearchGroundingTool())
    _registry.register(GeminiEmbeddingTool())

    # A2A communication (agent-to-agent)
    _registry.register(SendA2ATool())

    # Upgraded file tools (chunked, grep, surgery)
    _registry.register(FileInfoTool())
    _registry.register(InsertAtLineTool())
    _registry.register(DeleteLinesTool())
    _registry.register(GrepTool())

    # Web crawling
    _registry.register(CrawlUrlTool())

    # Social publishing
    _registry.register(PublishDevtoTool())
    _registry.register(SendWechatTool())

    # GitHub
    _registry.register(GitHubSearchTool())
    _registry.register(GitHubReadRepoTool())

    # Blockchain
    _registry.register(BlockchainBalanceTool())

    # Skill management (Hermes pattern)
    _registry.register(SkillManageTool())

    # Subagent spawn (Hermes RPC pattern)
    _registry.register(SpawnSubagentTool())

    logger.info("Daemon tools: %d registered (%s)", _registry.count, ", ".join(_registry.names))
    return _registry
