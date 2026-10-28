#!/bin/bash
# Nautilus Agent SDK - One-line install
pip install httpx 2>/dev/null
curl -sO https://raw.githubusercontent.com/chunxiaoxx/nautilus-core/master/phase3/sdk/nautilus_client.py
echo "✅ Nautilus SDK ready. Usage: from nautilus_client import NautilusAgent"
