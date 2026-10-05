# -*- coding: utf-8 -*-
"""L3 正榜 Round 1 题源: SWE-bench Verified 分层抽样 n=30 (repo 比例配额, seed 落档).

判据正本: docs/metering/L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md (正榜题源节)
构造同构于 swe_verified_heldout30.parquet (pyarrow 显式类型, 防 str 退化坑).
"""
import json
import urllib.request

import pyarrow as pa
import pyarrow.parquet as pq

SEED = 20261005
N = 30
MIRROR = "https://hf-mirror.com"
REPO = "datasets/princeton-nlp/SWE-bench_Verified"
OUT_PARQUET = "board30.parquet"
OUT_META = "board30_meta.json"


def http_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "compass-l3/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def http_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "compass-l3/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def main() -> None:
    import sys

    sys.path.insert(0, "C:/Users/chunx/nautilus-v5/tools/uni_agent_bridge")
    from r81_env import env_line
    tree = http_json(f"{MIRROR}/api/{REPO}/tree/main?recursive=true")
    files = [f["path"] for f in tree if f["type"] == "file" and f["path"].endswith(".parquet")]
    print("parquet files:", files)
    assert files, "no parquet found in repo tree"

    path = sorted(files)[0]
    url = f"{MIRROR}/{REPO}/resolve/main/{path}"
    print("downloading:", url)
    blob = http_bytes(url)
    print("bytes:", len(blob))

    import io

    table = pq.read_table(io.BytesIO(blob))
    rows = table.to_pylist()
    print("total rows:", len(rows))
    cols = list(rows[0].keys())
    print("cols:", cols)

    # 分层: 按 repo 计数比例, 最大余数法配额
    from collections import Counter

    repo_counts = Counter(r["repo"] for r in rows)
    print("repo distribution:", dict(repo_counts))
    quotas = {}
    acc = 0
    for repo, cnt in sorted(repo_counts.items()):
        q = N * cnt // len(rows)
        quotas[repo] = q
        acc += q
    # 余数从大到小补齐到 N
    rems = sorted(repo_counts, key=lambda r: -(N * repo_counts[r] / len(rows) % 1))
    for repo in rems[: N - acc]:
        quotas[repo] += 1
    print("quotas:", quotas)

    # 固定 seed 组内打乱后取样; instance_id 全局唯一保证
    import random

    rng = random.Random(SEED)
    picked = []
    for repo, q in quotas.items():
        pool = [r for r in rows if r["repo"] == repo]
        rng.shuffle(pool)
        picked.extend(pool[:q])
    inst_ids = [r["instance_id"] for r in picked]
    assert len(picked) == N, f"picked {len(picked)} != {N}"
    assert len(set(inst_ids)) == N, "duplicate instance ids"

    # 构造同构 schema (pyarrow 显式类型)
    meta_type = pa.struct(
        [
            ("instance_id", pa.string()),
            ("repo", pa.string()),
            ("base_commit", pa.string()),
            ("FAIL_TO_PASS", pa.string()),
            ("PASS_TO_PASS", pa.string()),
        ]
    )
    prompt_type = pa.list_(
        pa.field("item", pa.struct([("role", pa.string()), ("content", pa.string())]))
    )
    msg_type = pa.struct([("role", pa.string()), ("content", pa.string())])

    records = []
    for r in picked:
        inst = r["instance_id"]
        image = "swebench/sweb.eval.x86_64." + inst.replace("__", "-").replace("/", "-")
        records.append(
            {
                "data_source": "princeton-nlp/SWE-bench_Verified",
                # 🔴 ENV 行必须烧进 prompt(A 臂 runner 靠题面 ENV 行预置 worktree;
                # 首版漏烧→A 臂裸跑 4 题作废返工,与 B 臂 tasks.json task_text 字节同源)
                "prompt": [
                    {
                        "role": "user",
                        "content": env_line(r["repo"], r["base_commit"])
                        + "\n\n"
                        + r["problem_statement"],
                    }
                ],
                "extra_info": {
                    "tools_kwargs": {
                        "task": {
                            "name": "swe_bench",
                            "sandbox": {"image": image},
                            "metadata": {
                                "instance_id": inst,
                                "repo": r["repo"],
                                "base_commit": r["base_commit"],
                                "FAIL_TO_PASS": r["FAIL_TO_PASS"],
                                "PASS_TO_PASS": r["PASS_TO_PASS"],
                            },
                        }
                    }
                },
            }
        )

    schema = pa.schema(
        [
            pa.field("data_source", pa.large_string()),
            pa.field("prompt", prompt_type),
            pa.field(
                "extra_info",
                pa.struct(
                    [
                        (
                            "tools_kwargs",
                            pa.struct(
                                [
                                    (
                                        "task",
                                        pa.struct(
                                            [
                                                ("name", pa.string()),
                                                ("sandbox", pa.struct([("image", pa.string())])),
                                                ("metadata", meta_type),
                                            ]
                                        ),
                                    )
                                ]
                            ),
                        )
                    ]
                ),
            ),
        ]
    )
    table_out = pa.Table.from_pylist(records, schema=schema)
    pq.write_table(table_out, OUT_PARQUET)

    # 回读验证: prompt 必须 isinstance list (smoke 踩过的坑)
    back = pq.read_table(OUT_PARQUET).to_pylist()
    assert len(back) == N
    assert isinstance(back[0]["prompt"], list) and isinstance(back[0]["prompt"][0], dict), (
        "prompt degenerated to str!"
    )
    empty_ps = sum(1 for r in back if not r["prompt"][0]["content"].strip())
    assert empty_ps == 0, f"{empty_ps} empty problem statements"
    # 🔴 回读验证: ENV 行必须在 prompt 头(首版漏烧→A 臂裸跑 4 题作废返工)
    assert all(
        r["prompt"][0]["content"].startswith("ENV (repo=") for r in back
    ), "ENV line missing in prompt!"

    # tasks.json 单源双出(B 臂输入;与 parquet prompt 字节同源, 双臂题面不漂移)
    tasks = []
    for i, r in enumerate(back):
        md = r["extra_info"]["tools_kwargs"]["task"]["metadata"]
        tasks.append(
            {
                "idx": i,
                "instance_id": md["instance_id"],
                "repo": md["repo"],
                "base_commit": md["base_commit"],
                "task_text": r["prompt"][0]["content"],
            }
        )
    with open("tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=1)
    print("tasks.json rows:", len(tasks))

    meta = {
        "note": "L3 正榜 Round 1 题源: Verified 分层抽样 n=30 (repo 比例配额, 最大余数法)",
        "seed": SEED,
        "source": f"princeton-nlp/SWE-bench_Verified {path}",
        "source_bytes": len(blob),
        "n": N,
        "quotas": quotas,
        "repo_counts_full": dict(repo_counts),
        "instance_ids": inst_ids,
        "sha_note": "判据正本 L3_HARNESS_BOARD_ROUND1_PREREG_20261005.md 正榜题源节",
    }
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("WROTE", OUT_PARQUET, OUT_META)
    print("sample ids:", inst_ids[:5], "...")


if __name__ == "__main__":
    main()
