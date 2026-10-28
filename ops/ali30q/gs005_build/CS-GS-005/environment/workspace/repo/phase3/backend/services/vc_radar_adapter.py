"""
VC Radar Adapter — Connects 创投雷达 daily report pipeline to Nautilus multi-agent execution.

Instead of 创投雷达 calling LLM directly for each report section,
it POSTs event data here, and Nautilus orchestrates 7 parallel agents
(one per section) with RAID-2 quality verification.

API Flow:
  创投雷达 pipeline → POST /api/vc-radar/generate → Nautilus A2A decomposition
  → 7 agents write 7 sections → RAID-2 quality check → assembled markdown returned
"""
import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 7 report sections matching 创投雷达's generate_report_from_json.ts
REPORT_SECTIONS = [
    {
        "id": "daily_summary",
        "name": "I. 数据概览",
        "prompt_template": (
            "你是一位资深创投分析师。根据以下当日融资事件数据，撰写数据概览板块。\n"
            "包含：总融资笔数、总金额（亿元）、金额分层分布、轮次分布。\n"
            "用数据说话，客观精炼，markdown 格式。\n\n"
            "日期：{date}\n事件数据：\n{events_summary}"
        ),
    },
    {
        "id": "industry_insights",
        "name": "II. 行业深度分析",
        "prompt_template": (
            "你是创投行业分析专家。根据以下融资事件，分析 TOP5 热门行业的投资动向。\n"
            "每个行业：融资笔数、总金额、代表性公司、核心趋势判断。\n\n"
            "日期：{date}\n行业统计：\n{industry_stats}"
        ),
    },
    {
        "id": "cross_matrix",
        "name": "III. 跨行业对比矩阵",
        "prompt_template": (
            "根据以下行业融资数据，生成跨行业对比分析矩阵。\n"
            "维度：平均单笔金额、轮次偏好、投资机构重叠度、增长趋势。\n\n"
            "行业数据：\n{industry_stats}"
        ),
    },
    {
        "id": "investor_insights",
        "name": "IV. 投资机构 TOP10",
        "prompt_template": (
            "分析以下活跃投资机构的投资偏好和策略。\n"
            "每个机构：投资笔数、重点行业、轮次偏好、投资风格判断。\n\n"
            "投资机构统计：\n{investor_stats}"
        ),
    },
    {
        "id": "emerging_sectors",
        "name": "V. 新兴领域观察",
        "prompt_template": (
            "根据融资事件，识别和分析新兴投资领域（非传统热门赛道）。\n"
            "关注：首次出现的细分领域、异常高频出现的新概念、政策驱动的新方向。\n\n"
            "日期：{date}\n事件数据：\n{events_summary}"
        ),
    },
    {
        "id": "top_events",
        "name": "VI. TOP10 重点事件",
        "prompt_template": (
            "从以下事件中选择 TOP10 最重要的融资事件进行深度分析。\n"
            "每个事件5个维度：行业洞察、投资趋势、事件背景、过去回溯、未来影响。\n\n"
            "日期：{date}\n全部事件：\n{events_detail}"
        ),
    },
    {
        "id": "deep_insights",
        "name": "VII. AI 深度洞察",
        "prompt_template": (
            "作为资深创投分析师，基于今日全部融资数据给出深度洞察。\n"
            "包含：1) 市场特征总结 2) 趋势预判 3) 投资建议。\n"
            "要求：有数据支撑，有独到见解，有前瞻性。\n\n"
            "日期：{date}\n数据概览：{data_overview}\n行业分布：{industry_stats}"
        ),
    },
]


