"""张欢题 doubao 难倒测试:题干+输入数据 → doubao 算个税 → 验证器判分。"""
import json, os, re, sys, time
MODEL = os.environ.get("STUMP_MODEL", "doubao-seed-2-0-pro-260215")
from pathlib import Path
import pandas as pd, requests

sys.path.insert(0, str(Path(__file__).parent))
from v_zhanghuan_tax import load_expert, verify

XLSX = r"C:/Users/chunx/AppData/Local/Temp/claude/C--Users-chunx-Projects-nautilus-core/efea1144-0b71-4702-8732-646859f091b0/scratchpad/batch1/titi/大模型训练师-题目/客服/客服部_x/客服部/张欢/附件1-某外包客户工资2026年6月制作(1).xlsx"

def ark_key():
    for line in open(os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")):
        if line.startswith("ARK_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no ARK key")

def build_prompt():
    df = load_expert(XLSX)
    lines = ["姓名,本月应税工资,上期累计应税工资,累计专项附加扣除,累计免征额,上期累计已缴个税"]
    for _, r in df.iterrows():
        lines.append(f'{r["姓名"]},{r["应税工资"]:.2f},{r["上期累计应税"]:.2f},{r["专项附加合计"]:.2f},{r["累计免征额"]:.2f},{r["上期已缴"]:.2f}')
    data = "\n".join(lines)
    return (
        "你是人力资源外包公司的薪酬客服专员。任务:根据下表员工数据,按照中国居民个人工资薪金所得的"
        "累计预扣预缴方法(2026年现行税率表),计算每名员工本期应预扣预缴的个人所得税金额(元,保留2位小数)。\n"
        "计算口径:累计应纳税所得额 = 上期累计应税工资 + 本月应税工资 - 累计免征额 - 累计专项附加扣除;"
        "按累计预扣率表计算累计应纳税额,减去上期累计已缴个税,得本期应预扣税额(不小于0)。\n"
        f"员工数据(CSV):\n{data}\n\n"
        '只输出一个 JSON 对象,格式 {"姓名": 本期个税金额, ...},包含全部员工,不要输出任何其他文字。'
    )

def call_doubao(prompt, key):
    r = requests.post(
        "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": [{"role": "user", "content": prompt}], "temperature": 0.6, "max_tokens": 24000},
        timeout=280)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def parse_json(text):
    m = re.search(r"\{[\s\S]*\}", text)
    if not m: return None
    try: return json.loads(m.group(0))
    except Exception:
        try: return json.loads(m.group(0).replace("'", '"'))
        except Exception: return None

if __name__ == "__main__":
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    key = ark_key(); prompt = build_prompt()
    print(f"prompt {len(prompt)} chars · k={k}")
    results = []
    for i in range(k):
        t0 = time.time()
        try:
            out = call_doubao(prompt, key)
            cand = parse_json(out)
            if cand is None:
                results.append({"run": i, "ok": False, "err": "JSON解析失败", "raw_head": out[:150]})
                continue
            ok, findings, cov = verify(XLSX, {str(k2).strip(): v for k2, v in cand.items()})
            wrong = [f for f in findings if f[1] != "缺失"]
            miss = [f for f in findings if f[1] == "缺失"]
            results.append({"run": i, "ok": bool(ok), "覆盖率": round(cov, 3),
                            "错误人数": len(wrong), "缺失人数": len(miss),
                            "样例错误": wrong[:3], "耗时s": round(time.time() - t0, 1)})
        except Exception as e:
            results.append({"run": i, "ok": False, "err": str(e)[:120]})
        print(json.dumps(results[-1], ensure_ascii=False, default=str))
    passes = sum(1 for r in results if r.get("ok"))
    print(f"\npass@{k} = {passes}/{k}")
    json.dump(results, open(Path(__file__).parent / "doubao_zhanghuan_runs.json", "a", encoding="utf-8"), ensure_ascii=False)
