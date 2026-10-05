#!/usr/bin/env python3
"""r80 批 FUEL 判据预注册 v1 机判 v2(修正字段映射)。
- 判定源=库内 convert_submit 产物(verdict/failure_tag,label_origin=verifier,判据 §八绑定实现不在本地);
  判读侧职责=独立复核:轨迹实态↔判定一致性(判据 §三门+§六抽检放大到全批)。
- 复核口径:fail/unfinished ↔ 末条消息 role=tool(无 assistant 终结);pass/tag=None ↔ 末条 role=assistant。
- 同源性门:context.source 为产线标识(v5-selfline),前缀匹配 submitter(v5)=过(命名规约口径,披露)。
- 防泄漏门:G4=SKIP(panel 侧)=判定权在 panel,本判读披露不重复;行级 G1-G3 PASS 采纳。
- 工艺披露:导出行字符串字段双层转义,解析时一层降转义(行级 unescape 标记);材料文件字节未动。
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "r80_export_20261006.jsonl"


def parse_line(l: str) -> dict:
    try:
        return json.loads(l)
    except json.JSONDecodeError:
        r = json.loads(l.replace("\\\\", "\\"))
        r["_unescape"] = True
        return r


def main() -> int:
    rows = [parse_line(l.strip()) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    out, dis = [], []
    for r in rows:
        qid = r["qid"]
        ctx = r.get("context")
        if isinstance(ctx, str):
            try:
                ctx = json.loads(ctx)
            except json.JSONDecodeError:
                ctx = {}
        tr = r.get("trajectory") or []
        roles = [m.get("role") for m in tr]
        last_role = roles[-1] if roles else None
        lib_v, lib_tag = r.get("verdict"), r.get("failure_tag")
        # 四门
        gates_note = []
        src_ok = str(ctx.get("source", "")).startswith(str(r.get("submitter", "")))
        if not src_ok:
            dis.append(f"{qid}: 同源性门 source={ctx.get('source')} vs submitter={r.get('submitter')}")
        real_tool = "tool" in roles and len(tr) > 2  # 实态门:assistant/tool 轮替
        if not real_tool:
            dis.append(f"{qid}: 实态门 轨迹无 tool 轮次")
        g = r.get("gates") or {}
        # 复核:库判定 ↔ 轨迹末条
        if lib_v == "fail" and lib_tag == "unfinished":
            agree = (last_role == "tool")
        elif lib_v == "pass" and lib_tag is None:
            agree = (last_role == "assistant")
        else:
            agree = None  # 其他组合,单列
            gates_note.append(f"组合未定义:{lib_v}/{lib_tag}")
        verdict = lib_v if agree else ("U" if agree is False else f"U:{lib_v}")
        if agree is False:
            dis.append(f"{qid}: 复核不一致 lib={lib_v}/{lib_tag} vs last_role={last_role}")
        out.append({"qid": qid, "bounty_id": r.get("bounty_id"), "submitter": r.get("submitter"),
                    "verdict": verdict, "failure_tag": lib_tag, "lib_verdict": lib_v,
                    "last_role": last_role, "msg_n": len(tr),
                    "gates_G1G3": {k: g.get(k) for k in ("G1", "G2", "G3")},
                    "gates_G4": g.get("G4"), "final_patch_present": r.get("final_patch_present"),
                    "recheck_agree": agree, "unescape": bool(r.get("_unescape"))})

    from collections import Counter
    print("verdicts:", dict(Counter(o["verdict"] for o in out)))
    print("recheck disagreements:", len([d for d in dis if '不一致' in d]))
    for d in dis:
        print("  ", d)
    random.seed(20261006)
    for o in random.sample(out, 3):
        print(f"spot {o['qid']}: {o['verdict']}/{o['failure_tag']} msgs={o['msg_n']} last={o['last_role']} "
              f"gates={o['gates_G1G3']} G4={o['gates_G4']} fpp={o['final_patch_present']}")
    (HERE / "r80_verdicts.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written r80_verdicts.json;", "unescape rows:", sum(1 for o in out if o["unescape"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
