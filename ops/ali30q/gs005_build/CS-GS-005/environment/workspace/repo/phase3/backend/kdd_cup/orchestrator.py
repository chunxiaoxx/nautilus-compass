"""
KDD Cup 2026 Orchestrator — decomposes complex data questions into sub-tasks,
dispatches to specialist agents via A2A, aggregates results via RAID consensus.

Architecture:
    User Question
        │
        ▼
    Orchestrator (Gemini 3.1 Pro)
        │ A2A spawn_subtasks()
        ├─→ SQL Agent (MiniMax M2.7)
        ├─→ Document Agent (Gemini Pro)
        ├─→ Chart Agent (Gemini Vision)
        └─→ Calculation Agent (MiniMax)
                │
                ▼
        Synthesizer (RAID-3 consensus)
"""
import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger("kdd_cup")


# ── Data Source Detection ────────────────────────────────────────────────────

def detect_data_sources(data_package: Dict[str, Any]) -> List[Dict]:
    """Analyze a data package and identify all available data sources."""
    sources = []
    files = data_package.get("files", [])
    for f in files:
        name = f.get("name", "").lower()
        ftype = f.get("type", "")
        if name.endswith((".sqlite", ".db")) or ftype == "database":
            sources.append({"type": "sql", "file": f["name"], "agent": "sql_agent"})
        elif name.endswith((".csv", ".tsv")):
            sources.append({"type": "csv", "file": f["name"], "agent": "sql_agent"})
        elif name.endswith((".json", ".jsonl")):
            sources.append({"type": "json", "file": f["name"], "agent": "sql_agent"})
        elif name.endswith((".pdf",)):
            sources.append({"type": "document", "file": f["name"], "agent": "doc_agent"})
        elif name.endswith((".docx", ".doc", ".txt")):
            sources.append({"type": "document", "file": f["name"], "agent": "doc_agent"})
        elif name.endswith((".png", ".jpg", ".jpeg", ".svg")):
            sources.append({"type": "chart", "file": f["name"], "agent": "chart_agent"})
        elif name.endswith((".xlsx", ".xls")):
            sources.append({"type": "spreadsheet", "file": f["name"], "agent": "sql_agent"})
        else:
            sources.append({"type": "unknown", "file": f["name"], "agent": "calc_agent"})
    return sources


# ── Question Decomposition ───────────────────────────────────────────────────

async def decompose_question(question: str, sources: List[Dict]) -> List[Dict]:
    """Use LLM to decompose a complex question into sub-questions for each data source."""
    from agent_engine.llm.client import get_llm_client
    client = get_llm_client()

    source_desc = "\n".join(f"  - {s['file']} ({s['type']})" for s in sources)

    prompt = f"""You are a data analysis task decomposer. Given a complex question and available data sources,
break it into independent sub-questions that can be answered by specialist agents.

QUESTION: {question}

AVAILABLE DATA SOURCES:
{source_desc}

For each sub-question, specify:
1. The sub-question text
2. Which data source(s) to use
3. What type of output is expected (number, table, text, list)

Respond with a JSON array:
[{{"sub_question": "...", "sources": ["file1.csv"], "expected_output": "number", "agent": "sql_agent"}}]

Rules:
- Each sub-question should be independently answerable
- Prefer SQL agent for structured data (CSV, JSON, SQLite)
- Prefer doc agent for PDFs and text documents
- Prefer chart agent for images/charts
- If math/statistics needed, add a calc_agent sub-question
- The final sub-question should always be synthesis: combine all sub-results into the answer"""

    response = await asyncio.to_thread(
        client.chat,
        prompt,
        "You are a precise data analysis decomposer. Output ONLY valid JSON.",
        1024,
        0.1,
    )

    # Parse response
    import re
    text = response.strip()
    # Extract JSON array
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Fallback: single task
    return [{"sub_question": question, "sources": [s["file"] for s in sources], "expected_output": "text", "agent": "calc_agent"}]


# ── Sub-Task Execution ───────────────────────────────────────────────────────

