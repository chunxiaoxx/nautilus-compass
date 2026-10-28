"""薛美雪题 doubao 难倒测试:原始题干+四附件生数据(不喂公式),三集合 JSON 判分。"""
import json, os, re, sys, time, zipfile
from pathlib import Path
import pandas as pd, requests

sys.path.insert(0, str(Path(__file__).parent))
from v_xuemeixue_audit import BASE, verify

MODEL = os.environ.get("STUMP_MODEL", "doubao-seed-2-0-pro-260215")
URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

def ark_key():
    for line in open(os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")):
        if line.startswith("ARK_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no key")

def sheet_csv(path, header_row=2, drop_cols=None):
    df = pd.read_excel(path, header=header_row)
    if drop_cols:
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    return df.to_csv(index=False)

def docx_text(path, limit=2600):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    t = re.sub(r"<[^>]+>", "", xml.replace("</w:p>", "\n"))
    return re.sub(r"\n{3,}", "\n\n", t)[:limit]

def build_prompt():
    stem = str(pd.read_excel(BASE / "题目数据表.xlsx").iloc[0]["题目"]).strip()
    a2 = sheet_csv(BASE / "附件2_Q4劳务费用支付明细表.xlsx")
    a3 = sheet_csv(BASE / "附件3_个税预扣预缴台账.xlsx")
    a4 = sheet_csv(BASE / "附件4_发票记录表.xlsx", drop_cols=["发票号"])
    a5 = docx_text(BASE / "附件5_集团连续劳务费用管理制度.docx")
    return (
        f"任务背景(出题人原文):\n{stem}\n\n"
        f"附件2_Q4劳务费用支付明细表(CSV):\n{a2}\n"
        f"附件3_个税预扣预缴台账(CSV):\n{a3}\n"
        f"附件4_发票记录表(CSV,发票号列略):\n{a4}\n"
        f"附件5_集团连续劳务费用管理制度(节选):\n{a5}\n\n"
        "请完成稽核中的三项可量化判定,只输出一个 JSON 对象,格式:\n"
        '{"个税更正":[{"人":"姓名","月":"10月/11月/12月","正确税额":数值}],'
        '"跨期序号":[附件2中的序号],"缺完税凭证发票序号":[附件4中的序号]}\n'
        "其中「个税更正」只列台账已预扣税额有误的(人,月),给出按制度与税法重算后的正确本月预扣税额(元,保留2位小数);"
        "「跨期序号」列出附件2中服务期间与付款期间不一致(含未付款)的记录序号;"
        "「缺完税凭证发票序号」列出附件4中缺完税凭证的发票记录序号。不要输出任何其他文字。"
    )

def parse_json(text):
    m = re.search(r"\{[\s\S]*\}", text)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None

if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    key = ark_key(); prompt = build_prompt()
    print(f"prompt {len(prompt)} chars · k={k} · model={MODEL}")
    results = []
    for i in range(k):
        t0 = time.time()
        try:
            r = requests.post(URL, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.6, "max_tokens": 24000}, timeout=580)
            r.raise_for_status()
            out = r.json()["choices"][0]["message"]["content"]
            cand = parse_json(out)
            if cand is None:
                results.append({"run": i, "ok": False, "err": "JSON解析失败", "head": out[:120]})
            else:
                ok, findings = verify(cand)
                results.append({"run": i, "ok": bool(ok), "findings": [str(f)[:90] for f in findings[:6]],
                                "耗时s": round(time.time() - t0, 1)})
        except Exception as e:
            results.append({"run": i, "ok": False, "err": str(e)[:110]})
        print(json.dumps(results[-1], ensure_ascii=False, default=str))
    print(f"\npass@{k} = {sum(1 for x in results if x.get('ok'))}/{k}")
    json.dump({"model": MODEL, "results": results},
              open(Path(__file__).parent / "doubao_xuemeixue_runs.json", "w", encoding="utf-8"), ensure_ascii=False)
