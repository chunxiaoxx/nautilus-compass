"""TLS + mTLS tests for MCP TCP transport · v1.0 (Task #53)."""
from __future__ import annotations

import contextlib
import datetime as dt
import os
import socket
import ssl
import subprocess
import sys
import time
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from mcp_client import MCPClient, MCPClientError  # noqa: E402
import mcp_server  # noqa: E402


# ─── cert factory ────────────────────────────────────────────────


def _gen_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _self_signed(subject: str, key, *, ca: bool = False,
                 issuer_key=None, issuer_subject: str | None = None,
                 san_dns: list[str] | None = None,
                 issuer_pub_key=None):
    """Build a leaf or CA cert. If issuer_key is None · self-signed."""
    subj = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)])
    issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,
                                          issuer_subject or subject)])
    now = dt.datetime.now(dt.timezone.utc)
    builder = (x509.CertificateBuilder()
               .subject_name(subj)
               .issuer_name(issuer)
               .public_key(key.public_key())
               .serial_number(x509.random_serial_number())
               .not_valid_before(now - dt.timedelta(minutes=5))
               .not_valid_after(now + dt.timedelta(hours=1)))
    # Python 3.13 SSL demands SKI on CA and AKI on leaves signed by a CA.
    builder = builder.add_extension(
        x509.SubjectKeyIdentifier.from_public_key(key.public_key()),
        critical=False)
    if ca:
        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True)
        builder = builder.add_extension(
            x509.KeyUsage(digital_signature=False, key_cert_sign=True,
                          crl_sign=True, key_encipherment=False,
                          content_commitment=False, data_encipherment=False,
                          key_agreement=False, encipher_only=False,
                          decipher_only=False),
            critical=True)
    else:
        # AKI points to whoever signed us.
        aki_pub = (issuer_pub_key if issuer_pub_key is not None
                   else (issuer_key.public_key() if issuer_key else key.public_key()))
        builder = builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(aki_pub),
            critical=False)
    if san_dns:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(d) for d in san_dns]),
            critical=False)
    signing_key = issuer_key or key
    return builder.sign(signing_key, hashes.SHA256())


def _write_pem(path: Path, cert, key=None) -> None:
    buf = cert.public_bytes(serialization.Encoding.PEM)
    if key is not None:
        buf += key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption())
    path.write_bytes(buf)


@pytest.fixture
def tls_bundle(tmp_path):
    """Return (server_cert, server_key, ca_cert, client_cert, client_key).

    CA signs both server and client certs so mTLS tests can use the same
    CA file for verification in both directions.
    """
    ca_key = _gen_key()
    ca_cert = _self_signed("compass-test-ca", ca_key, ca=True)

    server_key = _gen_key()
    server_cert = _self_signed("localhost", server_key,
                               issuer_key=ca_key, issuer_subject="compass-test-ca",
                               san_dns=["localhost", "127.0.0.1"])

    client_key = _gen_key()
    client_cert = _self_signed("peer-alpha", client_key,
                               issuer_key=ca_key, issuer_subject="compass-test-ca")

    server_pem = tmp_path / "server.pem"
    ca_pem = tmp_path / "ca.pem"
    client_pem = tmp_path / "client.pem"
    _write_pem(server_pem, server_cert, server_key)
    _write_pem(ca_pem, ca_cert)
    _write_pem(client_pem, client_cert, client_key)
    return {
        "server_cert": str(server_pem),
        "server_key": str(server_pem),  # same PEM holds both
        "ca": str(ca_pem),
        "client_cert": str(client_pem),
        "client_key": str(client_pem),
    }


# ─── _build_server_ssl_context ──────────────────────────────────


def test_build_server_ssl_context_happy(tls_bundle):
    ctx = mcp_server._build_server_ssl_context(
        tls_bundle["server_cert"], tls_bundle["server_key"])
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_NONE  # no mTLS


def test_build_server_ssl_context_mtls(tls_bundle):
    ctx = mcp_server._build_server_ssl_context(
        tls_bundle["server_cert"], tls_bundle["server_key"],
        client_ca=tls_bundle["ca"])
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_build_server_ssl_context_missing_cert_raises(tmp_path):
    with pytest.raises((OSError, ssl.SSLError)):
        mcp_server._build_server_ssl_context(
            str(tmp_path / "nope.pem"), str(tmp_path / "nope.pem"))


