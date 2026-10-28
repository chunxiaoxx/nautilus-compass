import sys
import os

_repo = os.path.join(os.path.dirname(__file__), "environment/workspace/repo")
if _repo not in sys.path:
    sys.path.insert(0, _repo)
