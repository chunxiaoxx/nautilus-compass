"""v2 难倒测试:原始题干 + 生数据(乱表头/含干扰列/无公式提示)——对齐买方"不喂熟"口径。"""
import json, os, re, sys, time
from pathlib import Path
import pandas as pd, requests

sys.path.insert(0, str(Path(__file__).parent))
from v_zhanghuan_tax import verify

MODEL = os.environ.get("STUMP_MODEL", "doubao-seed-2-0-pro-260215")
BASE = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
XLSX = r"C:/Users/chunx/AppData/Local/Temp/claude/C--Users-chunx-Projects-nautilus-core/efea1144-0b71-4702-8732-646859f091b0/scratchpad/batch1/titi/大模型训练师-题目/客服/客服部_x/客服部/张欢/附件1-某外包客户工资2026年6月制作(1).xlsx"
TITI = r"C:/Users/chunx/AppData/Local/Temp/claude/C--Users-chunx-Projects-nautilus-core/efea1144-0b71-4702-8732-646859f091b0/scratchpad/batch1/titi/大模型训练师-题目/客服/客服部_x/客服部/张欢/AI训练师-张欢.xlsx"

def ark_key():
    for line in open(os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")):
        if line.startswith("ARK_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no key")

def build_prompt_raw():
    stem = str(pd.read_excel(TITI, sheet_name="Sheet1").iloc[0].get("题目", "")).strip()
    raw = pd.read_excel(XLSX, sheet_name="工资", header=None)
    hdr1, hdr2 = raw.iloc[1].tolist(), raw.iloc[2].tolist()
    # 保留输入列(0-35 与 37-49:月度明细+上期已缴),剔除答案列 36(本期累计个税)/50(个税金额)/51(调整)/52(实发)
    keep = [c for c in range(0, 50) if c != 36]
    def label(c):
        a, b = str(hdr1[c]).strip(), str(hdr2[c]).strip()
        parts = [x for x in (a, b) if x and x != "nan"]
        return "/".join(parts) if parts else f"列{c}"
    lines = [",".join(label(c) for c in keep)]
    body = raw.iloc[3:]
    body = body[body[1].notna()]
    for _, r in body.iterrows():
        cells = []
        PII = {4, 5, 9, 10}  # 身份证/开户行/手机/银行卡:与计算无关,遮蔽(附件本身未脱敏,已记整改单)
        for c in keep:
            v = r[c]
            if c in PII:
                cells.append("***")
            else:
                cells.append("" if pd.isna(v) else (f"{v:.2f}" if isinstance(v, float) else str(v)))
        lines.append(",".join(cells))
    data = "\n".join(lines)
    return (
        f"任务背景(出题人原文):\n{stem}\n\n"
        f"下面是甲方提供的 2026 年 6 月工资明细表原始数据(CSV,首行为表头,空单元格为空值):\n{data}\n\n"
        '请完成该任务中的个税核算:计算每名员工本期应预扣预缴的个人所得税金额(元,保留2位小数)。'
        '只输出一个 JSON 对象,格式 {"姓名": 本期个税金额, ...},包含全部员工,不要输出任何其他文字。'
    )

def call(prompt, key):
    r = requests.post(BASE, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.6, "max_tokens": 24000}, timeout=580)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def parse_json(text):
    m = re.search(r"\{[\s\S]*\}", text)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception: return None

if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    key = ark_key(); prompt = build_prompt_raw()
    print(f"v2 prompt {len(prompt)} chars · k={k} · model={MODEL}")
    results = []
    for i in range(k):
        t0 = time.time()
        try:
            out = call(prompt, key)
            cand = parse_json(out)
            if cand is None:
                results.append({"run": i, "ok": False, "err": "JSON解析失败", "raw_head": out[:120]}); print(json.dumps(results[-1], ensure_ascii=False)); continue
            ok, findings, cov = verify(XLSX, {str(x).strip(): v for x, v in cand.items()})
            wrong = [f for f in findings if f[1] != "缺失"]
            results.append({"run": i, "ok": bool(ok), "覆盖率": round(cov, 3), "错误人数": len(wrong),
                            "缺失人数": len(findings) - len(wrong), "样例错误": wrong[:3], "耗时s": round(time.time()-t0, 1)})
        except Exception as e:
            results.append({"run": i, "ok": False, "err": str(e)[:110]})
        print(json.dumps(results[-1], ensure_ascii=False, default=str))
    print(f"\nv2 pass@{k} = {sum(1 for r in results if r.get('ok'))}/{k}")
    json.dump({"model": MODEL, "mode": "raw_v2", "results": results},
              open(Path(__file__).parent / "doubao_zhanghuan_v2_runs.json", "w", encoding="utf-8"), ensure_ascii=False)