async def execute_sql_subtask(sub: Dict, data_dir: str) -> str:
    """Execute a SQL/CSV/JSON data query sub-task."""
    from agent_engine.llm.client import get_llm_client
    client = get_llm_client()

    # Build context about the data
    source_files = sub.get("sources", [])
    context_parts = []
    for fname in source_files:
        fpath = os.path.join(data_dir, fname)
        if fname.endswith(".csv"):
            import csv
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    rows = [next(reader, []) for _ in range(5)]
                context_parts.append(f"CSV {fname}: columns={headers}, sample_rows={rows}")
            except Exception as e:
                context_parts.append(f"CSV {fname}: error reading — {e}")
        elif fname.endswith((".sqlite", ".db")):
            try:
                import sqlite3
                conn = sqlite3.connect(fpath)
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                for (tname,) in tables:
                    cols = conn.execute(f"PRAGMA table_info({tname})").fetchall()
                    col_names = [c[1] for c in cols]
                    row_count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
                    context_parts.append(f"Table {tname}: columns={col_names}, rows={row_count}")
                conn.close()
            except Exception as e:
                context_parts.append(f"SQLite {fname}: error — {e}")
        elif fname.endswith(".json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    context_parts.append(f"JSON {fname}: array of {len(data)} items, keys={list(data[0].keys()) if data else []}")
                elif isinstance(data, dict):
                    context_parts.append(f"JSON {fname}: object with keys={list(data.keys())[:20]}")
            except Exception as e:
                context_parts.append(f"JSON {fname}: error — {e}")

    data_context = "\n".join(context_parts)

    prompt = f"""Analyze the following data to answer this question:

QUESTION: {sub['sub_question']}

DATA SOURCES:
{data_context}

If the data is in SQLite, write and describe the SQL query you would run.
If CSV/JSON, describe the filtering/aggregation steps.
Provide the answer as precisely as possible. If a number, give the exact value.
If a table, list the columns and key rows."""

    result = await asyncio.to_thread(client.chat, prompt, "You are a data analyst. Be precise and concise.", 1024, 0.1)
    return result


async def execute_doc_subtask(sub: Dict, data_dir: str) -> str:
    """Execute a document analysis sub-task using Gemini multimodal."""
    from services.google_ai import GeminiClient
    client = GeminiClient()

    results = []
    for fname in sub.get("sources", []):
        fpath = os.path.join(data_dir, fname)
        try:
            with open(fpath, "rb") as f:
                data = f.read()
            mime = "application/pdf" if fname.endswith(".pdf") else "text/plain"
            result = await client.analyze_image(data, sub["sub_question"], mime_type=mime)
            results.append(f"[{fname}]: {result}")
        except Exception as e:
            results.append(f"[{fname}]: Error — {e}")

    return "\n\n".join(results)


async def execute_chart_subtask(sub: Dict, data_dir: str) -> str:
    """Execute a chart/image analysis sub-task using vision model."""
    from services.google_ai import GeminiClient
    client = GeminiClient()

    results = []
    for fname in sub.get("sources", []):
        fpath = os.path.join(data_dir, fname)
        try:
            with open(fpath, "rb") as f:
                data = f.read()
            mime = "image/png" if fname.endswith(".png") else "image/jpeg"
            prompt = f"Analyze this chart/image to answer: {sub['sub_question']}. Extract all visible data points, labels, and trends."
            result = await client.analyze_image(data, prompt, mime_type=mime)
            results.append(f"[{fname}]: {result}")
        except Exception as e:
            results.append(f"[{fname}]: Error — {e}")

    return "\n\n".join(results)


async def execute_calc_subtask(sub: Dict, data_dir: str) -> str:
    """Execute a calculation/synthesis sub-task."""
    from agent_engine.llm.client import get_llm_client
    client = get_llm_client()

    result = await asyncio.to_thread(
        client.chat,
        f"Perform the following analysis:\n\n{sub['sub_question']}\n\nBe precise with numbers.",
        "You are a computational analyst. Show your work step by step.",
        1024,
        0.1,
    )
    return result


AGENT_EXECUTORS = {
    "sql_agent": execute_sql_subtask,
    "doc_agent": execute_doc_subtask,
    "chart_agent": execute_chart_subtask,
    "calc_agent": execute_calc_subtask,
}


# ── RAID-3 Synthesis ─────────────────────────────────────────────────────────

async def synthesize_with_raid(question: str, sub_results: List[Dict], data_dir: str) -> str:
    """Use RAID-3 consensus to synthesize final answer from sub-results."""
    from agent_engine.llm.client import get_llm_client

    context = "\n\n".join(
        f"[{r['sub_question']}]\n{r['result']}" for r in sub_results
    )

    prompt = f"""Based on the following sub-analysis results, synthesize the final answer to the original question.

ORIGINAL QUESTION: {question}

SUB-ANALYSIS RESULTS:
{context}

Requirements:
1. Combine all sub-results into a coherent answer
2. If sub-results conflict, note the discrepancy and use the most evidence-backed answer
3. Be precise — include exact numbers, column names, and data points
4. Format the answer clearly"""

    # RAID-3: 3 independent synthesis attempts, then vote
    async def _one_synthesis(seed: int) -> str:
        client = get_llm_client()
        return await asyncio.to_thread(
            client.chat,
            prompt,
            f"You are synthesis agent #{seed}. Provide your independent analysis.",
            1024,
            0.3 + seed * 0.1,  # Vary temperature for diversity
        )

    # Run 3 in parallel
    results = await asyncio.gather(
        _one_synthesis(0),
        _one_synthesis(1),
        _one_synthesis(2),
    )

    # Judge: pick best
    client = get_llm_client()
    judge_prompt = f"""You are a judge. Three analysts independently answered a question. Pick the BEST answer.

QUESTION: {question}

ANSWER A:
{results[0][:800]}

ANSWER B:
{results[1][:800]}

ANSWER C:
{results[2][:800]}

Which answer is most accurate and complete? Respond with ONLY the letter (A, B, or C), then the final answer."""

    judgment = await asyncio.to_thread(client.chat, judge_prompt, "Pick the best answer. Be decisive.", 1024, 0.1)

    if "A" in judgment[:5]:
        return results[0]
    elif "B" in judgment[:5]:
        return results[1]
    else:
        return results[2]


# ── Main Pipeline ────────────────────────────────────────────────────────────

async def solve_question(question: str, data_dir: str, files: List[str]) -> str:
    """
    Full KDD Cup pipeline:
    1. Detect data sources
    2. Decompose question into sub-tasks
    3. Execute sub-tasks in parallel (A2A pattern)
    4. Synthesize with RAID-3 consensus
    """
    logger.info("KDD Cup: solving question: %s", question[:100])

    # 1. Detect sources
    data_package = {"files": [{"name": f, "type": ""} for f in files]}
    sources = detect_data_sources(data_package)
    logger.info("Detected %d data sources: %s", len(sources), [s["type"] for s in sources])

    # 2. Decompose
    subtasks = await decompose_question(question, sources)
    logger.info("Decomposed into %d sub-tasks", len(subtasks))

    # 3. Execute in parallel (A2A pattern)
    async def _exec_sub(sub: Dict) -> Dict:
        agent = sub.get("agent", "calc_agent")
        executor = AGENT_EXECUTORS.get(agent, execute_calc_subtask)
        try:
            result = await executor(sub, data_dir)
            return {"sub_question": sub["sub_question"], "agent": agent, "result": result, "status": "ok"}
        except Exception as e:
            return {"sub_question": sub["sub_question"], "agent": agent, "result": str(e), "status": "error"}

    sub_results = await asyncio.gather(*[_exec_sub(s) for s in subtasks])
    ok_count = sum(1 for r in sub_results if r["status"] == "ok")
    logger.info("Sub-tasks completed: %d/%d succeeded", ok_count, len(sub_results))

    # 4. RAID-3 synthesis
    answer = await synthesize_with_raid(question, sub_results, data_dir)
    logger.info("RAID-3 synthesis complete, answer length: %d", len(answer))

    return answer
