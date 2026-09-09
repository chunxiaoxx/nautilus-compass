"""让 tests/ 可直接 import 仓根模块(daemon/recall/session_writer)。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
