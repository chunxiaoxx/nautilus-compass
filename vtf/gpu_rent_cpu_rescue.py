"""CPU 小机抢救租用(用户授权 ¥<1 帽)· 试探保留盘恢复参数 TheLatestCopyName。

流程:quote(价帽自守≤¥1) → create → 轮询拿 SSH → 探测 /root/LongMemEval-V2
→ 探测失败自动 release(防空烧),成功则保留由主流程拉源码。
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/c/Users/chunx/.workbuddy/ai-galaxy-compute/src")

from ai_galaxy_compute.client import AIGalaxyClient  # noqa: E402

CREDS = Path(
    os.environ.get(
        "AI_GALAXY_CREDENTIALS_FILE",
        str(Path.home() / ".config/ai-galaxy-compute/credentials.json"),
    )
)
client = AIGalaxyClient(json.loads(CREDS.read_text())["access_key"], json.loads(CREDS.read_text())["secret_key"])

# 652509 的保留盘 = 最新副本(IsLatestCopy=True, DiskReleaseTime=None)
KEEP_DISK_SOURCE = "18510625230_lyg0063_ebc626351222418980f80a1d231fe6db_u1_c2"
PRICE_CAP = 1.0

REQUEST = {
    "gpu_type": "CPU",
    "gpu_num": "0",
    "image_name": "ubuntu22.04_base",
    "unit": "hour",
    "pack_time": "4",
    "pay_type_first": "money",
    "autorenew_on": "false",
    "autorenew_unit": "hour",
    "add_disk_size": "0",
    "bandwidth": "10",
    "due_mode": "1",
    "spec_name": "ecs.c1.base",
    "TheLatestCopyName": KEEP_DISK_SOURCE,
}


def quote_total(quote: dict) -> float:
    sheet = (quote.get("PackPriceInfoSheet") or {}).get("InstanceSubPriceSheet") or []
    total = 0.0
    for item in sheet:
        for k in ("TotalPrice", "Price", "Amount"):
            v = item.get(k)
            if isinstance(v, (int, float)):
                total = max(total, total + v if k != "Amount" else total)
    # 兜底:直接找总价字段
    for k in ("TotalPrice", "Price", "total_price"):
        v = quote.get(k) or (quote.get("PackPriceInfoSheet") or {}).get(k)
        if isinstance(v, (int, float)):
            return float(v)
    return total


def all_instances():
    out = []
    for page in (1, 2, 3):
        lst = client.get_instance_list(page=page)
        out.extend(lst.get("list") or [])
        if not lst.get("has_more"):
            break
    return out


def main() -> int:
    existing_ids = {it.get("Id") for it in all_instances()}
    quote = client.quote_instance(REQUEST)
    total = quote_total(quote)
    print("QUOTE keys:", list(quote.keys())[:8], "parsed_total=", total)
    if total > PRICE_CAP:
        print(f"PRICE_CAP_BLOCK: quote total {total} > {PRICE_CAP}")
        return 2
    created = client.create_instance(REQUEST)
    print("CREATE:", json.dumps(created, ensure_ascii=False, default=str)[:400])
    time.sleep(20)
    fresh = [it for it in all_instances() if it.get("Id") not in existing_ids]
    if not fresh:
        print("NO_NEW_INSTANCE: create 后列表未见新实例,需人工核查")
        return 3
    inst = max(fresh, key=lambda it: it.get("Id") or 0)
    name = inst.get("Container_name")
    print(f"NEW: id={inst.get('Id')} name={name} host={inst.get('Host')} port={inst.get('SshPort')} status={inst.get('Status')}")
    # 探测循环:最多 ~4 分钟等 boot
    probe = ["ls /root/LongMemEval-V2/evaluation/harness.py /root/e2e/judge.env 2>&1"]
    ok = False
    for attempt in range(16):
        time.sleep(15)
        info = None
        for it in all_instances():
            if it.get("Id") == inst.get("Id"):
                info = it
                break
        if not info or info.get("Status") in (8, -2):
            print("INSTANCE_GONE_OR_STOPPED")
            break
        host, port, pw = info.get("Host"), info.get("SshPort"), info.get("Init_passwd")
        if not (host and port and pw):
            continue
        env = dict(os.environ, GPU_SSH_HOST=str(host), GPU_SSH_PORT=str(port), GPU_SSH_PW=str(pw))
        env["MSYS2_NO_PATHCONV"] = "1"
        env["MSYS2_ARG_CONV_EXCL"] = "*"
        import subprocess

        try:
            r = subprocess.run(
                [sys.executable, "vtf/gpu_ssh.py", probe[0]],
                env=env, capture_output=True, text=True, timeout=60,
            )
            out = (r.stdout or "") + (r.stderr or "")
            print(f"attempt {attempt}: {out.strip()[:200]}")
            if "harness.py" in out and "No such" not in out:
                ok = True
                break
        except Exception as exc:  # noqa: BLE001
            print(f"attempt {attempt} ssh err: {exc}")
    if ok:
        print("KEEP: 源码在,保留实例拉源码")
        (Path(__file__).parent / "_cpu_rescue_instance.json").write_text(
            json.dumps({"id": inst.get("Id"), "name": name, "host": host, "port": port}, ensure_ascii=False),
            encoding="utf-8",
        )
        return 0
    # 失败 → 退租防空烧
    try:
        rel = client.release_instance(name)
        print("RELEASED:", json.dumps(rel, ensure_ascii=False, default=str)[:200])
    except Exception as exc:  # noqa: BLE001
        print(f"RELEASE_ERR: {exc}(需人工退)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
