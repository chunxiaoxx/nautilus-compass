#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jev CV-screening 校准测量 runner(K 先于模型承诺件,key 已公证 2026-10-01)。

40 件 CV × 六维度(fields.ts 原文出题,零改动),全请求/响应日志归档(K5)。
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "runtime" / "typesafe_jev_cvscreen"
API = "https://api.typesafe.ai/v1/systemone"

# 六维度问题(fields.ts instructions/criteria 原文,机械转录)
QUESTIONS = {
    "career_progression": {
        "type": "choice",
        "instructions": "How has this candidate's career moved over time? Judge the shape of the progression from the job titles, employers and dates, not the length of the CV. Ignore gaps that are explained by study, parental leave or military service, and ignore a single short stay after a long one. When the shape is genuinely ambiguous, choose unclear rather than guessing.",
        "criteria": {
            "steady_growth": "Responsibility clearly grows over time, either at one employer or with each move being a step up. Titles, scope or ownership increase.",
            "lateral_moves": "Moves between roles of similar level and scope, with no clear upward step and no pattern of short stays.",
            "job_hopping": "Three or more stays of roughly under eighteen months each, with no stated reason such as a fixed term contract, relocation or study.",
            "unclear": "The dates, roles or employers are too sparse or too inconsistent to see a shape at all.",
        },
    },
    "technical_depth": {
        "type": "score",
        "instructions": "Rate hands-on engineering depth using the experience and project bullets: what the candidate personally built, how complex it was, and how much they owned. Ignore skills lists, keywords, titles and company names. Score the depth the CV shows, not the years worked. When torn between two levels, pick the lower.",
        "criteria": [
            {"what": "No role or project where the candidate wrote code."},
            {"what": "Code appears only as coursework, a bootcamp or a tutorial exercise."},
            {"what": "Small scoped work inside someone else's design, such as bug fixes, small features, tests or scripts."},
            {"what": "Owns features end to end, from design through shipping and keeping them running."},
            {"what": "Owns a whole system or service and makes its architectural decisions."},
            {"what": "Deep specialist with real breadth, such as hard production problems solved across more than one area."},
        ],
    },
    "ownership_leadership": {
        "type": "score",
        "instructions": "How far does this candidate's responsibility extend beyond their own work? Judge from what they were accountable for, not from a title. When torn between two levels, pick the lower.",
        "criteria": [
            {"what": "No evidence of responsibility beyond their own tasks."},
            {"what": "Helps colleagues informally, reviews other people's work or explains things to them."},
            {"what": "Owns a small project or workstream, or formally mentors one person."},
            {"what": "Leads a team or a workstream that other people's work depends on, with responsibility for outcomes."},
            {"what": "Leads several teams, or sets direction for a whole function or discipline."},
        ],
    },
    "communication": {
        "type": "score",
        "instructions": "How much of this candidate's work is aimed at people outside their own team? Judge from what the CV says they produced or did, and ignore any self-description like 'excellent communicator'.",
        "criteria": [
            {"what": "No evidence of written or spoken work outside their own immediate team."},
            {"what": "Writes internal notes or documentation for their own team."},
            {"what": "Writes material other teams use, presents to a group, or trains others."},
            {"what": "Writes for people outside the company, or represents it in front of clients, regulators or the public."},
        ],
    },
    "motivation_fit": {
        "type": "choice",
        "instructions": "Does the CV point at this kind of work, come into it sideways, or point somewhere else?",
        "criteria": {
            "pointed": "The CV is aimed at this kind of work.",
            "sideways": "The CV comes into this kind of work sideways.",
            "elsewhere": "The CV points somewhere else.",
        },
    },
    "english_level": {
        "type": "choice",
        "instructions": "Judge the candidate's English level from the CV itself.",
        "criteria": {
            "none_or_minimal": "No working English shown.",
            "working": "Working English shown.",
            "strong": "Strong English shown.",
        },
    },
}


def key():
    for ln in open(os.path.expanduser("~/.claude/.cache/typesafe_api_key.env"), encoding="utf-8"):
        if "=" in ln and "TYPESAFE" in ln.upper():
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("key not found")


def ask_jev(state: str, k: str, qid: str, log):
    req = urllib.request.Request(
        API,
        data=json.dumps({"state": state, "model": "jev-latest",
                         "questions": QUESTIONS}).encode(),
        method="POST",
        headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=90))
    dt = time.time() - t0
    log.write(json.dumps({"qid": qid, "ts": time.strftime("%H:%M:%S"),
                          "latency_s": round(dt, 2), "req_questions": list(QUESTIONS),
                          "resp": r}, ensure_ascii=False) + "\n")
    log.flush()
    return r.get("answers") or {}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    texts = {r["path"].split("/")[-1].split("\\")[-1]: r
             for r in json.load(open(DIR / "cv_texts.json", encoding="utf-8"))}
    k = key()
    out_rows = []
    with open(DIR / "jev_run_log.jsonl", "w", encoding="utf-8") as log:
        for i, (fname, r) in enumerate(sorted(texts.items()), 1):
            try:
                ans = ask_jev((r.get("text") or "")[:30000], k, fname, log)
            except Exception as e:
                out_rows.append({"qid": fname, "error": str(e)[:120]})
                print(f"[{i}/40] {fname} ERR {type(e).__name__}", flush=True)
                continue
            out_rows.append({"qid": fname, "answers": ans})
            conf = {kk: (vv.get("confidence") if isinstance(vv, dict) else None)
                    for kk, vv in ans.items()}
            print(f"[{i}/40] {fname[:24]} career={ans.get('career_progression', {}).get('choice')} "
                  f"conf_c={conf.get('career_progression')}", flush=True)
    (DIR / "jev_answers.json").write_text(
        json.dumps(out_rows, ensure_ascii=False, indent=1), encoding="utf-8")
    n_ok = sum(1 for r in out_rows if "answers" in r)
    print(f"DONE {n_ok}/40 -> jev_answers.json")


if __name__ == "__main__":
    main()
