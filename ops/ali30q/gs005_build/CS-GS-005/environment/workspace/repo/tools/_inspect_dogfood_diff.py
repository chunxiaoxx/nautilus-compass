"""Compare LLM-generated outcomes.py vs current master outcomes.py."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "phase3" / "backend"))

from engine.nautilus_engine import NautilusEngine

# Re-read SPEC from the dogfood script
dogfood_script = (ROOT / "tools" / "_stage1_self_dogfood.py").read_text(encoding="utf-8")
spec = dogfood_script.split('SPEC = """')[1].split('"""')[0]

eng = NautilusEngine(base_dir=str(ROOT / "phase3" / "backend"), dry_run=True)
raw = eng.generate(spec, max_tokens=4096, temperature=0.1)
blocks = eng.parse_file_blocks(raw)

if not blocks:
    print("NO BLOCKS")
    sys.exit(1)

llm_content = blocks[0]["content"]
master_content = (ROOT / "phase3" / "backend" / "engine" / "outcomes.py").read_text(encoding="utf-8")

print(f"master outcomes.py: {len(master_content.splitlines())} lines · {len(master_content)} chars")
print(f"LLM output       : {len(llm_content.splitlines())} lines · {len(llm_content)} chars")
print(f"line delta       : {len(llm_content.splitlines()) - len(master_content.splitlines())}")

print(f"\npreserved checks:")
for fn in ("def parse_spec_meta", "def compute_composite", "def classify",
           "def is_deadletter", "def compute_drift_ratio", "def aggregate_recent"):
    in_master = fn in master_content
    in_llm = fn in llm_content
    print(f"  {fn:30s} master={in_master} llm={in_llm}")

# Detect the compute_composite bug pattern
print(f"\nrisky pattern check:")
print(f"  'compute_composite(o)' (1-arg call) in LLM: {'compute_composite(o)' in llm_content}")
print(f"  'compute_composite(' (any call) in LLM   : {llm_content.count('compute_composite(')}")

# Module docstring preservation
master_docstring = master_content.split('"""')[1]
llm_docstring = llm_content.split('"""')[1]
print(f"\nmodule docstring preserved byte-for-byte: {master_docstring == llm_docstring}")
if master_docstring != llm_docstring:
    print(f"  master first 80: {master_docstring[:80]!r}")
    print(f"  llm    first 80: {llm_docstring[:80]!r}")
