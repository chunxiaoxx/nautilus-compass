FROM python:3.11-slim

WORKDIR /workspace/jobshop_orlib_v1_001

COPY . .

RUN pip install --no-cache-dir -r requirements.txt || true

# Regenerate the full artifact set (metrics.json, artifacts.json,
# eval.stdout.txt, eval.stderr.txt) so the workspace is verifiably reproducible.
CMD ["sh", "reproduce.sh"]