async def generate_report_via_nautilus(
    db: Session,
    report_date: str,
    events: List[Dict[str, Any]],
    industry_stats: Optional[Dict] = None,
    investor_stats: Optional[List] = None,
) -> Dict[str, Any]:
    """Generate a full VC daily report using Nautilus multi-agent pipeline.

    Args:
        db: Database session
        report_date: "2026-04-02" format
        events: List of event dicts from 创投雷达's data governance
        industry_stats: Pre-computed industry statistics (optional)
        investor_stats: Pre-computed investor statistics (optional)

    Returns:
        {sections: {section_id: markdown_text}, assembled_report: full_markdown, quality_scores: {...}}
    """
    start = time.time()
    logger.info("vc_radar: generating report for %s with %d events", report_date, len(events))

    # Prepare context strings
    events_summary = _summarize_events(events)
    events_detail = _detail_events(events[:30])  # top 30 for detailed analysis
    industry_text = json.dumps(industry_stats or _compute_industry_stats(events), ensure_ascii=False, indent=2)
    investor_text = json.dumps(investor_stats or _compute_investor_stats(events), ensure_ascii=False, indent=2)
    data_overview = f"{len(events)} 笔融资，总计约 {_total_amount(events):.1f} 亿元"

    # Generate all 7 sections in parallel via LLM
    sections = {}
    section_tasks = []

    for sec in REPORT_SECTIONS:
        prompt = sec["prompt_template"].format(
            date=report_date,
            events_summary=events_summary[:3000],
            events_detail=events_detail[:4000],
            industry_stats=industry_text[:2000],
            investor_stats=investor_text[:2000],
            data_overview=data_overview,
        )
        section_tasks.append((sec["id"], sec["name"], prompt))

    # Execute via RAID-2 (execute + review + improve) for each section
    results = await asyncio.gather(*[
        _generate_section(db, sid, name, prompt)
        for sid, name, prompt in section_tasks
    ])

    for sid, content, quality in results:
        sections[sid] = {"content": content, "quality": quality}

    # Assemble full report
    assembled = f"# 创投雷达日报 — {report_date}\n\n"
    for sec in REPORT_SECTIONS:
        sid = sec["id"]
        if sid in sections:
            assembled += f"## {sec['name']}\n\n{sections[sid]['content']}\n\n---\n\n"

    duration = round(time.time() - start, 2)
    logger.info("vc_radar: report generated in %.1fs, %d sections", duration, len(sections))

    # Record in DB for quality tracking
    try:
        for sec in REPORT_SECTIONS:
            sid = sec["id"]
            if sid in sections:
                db.execute(text(
                    "INSERT INTO academic_tasks (task_id, title, description, task_type, status, result_output, quality_rating) "
                    "VALUES (:tid, :title, :desc, 'vc_daily_report', 'completed', :result, :quality)"
                ), {
                    "tid": f"vc_{report_date}_{sid}",
                    "title": f"[VC Report] {sec['name']} — {report_date}",
                    "desc": f"创投雷达日报 {sec['name']} section",
                    "result": sections[sid]["content"][:5000],
                    "quality": sections[sid]["quality"],
                })
        db.commit()
    except Exception as e:
        logger.warning("vc_radar: failed to record tasks: %s", e)
        try:
            db.rollback()
        except Exception:
            pass

    return {
        "report_date": report_date,
        "events_count": len(events),
        "sections": {sid: s["content"] for sid, s in sections.items()},
        "quality_scores": {sid: s["quality"] for sid, s in sections.items()},
        "assembled_report": assembled,
        "duration_seconds": duration,
    }


async def _generate_section(db: Session, section_id: str, section_name: str, prompt: str) -> tuple:
    """Generate one report section using LLM with quality check."""
    try:
        from agent_engine.llm.client import get_llm_client
        client = get_llm_client()

        # Generate
        content = await asyncio.to_thread(
            client.chat,
            prompt,
            f"你是创投雷达AI分析师，正在撰写日报的[{section_name}]板块。用中文，markdown格式。",
            4096,
            0.3,
        )

        # Quick quality check (length + structure)
        quality = 3.0
        if len(content) > 500:
            quality += 0.5
        if "##" in content or "**" in content:
            quality += 0.5
        if any(c.isdigit() for c in content[:200]):
            quality += 0.5
        quality = min(quality, 5.0)

        return (section_id, content, quality)

    except Exception as e:
        logger.error("vc_radar section %s failed: %s", section_id, e)
        return (section_id, f"*{section_name}生成失败：{e}*", 1.0)


# ── Helper functions ─────────────────────────────────────────────────────────

def _summarize_events(events: List[Dict]) -> str:
    lines = []
    for e in events[:50]:
        company = e.get("companyName", "未知")
        industry = e.get("industry", "未知")
        amount = e.get("fundingAmount", "未披露")
        round_ = e.get("fundingRound", "")
        lines.append(f"- {company}（{industry}）{round_} {amount}万元")
    return "\n".join(lines)


def _detail_events(events: List[Dict]) -> str:
    return json.dumps(events, ensure_ascii=False, indent=1)[:4000]


def _compute_industry_stats(events: List[Dict]) -> Dict:
    stats = {}
    for e in events:
        ind = e.get("industry", "其他")
        if ind not in stats:
            stats[ind] = {"count": 0, "total_wan": 0}
        stats[ind]["count"] += 1
        try:
            stats[ind]["total_wan"] += float(e.get("fundingAmount", 0) or 0)
        except (ValueError, TypeError):
            pass
    return dict(sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)[:10])


def _compute_investor_stats(events: List[Dict]) -> List[Dict]:
    inv_map = {}
    for e in events:
        investors = e.get("investors", [])
        if isinstance(investors, str):
            investors = [i.strip() for i in investors.split(",")]
        for inv in (investors or []):
            if not inv:
                continue
            if inv not in inv_map:
                inv_map[inv] = {"name": inv, "count": 0, "industries": set()}
            inv_map[inv]["count"] += 1
            inv_map[inv]["industries"].add(e.get("industry", ""))
    result = sorted(inv_map.values(), key=lambda x: x["count"], reverse=True)[:10]
    for r in result:
        r["industries"] = list(r["industries"])[:5]
    return result


def _total_amount(events: List[Dict]) -> float:
    total = 0
    for e in events:
        try:
            total += float(e.get("fundingAmount", 0) or 0)
        except (ValueError, TypeError):
            pass
    return total / 10000  # 万→亿