# ─── End-to-end TLS ─────────────────────────────────────────────


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextlib.contextmanager
def _tls_server(bundle, *, mtls: bool = False, token: str = "tls-tok"):
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port),
           "--token", f"{token}:*",
           "--tls-cert", bundle["server_cert"],
           "--tls-key", bundle["server_key"]]
    if mtls:
        cmd += ["--tls-client-ca", bundle["ca"]]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, "PYTHONUTF8": "1"})
    deadline = time.time() + 5.0
    ready = False
    while time.time() < deadline:
        line = proc.stderr.readline() if proc.stderr else b""
        if b"listening on" in line and b"(tls)" in line:
            ready = True
            break
    try:
        if not ready:
            proc.kill()
            raise RuntimeError(f"server never ready · cmd={cmd}")
        yield port, proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_tls_happy_path(tls_bundle):
    with _tls_server(tls_bundle) as (port, _):
        with MCPClient(port=port, token="tls-tok",
                       tls=True, tls_ca_cert=tls_bundle["ca"],
                       tls_server_hostname="localhost") as c:
            tools = c.list_tools()
            assert isinstance(tools, list) and len(tools) > 0


def test_tls_rejects_plaintext_client(tls_bundle):
    """Plaintext socket against a TLS server must fail · no tools executed."""
    with _tls_server(tls_bundle) as (port, _):
        # tls=False → plain socket · server will see garbage on TLS handshake.
        with pytest.raises((MCPClientError, OSError, ConnectionError)):
            with MCPClient(port=port, token="tls-tok",
                           call_timeout_s=2.0, max_retries=0) as c:
                c.ping()


def test_tls_rejects_bad_ca(tls_bundle, tmp_path):
    """Client with a different CA must fail cert verification."""
    other_ca_key = _gen_key()
    other_ca = _self_signed("other-ca", other_ca_key, ca=True)
    other_pem = tmp_path / "other_ca.pem"
    _write_pem(other_pem, other_ca)
    with _tls_server(tls_bundle) as (port, _):
        with pytest.raises((MCPClientError, ssl.SSLError, OSError)):
            with MCPClient(port=port, token="tls-tok",
                           tls=True, tls_ca_cert=str(other_pem),
                           tls_server_hostname="localhost",
                           call_timeout_s=2.0, max_retries=0) as c:
                c.ping()


def test_tls_insecure_verify_false_skips_check(tls_bundle):
    """tls_verify=False lets the client connect even without matching CA."""
    with _tls_server(tls_bundle) as (port, _):
        with MCPClient(port=port, token="tls-tok",
                       tls=True, tls_verify=False) as c:
            assert c.ping() >= 0


def test_mtls_happy_path(tls_bundle):
    with _tls_server(tls_bundle, mtls=True) as (port, _):
        with MCPClient(port=port, token="tls-tok",
                       tls=True, tls_ca_cert=tls_bundle["ca"],
                       tls_client_cert=tls_bundle["client_cert"],
                       tls_client_key=tls_bundle["client_key"],
                       tls_server_hostname="localhost") as c:
            assert c.ping() >= 0


def test_mtls_rejects_client_without_cert(tls_bundle):
    """mTLS server must reject a client that doesn't present a cert."""
    with _tls_server(tls_bundle, mtls=True) as (port, _):
        with pytest.raises((MCPClientError, ssl.SSLError, OSError)):
            with MCPClient(port=port, token="tls-tok",
                           tls=True, tls_ca_cert=tls_bundle["ca"],
                           tls_server_hostname="localhost",
                           call_timeout_s=2.0, max_retries=0) as c:
                c.ping()


# ─── CLI arg validation ────────────────────────────────────────


def test_cli_rejects_cert_without_key(tmp_path):
    """Running mcp_server.py with --tls-cert but no --tls-key must exit 2."""
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port),
           "--tls-cert", str(tmp_path / "doesnt-matter.pem")]
    r = subprocess.run(cmd, capture_output=True, timeout=5,
                       env={**os.environ, "PYTHONUTF8": "1"})
    assert r.returncode == 2
    assert b"tls-cert and --tls-key" in r.stderr
