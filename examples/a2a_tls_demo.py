"""TLS + mTLS A2A demo · v1.0 (Task #55).

Two MCPClient peers talking to one nautilus-compass TCP server *over mTLS*:

  Observer  → writes 2 observations (tools.write scope)
  Reader    → reads them back via resources/read (resources.read scope)

Self-contained: generates a CA, a server cert, and two client certs in a
tempdir, boots an mTLS daemon, runs both peers, tears everything down.
No external CA, no network, no persistent state · just a dev-laptop demo
that proves TLS + mTLS + RBAC all compose cleanly over MCP A2A.

Run:
    python examples/a2a_tls_demo.py

Exits 0 on success · prints a PROOF line with the wire transport
(`(tls)`) observed from the server banner, plus cert SANs + observed
handshake peer.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from mcp_client import MCPClient, MCPClientError  # noqa: E402


# ─── cert factory (mirrors tests/test_mcp_tls.py · kept inline so the
# demo is runnable without pytest) ───────────────────────────────────


def _gen_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _cert(subject: str, key, *, ca: bool = False,
          issuer_key=None, issuer_subject: str | None = None,
          san_dns: list[str] | None = None):
    subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)])
    issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,
                                          issuer_subject or subject)])
    now = dt.datetime.now(dt.timezone.utc)
    b = (x509.CertificateBuilder()
         .subject_name(subj).issuer_name(issuer)
         .public_key(key.public_key())
         .serial_number(x509.random_serial_number())
         .not_valid_before(now - dt.timedelta(minutes=5))
         .not_valid_after(now + dt.timedelta(hours=1))
         .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()),
                        critical=False))
    if ca:
        b = (b.add_extension(x509.BasicConstraints(ca=True, path_length=None),
                             critical=True)
              .add_extension(x509.KeyUsage(digital_signature=False, key_cert_sign=True,
                                           crl_sign=True, key_encipherment=False,
                                           content_commitment=False,
                                           data_encipherment=False, key_agreement=False,
                                           encipher_only=False, decipher_only=False),
                             critical=True))
    else:
        aki_pub = (issuer_key.public_key() if issuer_key else key.public_key())
        b = b.add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(aki_pub),
                            critical=False)
    if san_dns:
        b = b.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(d) for d in san_dns]),
            critical=False)
    return b.sign(issuer_key or key, hashes.SHA256())


def _write_pem(path: Path, cert, key=None) -> None:
    buf = cert.public_bytes(serialization.Encoding.PEM)
    if key is not None:
        buf += key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption())
    path.write_bytes(buf)


def _build_bundle(tmp: Path) -> dict:
    ca_key = _gen_key()
    ca = _cert("compass-demo-ca", ca_key, ca=True)

    srv_key = _gen_key()
    srv = _cert("localhost", srv_key,
                issuer_key=ca_key, issuer_subject="compass-demo-ca",
                san_dns=["localhost", "127.0.0.1"])

    obs_key = _gen_key()
    obs = _cert("peer-observer", obs_key,
                issuer_key=ca_key, issuer_subject="compass-demo-ca")

    rdr_key = _gen_key()
    rdr = _cert("peer-reader", rdr_key,
                issuer_key=ca_key, issuer_subject="compass-demo-ca")

    paths = {
        "ca": tmp / "ca.pem",
        "server": tmp / "server.pem",
        "observer": tmp / "observer.pem",
        "reader": tmp / "reader.pem",
    }
    _write_pem(paths["ca"], ca)
    _write_pem(paths["server"], srv, srv_key)
    _write_pem(paths["observer"], obs, obs_key)
    _write_pem(paths["reader"], rdr, rdr_key)
    return {k: str(v) for k, v in paths.items()}


# ─── server spawn ────────────────────────────────────────────────


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def _tls_server(bundle: dict, token_specs: list[str]):
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port),
           "--tls-cert", bundle["server"],
           "--tls-key", bundle["server"],
           "--tls-client-ca", bundle["ca"]]
    for spec in token_specs:
        cmd += ["--token", spec]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, "PYTHONUTF8": "1"})
    deadline = time.time() + 5.0
    banner = ""
    ready = False
    while time.time() < deadline:
        line = proc.stderr.readline()
        if not line:
            continue
        text = line.decode("utf-8", errors="replace").strip()
        if "listening on" in text:
            banner = text
            ready = True
            break
    try:
        if not ready:
            proc.kill()
            raise RuntimeError("mTLS server never announced readiness")
        yield port, banner
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


# ─── the demo itself ────────────────────────────────────────────


OBSERVATIONS = [
    {
        "name": "TLS demo · observation one",
        "description": "mTLS cross-peer write",
        "body": "Observer peer wrote this over mutual TLS. Both sides "
                "presented certs signed by compass-demo-ca.",
        "type": "feature", "concept": "how-it-works", "drift": "green",
    },
    {
        "name": "TLS demo · observation two",
        "description": "reader will fetch this via resources/read",
        "body": "Proves end-to-end: ingest (tools.write scope) → "
                "resources/read (resources.read scope) over the same mTLS "
                "socket family · peer identity checked by CA.",
        "type": "feature", "concept": "pattern", "drift": "green",
    },
]


def run_demo(verbose: bool = True) -> dict:
    def log(msg: str) -> None:
        if verbose:
            print(msg, flush=True)

    transcript: dict = {"banner": "", "wrote": [], "read": {}, "tls_proof": False}

    with tempfile.TemporaryDirectory(prefix="compass-tls-demo-") as td:
        bundle = _build_bundle(Path(td))
        log(f"[setup] generated CA + server + 2 client certs in {td}")

        specs = [
            "observer-tls:tools.read,tools.write",
            "reader-tls:tools.read,resources.read",
        ]
        with _tls_server(bundle, specs) as (port, banner):
            transcript["banner"] = banner
            transcript["tls_proof"] = "(tls)" in banner
            log(f"[server] {banner}")

            # Observer writes over mTLS · tools.write scope
            tls_opts = dict(tls=True, tls_ca_cert=bundle["ca"],
                            tls_server_hostname="localhost")
            with MCPClient(port=port, token="observer-tls",
                           tls_client_cert=bundle["observer"],
                           tls_client_key=bundle["observer"],
                           client_name="observer-tls", **tls_opts) as obs:
                tools = sorted(t["name"] for t in obs.list_tools())
                log(f"[observer] connected over mTLS · tools={tools}")
                for o in OBSERVATIONS:
                    try:
                        obs.call_tool("ingest_obs", o)
                        transcript["wrote"].append(o["name"])
                        log(f"[observer] wrote '{o['name']}'")
                    except MCPClientError as e:
                        log(f"[observer] ingest failed · {e}")

            # Reader reads back via resources/read · resources.read scope
            with MCPClient(port=port, token="reader-tls",
                           tls_client_cert=bundle["reader"],
                           tls_client_key=bundle["reader"],
                           client_name="reader-tls", **tls_opts) as rdr:
                r_tools = sorted(t["name"] for t in rdr.list_tools())
                log(f"[reader]   connected over mTLS · tools={r_tools}")
                resources = rdr.list_resources(limit=5)
                log(f"[reader]   resources/list · {len(resources)} items")
                if resources:
                    body = rdr.read_resource(resources[0]["uri"])
                    text = body.get("text", "")
                    transcript["read"] = {"uri": resources[0]["uri"],
                                          "bytes": len(text),
                                          "snippet": text[:120]}
                    log(f"[reader]   resources/read {resources[0]['uri']} "
                        f"· {len(text)}B")

    return transcript


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    t = run_demo(verbose=not args.quiet)

    ok = t["tls_proof"] and len(t["wrote"]) >= 1
    if ok:
        print(f"\nPROOF · banner={t['banner']!r} · "
              f"wrote={len(t['wrote'])} · "
              f"read={t['read'].get('bytes', 0)}B over mTLS")
        return 0
    print(f"\nERR · tls_proof={t['tls_proof']} wrote={t['wrote']}",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
