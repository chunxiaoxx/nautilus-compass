"""VerifyPack v0.2 CLI(spec: docs/verifypack/SPEC_v0.2.md)。

python -m tools.verifypack build|verify|receipt|check|keygen
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

from . import checks, keys, receipt, seal, spec

sys.stdout.reconfigure(encoding="utf-8")


def _read_pack(pack_dir: Path) -> dict:
    pack = json.loads((pack_dir / "pack.json").read_text(encoding="utf-8"))
    spec.validate_pack(pack)
    return pack


# ── build ────────────────────────────────────────────────────────────────

def cmd_build(a: argparse.Namespace) -> int:
    spec_doc = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    pack = spec_doc["pack"]
    spec.validate_pack(pack)
    out = Path(a.out)
    (out / "payload").mkdir(parents=True, exist_ok=True)
    (out / "repro").mkdir(parents=True, exist_ok=True)

    files = spec_doc.get("files", {})  # {"payload.json": "<src>", "report.md": "<src>"}
    import shutil
    for rel, src in files.items():
        src_p = Path(src)
        if not src_p.is_file():
            print(f"[build][FAIL] source missing: {src}")
            return 1
        dest = out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_p, dest)

    (out / "pack.json").write_text(
        json.dumps(pack, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    inputs = pack.get("inputs", [])
    for inp in inputs:  # 声明的外部路径在 seal 前验存在,缺文件即 build 失败
        root = Path(inp["path"])
        missing = [f for f in inp.get("files", []) if not (root / f).is_file()]
        if missing:
            print(f"[build][FAIL] declared input missing in {root}: {missing}")
            return 1

    seal.write_manifest(out, inputs)
    n = len(pack["claims"])
    print(f"[OK] pack sealed: {out} · claims {n} · files {len(files)} · inputs "
          f"{sum(len(i.get('files', [])) for i in inputs)}")
    return 0


# ── verify ───────────────────────────────────────────────────────────────

def cmd_verify(a: argparse.Namespace) -> int:
    pack_dir = Path(a.pack)
    pack = _read_pack(pack_dir)
    env_caps = set(a.env or [])

    ok, violations = seal.verify_seal(pack_dir)
    if not ok:
        results = [{"id": c["id"], "level": c["level"], "verdict": "seal_fail",
                    "recomputed": "; ".join(violations[:5]), "claimed": str(c["value"])[:80]}
                   for c in pack["claims"]]
        print(f"🔒 SEAL_FAIL({len(violations)}):")
        for v in violations:
            print(f"   {v}")
        return _emit_receipt(a, pack_dir, pack, results, seal_fail=True)

    results: list[dict] = []
    computed: dict = {}
    for claim in pack["claims"]:
        chk = claim.get("checks") or {}
        primary = chk.get("primary", chk if chk.get("kind") else None)
        fallback = chk.get("fallback")
        verdict, recomputed = None, None
        try:
            r = checks.run_check(pack, claim, primary, pack_dir, computed, env_caps)
            verdict, recomputed = ("agree" if r["ok"] else "disagree"), r["recomputed"]
        except checks.EnvRequired as e:
            if fallback:
                try:
                    r = checks.run_check(pack, claim, fallback, pack_dir, computed, env_caps)
                    verdict, recomputed = ("agree" if r["ok"] else "disagree"), \
                        f"degraded·fb:{r['recomputed']}"
                    verdict = "degraded" if r["ok"] else "disagree"
                except Exception as ex:  # noqa: BLE001 — 回执记录失败原因
                    verdict, recomputed = "disagree", f"fallback error: {ex}"
            else:
                verdict, recomputed = "degraded", f"env {e.cap!r} not declared, no fallback"
        except Exception as ex:  # noqa: BLE001 — 无法执行 ≠ disagree,但同样进回执
            verdict, recomputed = "disagree", f"check error: {ex}"
        computed[claim["id"]] = recomputed
        results.append({"id": claim["id"], "level": claim["level"], "verdict": verdict,
                        "recomputed": str(recomputed)[:300],
                        "claimed": str(claim["value"])[:120]})
        print(f"[{verdict:9}] {claim['id']} · {recomputed!s:.120}")

    n_agree = sum(1 for r in results if r["verdict"] == "agree")
    n_dis = sum(1 for r in results if r["verdict"] == "disagree")
    n_deg = sum(1 for r in results if r["verdict"] == "degraded")
    print(f"TOTAL: {n_agree}/{len(results)} agree"
          + (f" · {n_dis} disagree" if n_dis else "")
          + (f" · {n_deg} degraded" if n_deg else ""))
    return _emit_receipt(a, pack_dir, pack, results)


def _emit_receipt(a: argparse.Namespace, pack_dir: Path, pack: dict,
                  results: list[dict], seal_fail: bool = False) -> int:
    env = (f"{platform.system()} {platform.release()} · python {platform.python_version()}")
    rec = receipt.build_receipt(pack["pack"], pack_dir, a.verifier, results, env,
                                subject=pack.get("subject"), ttl_days=getattr(a, "ttl_days", None))
    if rec.get("valid_until"):
        print(f"[OK] ttl: valid_until {rec['valid_until']} (LE 式续期;到期=UNVERIFIABLE 直至续验)")
    out = Path(a.out) if a.out else pack_dir / "receipts" / "receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"[OK] receipt: {out}")
    if a.key:
        kp = keys.load_key(a.key)
        sig = receipt.sign_receipt(out, kp)
        print(f"[OK] signed: {sig} (key {kp.name})")
    fails = seal_fail or any(r["verdict"] in ("disagree", "seal_fail") for r in results)
    return 1 if fails else 0


# ── receipt(对已有回执补签) ────────────────────────────────────────────

def cmd_receipt(a: argparse.Namespace) -> int:
    rp = Path(a.receipt)
    if a.replaces:  # 续验链:前驱回执 sha256 入 chain.replaces
        import hashlib
        rh = hashlib.sha256(Path(a.replaces).read_bytes()).hexdigest()
        rec = json.loads(rp.read_text(encoding="utf-8"))
        rec["chain"] = {"replaces": rh}
        rec["receipt_version"] = "0.3"
        rp.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print(f"[OK] chain: replaces {rh[:16]}…")
    kp = keys.load_key(a.key)
    sig = receipt.sign_receipt(rp, kp)
    print(f"[OK] signed: {sig} (key {kp.name})")
    return 0


# ── check(结算方验签,不重算) ───────────────────────────────────────────

def cmd_check(a: argparse.Namespace) -> int:
    pub = a.pubkey
    if not pub:
        pub_env = None
        try:  # 与签名 key 同目录的 .pub 作为缺省公钥来源
            kp = keys.load_key(None)
            pub_env = kp.with_suffix(".pub")
        except FileNotFoundError:
            pass
        if pub_env and Path(pub_env).is_file():
            pub = Path(pub_env).read_text(encoding="utf-8").strip()
    if not pub:
        print("[check][FAIL] no pubkey: pass --pubkey (hex) or set VERIFYPACK_KEY beside .pub")
        return 2
    diag = receipt.check_receipt(Path(a.pack), Path(a.receipt), pub,
                                 Path(a.sig) if a.sig else None)
    print(json.dumps(diag, ensure_ascii=False, indent=1))
    return 0 if diag["ok"] else 1


# ── keygen ───────────────────────────────────────────────────────────────

def cmd_keygen(a: argparse.Namespace) -> int:
    kp, pp = keys.keygen(Path(a.out_dir), a.name)
    print(f"[OK] private key: {kp}")
    print(f"[OK] public  key: {pp}")
    print("     私钥请勿入仓;公钥可随回执分发。")
    return 0


# ── export(燃料层:pack 回执 → verdict 语料 JSONL) ─────────────────────

def cmd_export(a: argparse.Namespace) -> int:
    from . import exporter
    pub = a.pubkey
    if not pub:  # 与 check 同款:签名 key 同目录的 .pub 作缺省公钥
        try:
            kp = keys.load_key(None)
            pp = kp.with_suffix(".pub")
            if pp.is_file():
                pub = pp.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            pp = Path(".verifypack") / "compass.pub"  # keygen 缺省名;公钥可公开
            if pp.is_file():
                pub = pp.read_text(encoding="utf-8").strip()

    rows: list[dict] = []
    metas: list[dict] = []
    for p in a.packs:
        try:
            r, meta = exporter.export_pack(Path(p), a.trace, pub)
        except (OSError, ValueError, KeyError) as e:  # 无回执/包坏/JSON 坏
            print(f"[export][FAIL] {p}: {e}")
            return 1
        rows += r
        metas.append(meta)
        print(f"[OK] export {meta['pack']}: rows {meta['rows']} · sig "
              f"{'✓' if meta['signature_ok'] else '✗(未验签)'}"
              + (f" · orphans {meta['orphan_claims']}" if meta["orphan_claims"] else ""))

    manifest = exporter.write_corpus(rows, Path(a.out), a.trace, metas)
    print(f"[OK] corpus: {a.out} · rows {manifest['rows_total']} · "
          f"sha256 {manifest['sha256'][:16]}…")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="verifypack", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="数据方:打包+seal")
    b.add_argument("--spec", required=True, help="pack 描述 json(含 pack+files)")
    b.add_argument("--out", required=True)
    b.set_defaults(fn=cmd_build)

    v = sub.add_parser("verify", help="验证方:seal 校验+逐条复算+出回执")
    v.add_argument("pack")
    v.add_argument("--env", action="append", help="声明环境能力(可多次)")
    v.add_argument("--key", help="签名私钥路径(或 VERIFYPACK_KEY)")
    v.add_argument("--verifier", default="compass")
    v.add_argument("--out", help="receipt 输出路径")
    v.add_argument("--ttl-days", type=int, dest="ttl_days",
                   help="回执有效期天数(LE 式 90 天续期↔持续适航订阅;pack 带 subject 时建议 90)")
    v.set_defaults(fn=cmd_verify)

    r = sub.add_parser("receipt", help="对已有 receipt.json 签名")
    r.add_argument("--receipt", required=True)
    r.add_argument("--key")
    r.add_argument("--replaces", help="续验链:被本回执替代的旧 receipt 路径")
    r.set_defaults(fn=cmd_receipt)

    c = sub.add_parser("check", help="结算方:验签+摘要核对(不重算)")
    c.add_argument("pack")
    c.add_argument("--receipt", required=True)
    c.add_argument("--pubkey", help="验证方公钥 hex")
    c.add_argument("--sig", help="sig 路径(缺省 receipt 同名 .sig)")
    c.set_defaults(fn=cmd_check)

    k = sub.add_parser("keygen", help="生成 ed25519 密钥对")
    k.add_argument("--out-dir", default=".verifypack")
    k.add_argument("--name", default="compass")
    k.set_defaults(fn=cmd_keygen)

    x = sub.add_parser("export", help="燃料层:pack 回执 → verdict 语料 JSONL")
    x.add_argument("packs", nargs="+", help="pack 目录(可多个)")
    x.add_argument("--out", required=True, help="语料输出路径(.jsonl)")
    x.add_argument("--trace", help="批次 trace id(回函链)")
    x.add_argument("--pubkey", help="验签公钥 hex(缺省 .verifypack 同名 .pub)")
    x.set_defaults(fn=cmd_export)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
